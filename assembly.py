import os
import cadquery as cq
from wing import build_wing_shell, wing_mass
from ribs import build_all_ribs, ribs_mass
from spar import build_single_spar, spar_mass

def generate_assembly(params):

    #Generate the wing assembly and calculate mass properties

    try:
        EXPORT_PATH = params["EXPORT_PATH"]
        EXPORT_SINGLE_PARTS = params["EXPORT_SINGLE_PARTS"]
        RIB_COUNT =  params["RIB_COUNT"]
        
        WING_DENSITY = params["WING_DENSITY"]
        RIBS_DENSITY = params["RIBS_DENSITY"]
        SPAR_DENSITY = params["SPAR_DENSITY"]
        
        os.makedirs(EXPORT_PATH, exist_ok=True)

        wing = build_wing_shell(params)
        ribs = build_all_ribs(params)
        spar = build_single_spar(**params)

        #Double "*" calls every parameter needed to build the spar assembly
        
    except Exception as e:
        
        raise

    #mass calculation with mass functions from each file
    mass_wing_kg = wing_mass(wing, WING_DENSITY)
    mass_ribs_kg = ribs_mass(ribs, RIBS_DENSITY)
    mass_spar_kg = spar_mass(spar, SPAR_DENSITY)
    
    total_mass_kg = mass_wing_kg + mass_ribs_kg*RIB_COUNT + mass_spar_kg

    asm = cq.Assembly()
    asm.add(wing, name="WingShell", color=cq.Color(1, 1, 0, 0.3))
    asm.add(ribs, name="Ribs", color=cq.Color(0, 0, 1))
    asm.add(spar, name="Spar", color=cq.Color(0, 0, 0))

    asm.export(os.path.join(EXPORT_PATH, "wing_assembly.step"), exportType="STEP")

    if EXPORT_SINGLE_PARTS:
        wing.export(os.path.join(EXPORT_PATH, "wing.step"))
        ribs.export(os.path.join(EXPORT_PATH, "ribs.step"))
        spar.export(os.path.join(EXPORT_PATH, "spar.step"))

    return total_mass_kg