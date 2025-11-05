import os
import cadquery as cq
from wing import build_wing_shell
from ribs import build_all_ribs
from spar import build_single_spar


def generate_assembly(params):
    """
    Generate the wing assembly using parameters passed from the GUI.
    """
    try:
        EXPORT_PATH = params["EXPORT_PATH"]
        EXPORT_SINGLE_PARTS = params["EXPORT_SINGLE_PARTS"]
        os.makedirs(EXPORT_PATH, exist_ok=True)

        wing = build_wing_shell(params)
        ribs = build_all_ribs(params)
        spar = build_single_spar(**params)
        # ... rest as before ...
    except Exception as e:
        # rilancia per la GUI
        raise

    asm = cq.Assembly()
    asm.add(wing, name="WingShell", color=cq.Color(1, 1, 0, 0.3))
    asm.add(ribs, name="Ribs", color=cq.Color(0, 0, 1))
    asm.add(spar, name="Spar", color=cq.Color(0, 0, 0))

    asm.export(os.path.join(EXPORT_PATH, "wing_assembly.step"), exportType="STEP")

    if EXPORT_SINGLE_PARTS:
        wing.export(os.path.join(EXPORT_PATH, "wing.step"))
        ribs.export(os.path.join(EXPORT_PATH, "ribs.step"))
        spar.export(os.path.join(EXPORT_PATH, "spar.step"))

    print(f"✅ Assembly exported to {EXPORT_PATH}")

