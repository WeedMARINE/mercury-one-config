# Beacon scan compensation: correct a proximity-scanned bed mesh with a stored
# "contact minus proximity" profile.
#
# Idea from RatOS (beacon_mesh.py, GPLv3: H. Keck, M. Schmidt, T. Glastonbury).
# This is an independent minimal implementation for a plain Klipper install.
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# Install (once, on the Pi):
#   ln -sf ~/printer_data/config/scripts/klippy/beacon_scan_comp.py \
#          ~/klipper/klippy/extras/beacon_scan_comp.py
#   sudo systemctl restart klipper
#
# Config:
#   [beacon_scan_comp]
#   profile: compensation      # bed_mesh profile holding contact - proximity
#   max_correction: 0.15       # refuse to apply anything larger (mm)
#
# Use: BEACON_APPLY_SCAN_COMPENSATION [PROFILE=name]  right after a proximity
# BED_MESH_CALIBRATE. The compensation profile must be 0 at the Z-home point.
import logging
from . import bed_mesh as BedMesh


class BeaconScanComp:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name()
        self.profile = config.get("profile", "compensation")
        self.max_correction = config.getfloat("max_correction", 0.15, above=0.0)
        gcode = self.printer.lookup_object("gcode")
        gcode.register_command(
            "BEACON_APPLY_SCAN_COMPENSATION",
            self.cmd_BEACON_APPLY_SCAN_COMPENSATION,
            desc=self.cmd_BEACON_APPLY_SCAN_COMPENSATION_help,
        )

    cmd_BEACON_APPLY_SCAN_COMPENSATION_help = (
        "Add the stored contact-minus-proximity profile to the active bed mesh"
    )

    def cmd_BEACON_APPLY_SCAN_COMPENSATION(self, gcmd):
        bed_mesh = self.printer.lookup_object("bed_mesh")
        prof_name = gcmd.get("PROFILE", self.profile)
        mesh = bed_mesh.get_mesh()
        if mesh is None:
            raise gcmd.error("%s: no active bed mesh to compensate" % (self.name,))
        if getattr(mesh, "scan_comp_applied", None) is not None:
            gcmd.respond_info(
                "Scan compensation '%s' is already applied to this mesh - skipped"
                % (mesh.scan_comp_applied,)
            )
            return
        profiles = bed_mesh.pmgr.get_profiles()
        if prof_name not in profiles:
            raise gcmd.error(
                "%s: bed mesh profile '%s' not found" % (self.name, prof_name)
            )
        if mesh.get_profile_name() == prof_name:
            raise gcmd.error(
                "%s: the active mesh is the compensation profile itself"
                % (self.name,)
            )
        prof = profiles[prof_name]
        try:
            comp = BedMesh.ZMesh(dict(prof["mesh_params"]), prof_name)
            comp.build_mesh([list(row) for row in prof["points"]])
        except BedMesh.BedMeshError as e:
            raise gcmd.error("%s: cannot build '%s': %s" % (self.name, prof_name, e))

        params = mesh.get_mesh_params()
        probed = mesh.get_probed_matrix()
        ny = len(probed)
        nx = len(probed[0]) if ny else 0
        if nx < 2 or ny < 2:
            raise gcmd.error("%s: active mesh has no probed points" % (self.name,))
        x_step = (params["max_x"] - params["min_x"]) / (nx - 1)
        y_step = (params["max_y"] - params["min_y"]) / (ny - 1)

        new_points = []
        lo = hi = 0.0
        for yi in range(ny):
            y = params["min_y"] + yi * y_step
            row = []
            for xi in range(nx):
                x = params["min_x"] + xi * x_step
                c = comp.calc_z(x, y)
                lo = min(lo, c)
                hi = max(hi, c)
                row.append(probed[yi][xi] + c)
            new_points.append(row)
        if max(-lo, hi) > self.max_correction:
            raise gcmd.error(
                "%s: correction of %.3f mm exceeds max_correction %.3f - not applied"
                % (self.name, max(-lo, hi), self.max_correction)
            )
        try:
            mesh.build_mesh(new_points)
        except BedMesh.BedMeshError as e:
            raise gcmd.error("%s: rebuilding the mesh failed: %s" % (self.name, e))
        mesh.scan_comp_applied = prof_name
        bed_mesh.set_mesh(mesh)
        logging.info(
            "%s: applied '%s' to %dx%d mesh, correction %.4f..%.4f",
            self.name, prof_name, nx, ny, lo, hi,
        )
        gcmd.respond_info(
            "Scan compensation '%s' applied to %dx%d mesh: correction %+.3f to %+.3f mm"
            % (prof_name, nx, ny, lo, hi)
        )


def load_config(config):
    return BeaconScanComp(config)
