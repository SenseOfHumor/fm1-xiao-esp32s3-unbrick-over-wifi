"""Keep both independent reads and require them again for restoration planning."""
import hashlib
import json
import os
from pathlib import Path

FLASH_SIZE = 1024*1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_pair(first, second):
    if len(first)!=FLASH_SIZE or len(second)!=FLASH_SIZE:
        raise ValueError('both full-flash backups must be exactly 1 MiB')
    if first!=second:
        raise ValueError('independent flash reads differ; no restoration permitted')
    return digest(first)

def preserve_pair(outdir, reads):
    if len(reads)!=2: raise ValueError('expected two independent reads')
    sha=validate_pair(*reads)
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    paths=[outdir/f'full-flash-before-{i}.bin' for i in (1,2)]
    if any(p.exists() for p in paths):
        raise FileExistsError('original backups already exist; choose a new backup directory')
    for path,data in zip(paths,reads):
        with path.open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        if path.read_bytes()!=data: raise ValueError('backup file readback failed')
    return sha

def validate_reference(path, allow_mock=False):
    path=Path(path)
    first=(path.parent/'full-flash-before-1.bin').read_bytes()
    second=(path.parent/'full-flash-before-2.bin').read_bytes()
    sha=validate_pair(first,second)
    if path.read_bytes()!=first: raise ValueError('reference differs from verified backups')
    manifest=json.loads((path.parent/'analysis.json').read_text())
    if manifest.get('mock',False) and not allow_mock:
        raise ValueError('a simulated backup cannot authorize a real recovery plan')
    if manifest['sha256']!=sha: raise ValueError('backup manifest hash mismatch')
    return sha

def install_dump_capture(ftr):
    original=ftr.double_read
    analyse=ftr.dump_and_analyse
    def dump(t,outdir,labelled,v15):
        outdir=Path(outdir)
        if any((outdir/f'full-flash-before-{i}.bin').exists() for i in (1,2)):
            raise FileExistsError('use a new directory to preserve original flash backups')
        reads=[]
        class Reader:
            def __getattr__(self,name): return getattr(t,name)
            def read_flash(self,*args,**kwargs):
                data=t.read_flash(*args,**kwargs);reads.append(data);return data
        def record(_):
            result=original(Reader())
            preserve_pair(outdir,reads)
            return result
        ftr.double_read=record
        try: path,data,report=analyse(t,outdir,labelled,v15)
        finally: ftr.double_read=original
        manifest={'sha256':validate_pair(*reads),'size':len(data),'independent_reads':2,
                  'identity':ftr.parse_info(t.info()),'analysis':report.text,
                  'regions':{'head':'0x00000..0x03fff (protected)',
                             'firmware':'0x04000..0x92fff',
                             'device_data':'0x93000..0xfffff (protected)'},
                  'state':'BACKUP_READY','mock':t.mock}
        (outdir/'analysis.json').write_text(json.dumps(manifest,indent=2)+'\n')
        ftr.log.info('STATE BACKUP_READY: both independent reads preserved')
        return path,data,report
    ftr.dump_and_analyse=dump
