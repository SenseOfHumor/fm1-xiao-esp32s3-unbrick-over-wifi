#!/bin/bash
# Separate output/config per mode; never flash or change a computer's network.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:$PATH"
fm1_idf_root="${IDF_PATH:-../esp-idf-v5.4.1}"
if [[ -z "${IDF_PYTHON_ENV_PATH:-}" && -d "$HOME/.espressif/python_env/idf5.4_py3.12_env" ]]; then
  export IDF_PYTHON_ENV_PATH="$HOME/.espressif/python_env/idf5.4_py3.12_env"
fi
[[ -f sdkconfig.wifi ]] || { echo 'Run tools/configure_wifi.py once before building.' >&2; exit 2; }
source "$fm1_idf_root/export.sh"
[[ "$(idf.py --version)" == *5.4.1* ]] || { echo "ESP-IDF v5.4.1 is required." >&2; exit 2; }
case "${1:-diagnostic}" in
 diagnostic)
  idf.py -B build -D SDKCONFIG=sdkconfig -D 'SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.wifi' build
  ;;
 recovery)
  cat > sdkconfig.recovery <<'CFG'
CONFIG_FM1_USB_RECOVERY=y
CONFIG_FM1_ALLOW_FLASH_WRITES=n
CONFIG_FM1_TRANSPORT_SELFTEST=n
CONFIG_ESP_CONSOLE_NONE=y
CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=n
CONFIG_USJ_ENABLE_USB_SERIAL_JTAG=n
CFG
  idf.py -B build-recovery -D SDKCONFIG=sdkconfig.recovery.generated -D 'SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.wifi;sdkconfig.recovery' build
  ;;
 approved-v15)
  [[ "${2:-}" == --enable-app-writes ]] || { echo 'Write-capable build requires: approved-v15 --enable-app-writes' >&2; exit 2; }
  cat > sdkconfig.approved-v15.defaults <<'CFG'
CONFIG_FM1_USB_RECOVERY=y
CONFIG_FM1_ALLOW_FLASH_WRITES=y
CONFIG_FM1_TRANSPORT_SELFTEST=n
CONFIG_ESP_CONSOLE_NONE=y
CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=n
CONFIG_USJ_ENABLE_USB_SERIAL_JTAG=n
CFG
  idf.py -B build-approved-v15 -D SDKCONFIG=sdkconfig.approved-v15 -D 'SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.wifi;sdkconfig.approved-v15.defaults' build
  ;;
 *) echo 'usage: bash tools/build_firmware.sh diagnostic|recovery|approved-v15 --enable-app-writes' >&2; exit 2;;
esac

case "${1:-diagnostic}" in
 diagnostic) fm1_build_dir=build;;
 recovery) fm1_build_dir=build-recovery;;
 approved-v15) fm1_build_dir=build-approved-v15;;
esac
python - "${1:-diagnostic}" "$fm1_build_dir/config/sdkconfig.json" <<'PYCFG'
import json,sys
mode,path=sys.argv[1:]
c=json.load(open(path))
assert bool(c.get('FM1_USB_RECOVERY')) == (mode!='diagnostic'), 'cached USB recovery configuration disagrees with mode'
assert bool(c.get('FM1_ALLOW_FLASH_WRITES')) == (mode=='approved-v15'), 'cached write gate disagrees with mode; STOP before flashing'
assert c['ESPTOOLPY_FLASHSIZE']=='8MB' and c['SPIRAM_MODE_OCT'], 'wrong board memory configuration'
assert c['IDF_TARGET']=='esp32s3' and c['ESPTOOLPY_FLASHMODE']=='dio' and c['ESPTOOLPY_FLASHFREQ']=='80m', 'wrong chip/flash settings'
assert c['FREERTOS_HZ']==1000 and c['SPIRAM_SPEED_80M'], 'wrong timing/PSRAM configuration'
assert bool(c.get('ESP_CONSOLE_NONE'))==(mode!='diagnostic'), 'wrong native console ownership'
assert bool(c.get('USJ_ENABLE_USB_SERIAL_JTAG'))==(mode=='diagnostic'), 'wrong serial/JTAG mode'
credentials=json.load(open('wifi_credentials.json'))
assert c['FM1_AP_PASSWORD']==credentials['password'] and c['FM1_SESSION_SECRET']==credentials['secret'], 'cached credentials disagree; preserve old builds and resolve configuration before flashing'
assert c['FM1_AP_SSID']==credentials['ssid'] and c['FM1_TCP_PORT']==credentials['port'], 'cached network settings disagree with controller JSON'
print('Build-mode and XIAO memory guards verified:',mode)
PYCFG
