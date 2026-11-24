# Mercury One.1 "Hydra" — hardware

What the machine physically is. Update when a part is swapped or rewired.
Tuning results, decisions and open work are in `STATUS.md`.

## Overview

| | |
|---|---|
| Printer | ZeroG Mercury One.1 with Hydra bed, built on an Ender 5 frame (not the Plus) |
| Kinematics | CoreXY; bed moves in Z on three independent lead screws |
| Printable area | 260 x 250 mm (X x Y), Z 250 mm. **Provisional**: see the note under Coordinate frame |
| Host | Raspberry Pi 5, Raspberry Pi OS Trixie, hostname `BoomMercuryOne1` |
| Firmware | Klipper, Moonraker, Mainsail (installed with KIAUH) |
| Screen | BTT HDMI5 touchscreen running HelixScreen |
| Mainboard | BTT Octopus Pro V1.1 (STM32H723), USB to the Pi |
| Toolhead board | BTT EBB36 GEN2 V1.0 (STM32G0B1), USB to the Pi through the BTT EBB USB Adapter V1.0 |
| Probe | Beacon RevH, its own USB cable to the Pi |
| Toolhead | E34M1 (EVA 3 for the Mercury One.1) |

Not recorded yet: frame outer dimensions, moving mass.

## Power

| Rail | Supply | Feeds |
|---|---|---|
| 24 V | Mean Well LRS-350-24 | Octopus main power, Z drivers, toolhead, fans, and the Pi's converter |
| 48 V | Mean Well LRS-200-48 | A/B drivers only, through the Octopus MOTOR_POWER input |
| USB-C PD for the Pi | DC to USB-C PD converter (10-30 V input, 65 W max, right-angle plug), fed from the 24 V rail | Raspberry Pi 5 |
| Mains 220 V | IEC inlet with T8A fuse | Bed heater through the solid-state relay |

The bed has no independent thermal cutoff yet (see `STATUS.md`, TODO).
Klipper cannot cut bed power if the relay fails closed.

## Motion

| Axis | Motor | Driver | Supply | Run current | Notes |
|---|---|---|---|---|---|
| A/B (X/Y) | LDO 42STH48-2004MAH, 0.9 deg | BTT TMC5160T Pro, SPI | 48 V | 1.0 A, no hold current | 16 microsteps, rotation distance 40, spreadCycle |
| Z, Z1, Z2 | StepperOnline 17HS15-1504S-X1, 1.8 deg | BTT TMC5160 V1.x, SPI | 24 V | 0.8 A | TR8x2 lead screws, rotation distance 2 |
| Extruder | LDO-36STH20-1004AHG (Orbiter 2.5) | TMC2209 on the EBB36, UART | 24 V | 0.85 A | spreadCycle |

- All TMC5160 sense resistors are 0.075 ohm.
- A/B chopper: TBL 2, TOFF 5, HSTRT 0, HEND 2, TPFD 4. These values removed
  a noise band at 40 and 80 mm/s.
- Both A and B direction pins are inverted.
- Driver slots: MOTOR0 = X/A, MOTOR1 = Y/B, MOTOR2 = Z front-left,
  MOTOR3 = Z1 front-right, MOTOR4 = Z2 rear-centre.
- X and Y home sensorless (DIAG jumpers fitted, StallGuard threshold 1,
  current dropped to 0.6 A while homing). X homes to the right stop, Y to the
  front stop.
- Limits in Klipper: 300 mm/s, 6000 mm/s2, Z 10 mm/s.
- Driver cooling: two 40 mm fans on a printed plate over the Octopus. FAN2
  covers slots 0-2 (A/B and Z); FAN3 covers slots 3-4 (Z1 and Z2) and was
  added 2026-11-24. Both run whenever a motor is enabled.
- Z1 incident, 2026-11-24: the front-right Z motor stalled twice (once while
  homing, once on the lift at a filament-tangle pause) with no console error,
  and `STEPPER_BUZZ` showed it shaking instead of rocking smoothly. Swapping
  the driver modules between slots 3 and 4 cleared it, which points to a poor
  contact, not a dead part. The driver that was in slot 3 during the incidents
  is now in slot 4 (rear Z2) and is the suspect: if the rear screw misbehaves,
  replace that driver; if the front-right does again, look at the slot 3
  socket or that motor's cable. Slots 3-4 had no airflow at the time.

## Toolhead

