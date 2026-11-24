# Mercury One.1 config — Claude Instructions

Klipper configuration for a ZeroG Mercury One.1 "Hydra" CoreXY. This repo IS
`~/printer_data/config` on the printer. Sole user: the owner.

- The machine: `docs/HARDWARE.md`
- Tuning results, decisions already made, environment, TODO: `docs/STATUS.md`.
  Read its Decisions section before proposing a change.

## Working Rules (non-negotiable)

1. **Summarise first, then wait.** Before changing any file here, or any
   PrusaSlicer profile, state the change and wait for an explicit go-ahead.
   Ruled 2026-11-18 after a profile was written mid-task without warning.
2. **No commit or push without an explicit go-ahead.** Approval of a summary
   covers that one change only.
3. **`main` must always be printable.** The printer pulls `main` directly.
   Work in progress goes on a branch (`wip/<topic>`); merge when it is ready
   to try on the printer; tag when it is proven. Ruled 2026-11-24.
4. **Tag proven states** `good-YYYY-MM-DD` after a verified print. Roll back
   with a revert commit on `main`, never a force-push.
5. **Nothing takes effect until the printer runs `CONFIG_PULL`.** Say so when
   handing work back.

## Session flow

1. `git pull` (the printer and other sessions also commit here)
2. Edit, summarise, wait for the go-ahead
3. Commit and push
4. Owner runs `CONFIG_PULL` (or `CONFIG_PULL MSG="..."`) in the console
5. Verify on the printer: Klipper starts, then the feature itself
6. Tag if a print proves it; update `docs/STATUS.md`, and `docs/HARDWARE.md`
   if a part or wire changed

## Layout

- `printer.cfg`: Octopus side (pins, motion, shapers, Z, bed) and includes.
  The `#*#` block at the bottom belongs to Klipper (PIDs, mesh profiles,
  Beacon model).
- `ebb36.cfg`: toolhead board hardware only.
- `beacon.cfg`: Beacon homing, bed mesh, scan compensation, expansion offset,
  diagnostics.
- `settings.cfg`: every user-tunable number. Change behaviour here, not in macros.
- `macros/`: print, filament, calibration, system (git), vendored KAMP.
- `scripts/`: `config_pull.sh`, `config_push.sh`; `scripts/klippy/` holds our
  Klipper Python modules.
- `variables.cfg`: values the printer saves itself (not in git).
- `helixscreen/`, `moonraker.conf`, `mainsail.cfg`: owned by those tools.

## Gotchas (each one has bitten once)

- Comments use `#` only. A `;` anywhere in a value, description or shell
  command string truncates the line.
- Never hand-edit the `#*#` SAVE_CONFIG block except to add a mesh profile in
  the exact existing format.
- A new config section backed by `scripts/klippy/*.py` breaks Klipper on
  `CONFIG_PULL` until the module is linked into `~/klipper/klippy/extras`.
  Install those over SSH; a changed module needs
  `sudo systemctl restart klipper`.
- Macros cannot branch on a probe result mid-run: templates render before the
  macro executes. Read results in a separate helper macro.
- A macro that saves a measured value changes prints silently. Calibration
  macros report; they store only with `SAVE=1`.
- `[homing_override]` and `[safe_z_home]` cannot coexist with the Beacon
  homing helper. Sensorless X/Y logic lives in the `home_gcode_*` hooks, with
  a 0.5 s settle after each back-off.
- z_tilt points are nozzle coordinates, not probe coordinates.
- PrusaSlicer must be closed before its profile files are written.
- Use extrude moves of 140 mm or less (the limit is 150).

## How this file grows

Every line is a decision already made. No placeholder sections. Add a gotcha
the first time it bites. Date each ruling. Facts about the machine go in
`docs/HARDWARE.md`; results and decisions go in `docs/STATUS.md`.
