# Mercury One.1 "Hydra" — status

What has been tuned, decided and is still to do. Update after each session.
The machine itself is described in `HARDWARE.md`; working rules are in `../CLAUDE.md`.

**Current state (2026-11-24):** commissioned and printing ASA and PLA at 0.20 mm on Klipper 0.14.0. Shapers retuned after the fan shroud; scan compensation and the nozzle expansion offset are live. Biggest open quality item: the 0.30 mm ASA profiles.

## Environment
- Klipper v0.14.0 (updated 2026-11-24 from v0.13.0-827), Python 3.13, Raspberry Pi OS Trixie.
- Beacon module linked into Klipper extras; contact homing.
- Shake&Tune carries a one-line `import importlib.util` patch for Python 3.13, so its repo shows as dirty.
- `gcode_shell_command` extension (KIAUH) runs `scripts/config_pull.sh` / `config_push.sh`.
- `scripts/klippy/beacon_scan_comp.py` symlinked into `~/klipper/klippy/extras`.
- Moonraker's system package update fails while 4 libcamera/rpicam packages are kept back (`sudo apt full-upgrade`, or wait for the phased rollout).

## Decisions (do not re-propose without new evidence)
- Adaptive heat soak: not needed; fixed 10 min is adequate (soak log 2026-11-19).
- Multipoint true-zero correction: not needed; contact spread on this sheet is 0.014 mm.
- `hold_current` on A/B: removed once the driver fan was fitted.
- 25x25 bed mesh: no; 15 rows suffice because X is sampled continuously.
- ZV shaper on Y: no; 21 % residual vibration.
- `max_accel` above 6000 on walls: no; limited by the 45 Hz Y mode. 10k for infill/travel only is parked.
- Nozzle expansion: the first layer is the reference, not the calibration macro (0.0419 x 1.125).

