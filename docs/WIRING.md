# External-breakout hardware review

## Completed case and electrical-validation limits

The completed 2026-11-21 case used an assembled connection from the XIAO underside native USB
pads to a generic red USB-C female breakout. The breakout has CC1, D+, D-, CC2,
GND and VBUS labels and two unidentified SMD parts near CC. No manufacturer,
resistor values or internal schematic are known. Color and labels do not
identify a circuit. No further manufacturer identification is required to
continue software work; **electrical compatibility remains unknown**.

No multimeter measurements were recorded in that case. A real ROM response,
verified restoration and owner-reported normal boot were obtained, but they do
not retroactively verify the unknown circuit or every solder joint. For any
reproduction, target attachment is blocked until an appropriate meter or a
qualified person verifies the assembly.

```
Mac Terminal -- Wi-Fi/TCP --> XIAO ESP32-S3
                              | TP8/D+, TP7/D-, GND
                              v
                    external USB-C female breakout
                              | passive USB-C data cable
                              v
                            FM-1
```

The XIAO built-in USB-C receptacle is for programming only, with the FM-1
physically detached. It stays EMPTY while recovery firmware runs. It shares
its data nets with the test pads: the external breakout does not create a
second USB controller. A Mac USB data cable must never remain attached during
FM-1 recovery.

Power is independent: single-cell battery -> existing TP4056 protection/charge
arrangement -> XIAO battery supply; FM-1 -> its own battery. The TP4056 wiring,
protection path, polarity and voltages have not been electrically verified.
Do not power an external charger during integration checks or connect two
charging systems by guesswork. Do not connect battery/3V3/5V to the breakout.

## Verified schematic mapping

Official Seeed V1.3, sheet 03 ESP32S3 (PDF page 4), and the previously saved
V1.1 schematic show:

| XIAO connection | Net / chip connection | External breakout |
|---|---|---|
| TP8 | ESP_USB_D+ -> GPIO20, U1 pin 26 | D+ |
| TP7 | ESP_USB_D- -> GPIO19, U1 pin 25 | D- |
| GND | Board ground | GND |
| No power wire | No XIAO source connection | VBUS left unwired |
| No external wires | No XIAO CC connections | CC1/CC2 left externally unwired |

TP7/TP8 are on the **chip side** of the built-in receptacle's R3/R4 series
resistors: R3 is 22 ohms on D-, R4 is 22 ohms on D+. The receptacle uses
USB_D-/USB_D+ on the opposite side. Therefore the external test-pad path
bypasses those series resistors; the unused receptacle branch remains a stub.
The pads are electrically suitable access to native USB, but solder bridges,
wire length/routing, direct-drive loading and signal integrity are untested.
Do not assume a schematic validates the actual solder joints. Keep wiring
short and data wires paired; no added resistor or timing change is justified
without evaluating the actual assembly.

Built-in CC1 and CC2 have R1/R2, 5.1 kohm to ground. They advertise a Type-C
sink/device, not a source/host. **These resistors do not determine the external
breakout's CC configuration:** the new wiring exports only D+, D- and GND.
The battery circuit has no 5 V host boost; TP4056 is not a boost converter.

The recovery code already uses PIN_DP=20 and PIN_DM=19. recovery_init()
releases USB-Serial-JTAG's pull-up/pads and configures the same GPIOs before
USB_KEY. Native host handoff later uses the built-in PHY. No new GPIO mapping
is needed for test pads. The same local USB_KEY/ACK/calibration algorithm is
applicable electrically to these nets, but no timing or target handshake has
been measured through this jumper assembly. Low-level timing is unchanged.

## External CC and standard cable assessment

Upstream Transporter explicitly requires D+, D-, GND and no VBUS supply. This
is a special self-powered ROM link, not standards-compliant negotiated USB-C
host operation. Ordinary USB host support alone proves neither CC nor target
compatibility.

A known passive USB 2.0 C-to-C data cable can carry D+/D- and ground through
the external receptacle. Its VBUS conductor can terminate at an **unpowered**
breakout VBUS contact. Unlike the obsolete direct-receptacle plan, this does
not inherently require cutting the cable's VBUS wire: isolation must be between
breakout VBUS and every XIAO/battery/charger power source. It must be measured,
not inferred from the absence of a jumper. The FM-1's VBUS is still connected
to that exposed breakout contact through the cable, so insulate the contact.

If the SMD parts are solely passive Rd pull-downs from CC to ground, independent
of D+/D-, they do not themselves supply VBUS or switch data. Two sink roles
would not negotiate a normal powered USB-C attachment; that does not alone
prove this raw ROM signaling path impossible. However, the parts' values,
connections and possible CC-to-VBUS paths are UNKNOWN. No compatibility claim
is made for this breakout. Active/muxed cables cannot be assumed to pass data
without power; cable topology/orientation and both USB2 data pin sets matter.
Do not add/remove CC components by guesswork.

## Required electrical checks — NOT PERFORMED

Obtain/borrow a suitable multimeter, or have a qualified person verify:

1. With the assembly unpowered and target detached, identify actual TP8/TP7
   solder points and confirm TP8 -> breakout D+ -> cable far-end D+, and
   TP7 -> D- -> far-end D-. Verify both cable plug orientations as applicable.
2. Verify common ground reaches the cable far end and XIAO ground. Check the
   TP4056 protected-output grounding/polarity against the actual module circuit;
   do not assume labels or a lit LED prove correct protection wiring.
3. Verify there are no low-resistance solder shorts between D+, D-, GND,
   VBUS, neighboring pads, battery or supply rails. Account for real components
   and IC protection paths rather than treating every meter reading as a short.
4. Trace/measure each CC-area SMD part: resistor or other component, value,
   CC1/CC2 endpoints and any connections to VBUS, GND or data. Confirm the
   receptacle combines the required A/B USB2 data pins correctly.
5. Verify breakout VBUS has no intentional or accidental path to XIAO 5V,
   3V3, battery or charger output. It remains connected to the cable's VBUS
   conductor but must not receive a source from this assembly.
6. Before target attachment, confirm the XIAO supply polarity and voltage at
   its battery contacts (a normal single Li-ion cell is roughly 3.0..4.2 V,
   subject to actual cell/protection limits), stable operation on battery,
   and that the powered assembly does not source VBUS to the target. A floating
   unwired conductor is not a regulated zero-volt output.
7. Confirm built-in XIAO USB-C is empty, other chargers are detached, FM-1 is
   OFF and on its own battery, and Wi-Fi ping/log work in recovery firmware.

Resistance/continuity tests require removal of power from the points tested.
Do not resistance-test a live board. During verification, the FM-1 remains detached throughout;
there is no need to open the FM-1 just to measure this assembly.

Until these checks establish compatibility, stop before FM-1 attachment.
XIAO programming with the target detached and --after no-reset is separate.

## Sources

- Seeed V1.3: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_V1.3_SCH_260115.pdf
- Official V1.1: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_SCH_v1.1.pdf (inspection cache retained privately)
- Upstream: https://github.com/kurogedelic/FM-1-transporter/tree/14fd4dfe08b5afb403693142b07fcb21a95092ba
- IDF v5.4.1: https://docs.espressif.com/projects/esp-idf/en/v5.4.1/esp32s3/api-reference/peripherals/usb_host.html
- Local code: main/compat.h, main/recovery.c, main/main.c, main/host.c.