| Part | Detail |
|---|---|
| Hotend | Phaetus Rapido V2.0 UHF, about 115 W; heater duty capped at 0.8 for the EBB's 5 A fuse |
| Nozzle | CHT 0.4 mm, brass |
| Hotend sensor | PT1000 on TH0 with the GEN2's 2.2 kohm pull-up; limit 350 C |
| Extruder | Orbiter 2.5, rotation distance 4.611 (measured) |
| Filament sensor | Orbiter smart sensor: filament switch plus unload button |
| Heatbreak fan | Noctua NF-A4x10 24 V on FAN2, tachometer monitored; its PWM wire is not used |
| Part cooling | 24 V blower on FAN1, with the fan shroud fitted 2026-11-24 |
| Accelerometers | Beacon's (used for input shaping); the EBB's LIS2DW is no longer used because its bracket flexes |

Orbiter sensor wiring, on the EBB's I2C header P14: pin 1 = 5 V, pin 2 = GND,
pin 3 (PA7) = unload button, pin 4 (PA6) = filament switch. The header has
10 kohm pull-ups, 470 ohm series resistors and clamp diodes on both lines.
A straight-through cable would miswire it; the plug was re-pinned.

## Probe

Beacon RevH on a printed E34M1 mount. The coil sits 17 mm behind the nozzle
in Y and in line with it in X. It homes Z by touching the nozzle to the plate
(contact) and scans the bed mesh without contact (proximity). The BLTouch
used during early commissioning has been removed.

## Bed

| Part | Detail |
|---|---|
| Heater | Hydra 600 W, 220 V mains |
| Switching | Omron G3NA-210B solid-state relay, driven from the Octopus bed output |
| Sensor | NTC 3950 on TH0; limit 130 C |
| Surface | Textured steel sheet on a magnetic base; the magnet limits the bed to about 105 C |
| Levelling | Three lead screws: front-left, front-right, rear-centre |
| Flatness | About 0.39 mm twist: left-rear low, right-rear high (confirmed by contact probing) |

## Pin map

These match the `[board_pins]` aliases in `printer.cfg` and `ebb36.cfg`,
which are the only places physical pins appear in the config.

**Octopus Pro V1.1**

| Function | Step | Dir | Enable | SPI CS | DIAG |
|---|---|---|---|---|---|
| X/A (MOTOR0) | PF13 | PF12 | PF14 | PC4 | PG6 |
| Y/B (MOTOR1) | PG0 | PG1 | PF15 | PD11 | PG9 |
| Z (MOTOR2) | PF11 | PG3 | PG5 | PC6 | |
| Z1 (MOTOR3) | PG4 | PC1 | PA2 | PC7 | |
| Z2 (MOTOR4) | PF9 | PF10 | PG2 | PF2 | |

MOTOR3's enable pin is PA2 on board revision V1.1 (it differs on V1.0).

| Function | Pin |
|---|---|
| Bed heater output | PA1 |
| Bed thermistor (TH0) | PF3 |
| Driver fan 1 (FAN2) | PD12 |
| Driver fan 2 (FAN3) | PD13 |
| Spare thermistor input (TH1) | PF4 |
| Spare fan outputs (FAN4, FAN5) | PD14, PD15 |

**EBB36 GEN2 V1.0**

| Function | Pin |
|---|---|
| Extruder step / dir / enable / UART | PB14 / PA8 / PB6 / PB3 |
| Hotend heater (HE0) | PB4 |
| Hotend sensor (TH0) | PA3 |
| Board temperature sensor | PA0 |
| Part fan (FAN1) | PA5 |
| Heatbreak fan (FAN2) and tachometer | PD2, PA4 |
| Filament switch | PA6 |
| Unload button | PA7 |
| LIS2DW chip select | PB1 |
| Spare: probe input (optocoupler), servo, endstop | PB8, PB5, PA15 |

The GEN2 pin map is not the same as the older EBB36 V1.2.

## Coordinate frame

**Provisional (2026-11-24).** The printer runs safely on these limits, but they
are due a re-measure: Z travel has never been measured (250 is a placeholder),
and the X and Y limits were set while the BLTouch mount was fitted. That mount
is what kept the toolhead off the left stop, so travel may now be larger.
Limits, slicer bed size, mesh area and tilt probe points all follow from this
and change together.

| | |
|---|---|
| Origin (0, 0) | Front-left corner of the build sheet |
| X travel | -20 to 270; homes at 270 (right) |
| Y travel | -10 to 250; homes at -10 (front) |
| Why Y stops at 250 | The fan duct hits the rear-right belt tower beyond 255 |
| Bed centre and Z home point | 130, 130 |
| Hard-stop travel | About 290 x 275 mm |
| Lead screw positions | Front-left (-60, -13), front-right (290, -13), rear (115, 267) |
| Tilt probe points (nozzle) | (40, -2), (230, -2), (130, 223) |
| Mesh area | 10, 10 to 250, 240; 15 x 15 points |
| Parking | End of print and pause at (240, 240); idle filament changes at (20, 5) with the bed lowered |