## Tuning results
- **Input shaper, current (2026-11-24, after fitting the fan shroud; commit 36faeff):** X main peak 59.9 Hz (was 64.8; shroud mass) with a shoulder near 66 and a new small 125 Hz peak → **MZV 62.8** (2.1 % residual, allows ~11.6k). Y main 45.4 Hz unchanged, minor peaks 86 / 123 Hz → **MZV 46.6** (3.8 % residual, allows ~6.3k). **max_accel stays 6000.** The ~125 Hz peak on both axes is most likely the shroud itself — check its screws if fine wall ripple appears. 10k accel is possible for infill/travel only (walls limited by the 45 Hz Y mode; needs ~57 Hz for 10k on walls = lighter gantry) — parked, needs a skipped-step test first.
- **Klipper updated v0.13.0-827 → v0.14.0** (2026-11-24). Post-update checks passed: G28, BEACON_POKE_TEST (range 0.0056, latency 3–4), BEACON_APPLY_SCAN_COMPENSATION on the proximity profile. Shake&Tune repo shows 'dirty' because of the importlib.util patch (harmless). System package update in Moonraker fails only because 4 libcamera/rpicam packages are kept back (`sudo apt full-upgrade` or wait for the phased rollout). PID_CALIBRATE maths was fixed upstream 2026-10-18 — re-run PID only if temperatures oscillate.
- Shake&Tune before the shroud (2026-11-18, concrete top; superseded): belts 96.3–96.8 % match. X 64.8 Hz → **MZV 66.0**. Y 45.4 Hz main + 70 Hz minor → **MZV 47.6** (6.7 % residual, allows ~6.7k) → **max_accel 6000**. Verified on a 20 mm cube at 6000 accel, 100–200 mm/s walls, no cooling slowdown: no visible ringing. Alternative if ringing ever shows: Y 2hump_ei 66.8 @ 4500. The earlier 67 Hz Y peak with Z component was the EBB bracket flexing under the LIS2DW, not the gantry — no gusset needed.
- Pressure advance: PLA 0.05, ASA 0.04 (garethky PrusaSlicer PA tool; Prusa's standard-nozzle values match — UHF+CHT doesn't lower PA because the long melt zone cancels the CHT viscosity gain).
- Max flow, in-air test (2.405 mm³ per mm): PLA 30 sustained / 35 slip. ASA 255 °C 30 ok / 35 gear marks; 265 °C clean at F980 = 39. Slicer cap **30** for both.
- Extrusion multiplier: PLA 0.965, ASA 0.96 (0.20). 0.30 not cubed.
- **Nozzle thermal expansion offset** (RatOS method, beacon.cfg): contact Z=0 is found at 150 °C, so START_PRINT lifts Z by `multiplier × (print_temp − 150) × coefficient/100` after M109. Coefficient default **0.07 mm/100 °C** (RatOS typical for Rapido 2+ UHF 0.06–0.08; sanity 0.05–0.10), measurable with `BEACON_CALIBRATE_NOZZLE_TEMP_OFFSET` (contact probe at 150 and 250). **Working setting since 2026-11-19: coefficient 0.0419 × multiplier 1.125 = +0.054 mm at 265 °C (≈ +0.033 at 220); first layers confirmed fine on it 2026-11-24.** The earlier +0.09 came from one test cube and was more than needed. Calibration runs: 0.0419 (11-19), then 0.0344 / 0.0294 on 11-24 — readings creep upward for minutes after reaching temperature (150 °C baseline 0.0738 → 0.0856 between passes) and ooze gives false triggers at 250, so the short-dwell value shrinks every run. Macro changed 2026-11-24 (commit after 36faeff): reports only (SAVE=1 to store), SOAK=180 s per temperature, creep-corrected value, one 3 mm retract at 250; ~18 min. Trust the first layer over this test. Multiplier: layer-1 babystep then `Z_OFFSET_APPLY_PROBE` (overridden — Beacon's own refuses with contact) saves it to `variables.cfg`, or `SAVE_VARIABLE VARIABLE=nozzle_expansion_multiplier VALUE=x`. **Current multiplier 1.125** (ASA cube wanted +0.09 total at 265 °C; PLA at 220 gets ~+0.055). Without the offset the first layer flashed (too low) vs the BLTouch manual setting.
- **Scan compensation — live since 2026-11-19 (commit bb3f743).** Second contact/proximity run reproduced the first (contact repeat sd 0.014, proximity 0.009, difference maps correlate 0.88, row means within 0.003), and the bands do not follow scan-row parity → bed-fixed (magnets suspected), so a stored correction is valid for adaptive meshes. Own klippy module `scripts/klippy/beacon_scan_comp.py` (symlinked into `~/klipper/klippy/extras`; idea from RatOS beacon_mesh.py, which is too RatOS-entangled to install) adds `BEACON_APPLY_SCAN_COMPENSATION`: adds bed_mesh profile `compensation` (9×9, contact − proximity, average of both runs, 0 at bed centre, −0.03…+0.07 mm) to the active mesh; refuses > 0.15 mm or a second application. `[beacon_scan_comp]` in beacon.cfg; START_PRINT calls it right after the adaptive mesh. Offline test: proximity-vs-contact range 0.107 → ~0.03 mm (in-sample). Verified loading on the printer (15×15: −0.023…+0.069). Measured at bed 105 only; re-measure (BEACON_CONTACT_MESH twice) after a sheet/bed change, and a 60 °C set for PLA is still open. Module updates need `sudo systemctl restart klipper`; changes to this module must be installed over SSH, not CONFIG_PULL, if they add config sections.
- **Soak drift log** (2026-11-19, bed 105, Beacon at Z2.5 over centre, 1 Hz via Moonraker `/printer/beacon/status`): gap closes 0.25 mm over 36 min after reaching temp; rate peaks ~290 nm/s at minute 7, ~210 nm/s at minute 10, ~65 nm/s at minute 20; Beacon coil 26 → 76 °C so part may be sensor drift (not separated). Drift direction = more squish, so adhesion at the 10 min soak is fine (user-confirmed on prints); effect on a 2 min first layer ~0.025 mm. **Decision: keep SOAK 10; adaptive heat soak module (RatOS beacon_adaptive_heat_soak.py, needs pygam, ≥6.5 min minimum) not needed.**
- Contact vs proximity mesh, first run (2026-11-18, bed 105, 9×9 contact SAMPLES=2 DROP=1 vs 15×15 proximity): shapes agree; proximity − contact range **0.104 mm** (−0.068 … +0.036). Two components: a smooth bias (proximity ~0.02 low on average, 0.04–0.06 low along the right edge / rear-right — eddy response drifting from the centre-calibrated model; this is what scan compensation fixes, above RatOS's 0.03 threshold) and a **row-alternating noise** of ~0.03 (rows Y240/154/96/10 vs the rows between — either single-sample contact noise or proximity scan-direction bias). (Resolved by the second run — see scan compensation above.) Profiles `contact` and `proximity` saved in printer.cfg (commit 1794792). Meanwhile first layers are centre-referenced by contact and adaptive meshes span regions with 0.01–0.03 error.

## START_PRINT (macros/print.cfg)
`SET_GCODE_OFFSET Z=0` → home → park centre → bed heat + SOAK (default 10 min when BED ≥ 90) → nozzle 150 → `G28 Z METHOD=CONTACT CALIBRATE=1` (touch + model on the hot plate) → Z_TILT_ADJUST → `BED_MESH_CALIBRATE ADAPTIVE=1 RUNS=2` → `BEACON_APPLY_SCAN_COMPENSATION` → `G28 Z METHOD=CONTACT CALIBRATE=0` (final touch, Beacon order) → SMART_PARK → M109 → `_BEACON_APPLY_TEMP_OFFSET` → LINE_PURGE. END_PRINT resets the offset. Three nozzle touches per print is the Beacon-recommended sequence; the main failure mode is plastic on the tip (wiper, TODO #3).

## Beacon / maintenance macros (beacon.cfg, macros/filament.cfg)
- `BEACON_POKE_TEST` — 5 pokes at centre, reports range (≤ 0.01 ok). After nozzle change / crash / odd first layers.
- `BEACON_CONTACT_SPREAD [APPLY=1]` — 6 contact points within 1.5 mm of centre; reports range/median (APPLY lifts by the median). Re-run on a new sheet.
- `BEACON_CONTACT_MESH BED=105 [SOAK=10]` — 9×9 contact mesh (profile `contact`) + proximity mesh (profile `proximity`) at temp; SAVE_CONFIG after. Run 2026-11-18 and 2026-11-19 (current `contact`/`proximity` profiles are run 2; run 1 is in git at 1794792).
- `BEACON_CALIBRATE_NOZZLE_TEMP_OFFSET [TEMP=250 SOAK=180 SAVE=0]` — measures the expansion coefficient and reports it; stores only with SAVE=1.
- `COLD_PULL [TEMP=220 PULL_TEMP=80]` — heat, extrude 30, cool, prompt to pull. `M600` — PAUSE + UNLOAD_FILAMENT (slicer colour change).
- Adaptive heat soak: evaluated and dropped 2026-11-19 (see soak drift log).

## Config — git workflow
- Repo: **github.com/WeedMARINE/mercury-one-config** (private) = `~/printer_data/config` on the Pi. Claude GitHub App installed → Claude can clone and push.
- `CONFIG_PULL MSG="what I changed"`: commits local edits ("edit from printer: MSG [files]"), rebases on origin/main, pushes to main, RESTART. On a rebase conflict it pushes the local commit to `printer-edits/<timestamp>`, resets to origin/main and says so in the console. `CONFIG_PUSH` commits + pushes only. Scripts in `scripts/`; `macros/system.cfg` via gcode_shell_command (KIAUH). `#` comments only in cfg; no `;` inside shell command strings or description values. `.gitignore`: printer-*.cfg, helixscreen crash log, *.bak, ShakeTune_results/, *.zip, variables.cfg.
- Layout: `printer.cfg` (Octopus: motion, input_shaper, Z, z_tilt, bed, bay fan, includes, [save_variables]), `ebb36.cfg` (EBB36 hardware only), `beacon.cfg` ([beacon], [bed_mesh], expansion + diagnostic macros), `variables.cfg` (gitignored: measured coefficient/multiplier), `macros/homing.cfg` (comment), `macros/print.cfg`, `macros/filament.cfg` (load/unload/purge/runout + COLD_PULL, M600), `macros/calibration.cfg` (G32, resonance_tester accel_chip beacon, shaketune, PID_HOTEND/PID_BED), `macros/kamp_*.cfg`, `macros/system.cfg`. PIDs/mesh profiles/beacon model in SAVE_CONFIG block of printer.cfg. **Layout commit done (3dd77f0):** `settings.cfg` holds _SETTINGS (park spots, soak, purge line), _CLIENT_VARIABLE, _FILAMENT_VARS, _BEACON_VARS, _KAMP_Settings; `[board_pins octopus]` / `[board_pins ebb]` aliases name every pin. `scripts/klippy/` holds our klippy modules.

## PrusaSlicer (profile folder `%APPDATA%\PrusaSlicer`, reachable from Claude via the desktop app)
- Klipper flavor, relative E, label objects firmware-specific, bed 260×250, physical printer via Moonraker. Bed texture PNG marks purge zone. Machine limits "time estimate only", **6000** x/y/extruding/travel (2026-11-18). Colour change G-code should be `M600`.
- Start: `M104 S0 / M140 S0 / START_PRINT BED=[first_layer_bed_temperature] EXTRUDER=[first_layer_temperature]`. End: `END_PRINT`. PA via filament start G-code. Filament end needs a comment line for the PA tool.
- **Profile model (Prusa-style):** Printer owns geometry/G-code/accel limits/retraction defaults. Filament owns temps, cooling, max volumetric, EM, PA, retraction overrides. Print owns layer/widths/walls/infill/speeds. Suffix `(TEST)` = changed, not fully validated; `(UNTESTED)` = placeholder; `(RINGING TEST)` = diagnostic copies (0.20 SPEED with 6000 accel everywhere; ASA with slowdown 0) — not for parts.
- Print `0.20 SPEED/QUALITY/STRUCTURAL (TEST)` (from Prusa `0.20mm SPEED @MK4IS 0.4`): min thickness 0.7/0.5, Arachne, monotoniclines top @0.42, anchors 2/12, overlap 15 %, speeds 150/100/80 (QUALITY 120/70/60, STRUCTURAL 100/60/60), infill 200, solid 170, top 80, **accel 6000** (default/perimeter/infill/solid/travel, since 2026-11-18; STRUCTURAL perimeter 3000) with outer 3000/2500/2000, top 2000, bridge 1500, first layer 40 + infill 100 @ 500, short-travel accel 250, dynamic overhang 15/25/50/80 %, skirt 2×3 layers, Prusa support block, arc fitting, gcode_resolution 0.008. SPEED = grid 15 % 2 walls 5/4; QUALITY = gyroid 15 % 3 walls 6/5 (verified in step with SPEED 2026-11-18); STRUCTURAL = gyroid 30 % 4 walls 7/5 EF 0.15. **0.30 profiles still untouched** apart from the 6000 accel — handle on 0.30 STRUCTURAL showed thin/separated layers.
- Filament: `Polymaker ASA @MercuryOne (TEST)` — 265 first / 255 other, bed 105/105, fan 15/40 always-on off first 4, slowdown 10 s / min 25 (on a 20 mm cube this makes every layer 10 s → 22 min vs 13 min without; on real parts it rarely engages), consistent_surface +10 mm, crossing cap 140, vol 30, EM 0.96, PA 0.04, retract 0.8, shrink 0.22 % XY+Z. `Polymaker PLA @MercuryOne (TEST)` — 225/220, fan 85/100 full from L3 below 40 s, slowdown 8/15, consistent_surface, dynamic overhang fan 100, crossing cap 140, vol 30, EM 0.965, PA 0.05. `Generic PETG (UNTESTED)` placeholders.

## TODO (updated 2026-11-24)
**Hardware**
4. Proper driver fan (on order; Ender 5 blower is the stopgap).
5. Bed thermal cutoff — KSD301 too big; axial thermal fuse (157 °C 10 A) in the live lead is the alternative. Parked; no unattended ASA until fitted.
6. Smarter soak — closed: fixed 10 min is adequate (soak drift log).
9. Measure real Z travel; set `position_max` (250 placeholder).
**Software / config**
11. `verify_heater` tuning for extruder after a long high-flow print.
12. Dashboard macros (PREHEAT_x, COOLDOWN, PARK_FRONT).
13. Orbiter current/tension experiment to lift the slip point (optional).
14. HelixScreen: enable confirm on emergency stop.
19. Beacon follow-ups: watch a first layer in the rear-right with scan compensation on; contact/proximity set at bed 60 for PLA; nozzle expansion settled at 0.0419 × 1.125 (re-run the new report-only calibration only out of curiosity); optional per-filament squish via `Z_ADJUST` from slicer filament start G-code; consider `mesh_min` X 10 → 20 to drop the left-edge coil overhang.
20. Skew calibration print.
21. Skippable heat soak: pause-based soak with a timer, `SKIP_SOAK`, a HelixScreen prompt dialog with a Skip button, and a RESUME guard (Helix's print page has fixed controls, no custom buttons). Design described 2026-11-19; awaiting go for a commit summary.
22. Optional: max_accel 10000 for infill/travel only, after a skipped-step test.
**Slicer**
2/15. **0.30 ASA tuning** — diff 0.30 SPEED/STRUCTURAL/VASE vs Prusa `0.30mm … @MK4IS 0.4`, apply the same pass; 0.3 cube for EM (expect 0.98–1.0) or wider lines; reprint the handle.
16. PETG profile when a spool is opened (PA ≈ 0.07 expected).
17. PLA stringing re-test at 220 °C.
18. "0.20 SPEED PLA" faster variant — only if PLA time matters.
**Design**
3. **Nozzle wiper + poop chute redesign** — Ender 5 frame (not Plus); ~5 mm gap between plate and frame → needs an indexer for the steel plate. Once it exists, START_PRINT purge and PURGE move off the bed, and a wipe can precede the contact touch.
**Done since last note**: fan shroud fitted and shapers retuned, Klipper 0.14.0 update verified; scan compensation module + profile live, layout commit (settings.cfg, board_pins), soak drift logged and adaptive soak dropped; nozzle expansion offset (multiplier 1.125) + Z_OFFSET_APPLY_PROBE override, beacon.cfg/ebb36.cfg split, poke/spread diagnostics (both excellent), contact-vs-proximity mesh measured, COLD_PULL, M600, slicer accel 6000, RINGING TEST slicer copies; Beacon RevH installed (contact homing, z_tilt, 15×15 mesh, hooks with settle pauses), shapers re-measured at the nozzle and verified at 6000 accel, START_PRINT contact sequence at bed temp, CONFIG_PULL conflict-safe with MSG, 0.20 profiles + ASA/PLA filament profiles rewritten, ASA bracket verified, chopper noise fixed, BLTouch removed (items 1, 7, 8, 10 closed).
