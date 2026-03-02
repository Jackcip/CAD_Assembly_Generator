import os
import cadquery as cq
from wing import build_wing_shell, get_wing_mass
from ribs import build_all_ribs, ribs_mass
from spar import build_spars, spar_mass


def generate_assembly(params):

    try:
        EXPORT_PATH = params["EXPORT_PATH"]
        EXPORT_SINGLE_PARTS = params["EXPORT_SINGLE_PARTS"]

        wing_mass_type = params["WING_MASS_TYPE"]
        wing_mass_val = params["WING_MASS_VAL"]

        ribs_mass_type = params["RIBS_MASS_TYPE"]
        ribs_mass_val = params["RIBS_MASS_VAL"]

        spar_mass_type = params["SPAR_MASS_TYPE"]
        spar_mass_val = params["SPAR_MASS_VAL"]

        if EXPORT_PATH:
            os.makedirs(EXPORT_PATH, exist_ok=True)

        wing = build_wing_shell(params)
        ribs = build_all_ribs(params)
        spars = build_spars(params)

    except Exception as e:
        raise

    if wing_mass_type == "Density":
        mass_wing_kg = get_wing_mass(wing, wing_mass_val)
    else:
        mass_wing_kg = wing_mass_val

    if ribs_mass_type == "Density":
        mass_ribs_kg = ribs_mass(ribs, ribs_mass_val)
    else:
        mass_ribs_kg = ribs_mass_val

    if spar_mass_type == "Density":
        mass_spar_kg = spar_mass(spars, spar_mass_val)
    else:
        mass_spar_kg = spar_mass_val

    total_mass_kg = mass_wing_kg + mass_ribs_kg + mass_spar_kg

    cg_wing = wing.val().Center()
    cg_ribs = ribs.val().Center()
    cg_spar = spars.val().Center()

    cg_x = (
        mass_wing_kg * cg_wing.x + mass_ribs_kg * cg_ribs.x + mass_spar_kg * cg_spar.x
    ) / total_mass_kg
    cg_y = (
        mass_wing_kg * cg_wing.y + mass_ribs_kg * cg_ribs.y + mass_spar_kg * cg_spar.y
    ) / total_mass_kg
    cg_z = (
        mass_wing_kg * cg_wing.z + mass_ribs_kg * cg_ribs.z + mass_spar_kg * cg_spar.z
    ) / total_mass_kg

    asm = cq.Assembly()
    asm.add(wing, name="WingShell", color=cq.Color(1, 1, 0, 0.3))
    asm.add(ribs, name="Ribs", color=cq.Color(0, 0, 1))
    asm.add(spars, name="Spars", color=cq.Color(0, 0, 0))

    if EXPORT_PATH:
        asm.export(
            os.path.join(EXPORT_PATH, "wing_assembly.step"),
            exportType="STEP",
            tolerance=0.01,
        )

        if EXPORT_SINGLE_PARTS:
            wing.export(os.path.join(EXPORT_PATH, "wing.step"), tolerance=0.01)
            ribs.export(os.path.join(EXPORT_PATH, "ribs.step"), tolerance=0.01)
            spars.export(os.path.join(EXPORT_PATH, "spars.step"), tolerance=0.01)

    return total_mass_kg, (cg_x, cg_y, cg_z)
