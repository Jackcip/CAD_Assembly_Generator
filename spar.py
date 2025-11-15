import cadquery as cq

def build_single_spar(SPAR_SHAPE, SPAR_OUTER_DIAMETER, SPAR_WALL_THICKNESS, SPAR_X_RELATIVE, SPAN, CHORD, **kwargs):
    """Create a spar; validate inner radius before cutting."""
    
    if SPAR_OUTER_DIAMETER <= 0:
        raise ValueError("outer_d must be > 0")
    
    if SPAR_WALL_THICKNESS < 0:
        raise ValueError("wall_thickness must be >= 0")
    
# check spar shape
    if SPAR_SHAPE.lower() == "circular":
        # create outer circle and define inner radius
        outer = cq.Workplane("XY").circle(SPAR_OUTER_DIAMETER / 2)
        inner_radius = (SPAR_OUTER_DIAMETER / 2) - SPAR_WALL_THICKNESS
        
        if inner_radius <= 0:
            raise ValueError("Spar inner radius <= 0 (outer_d too small or wall_thk too large).")
        # create inner circle and extrude
        inner = cq.Workplane("XY").circle(inner_radius)
        spar=outer.extrude(SPAN).cut(inner.extrude(SPAN))
        spar_traslated = spar.translate((float(SPAR_X_RELATIVE*CHORD), 0, 0))
        return spar_traslated

    elif SPAR_SHAPE.lower() == "square":
        outer = cq.Workplane("XY").rect(SPAR_OUTER_DIAMETER, SPAR_OUTER_DIAMETER)
        inner_side = SPAR_OUTER_DIAMETER - 2 * SPAR_WALL_THICKNESS
        
        if inner_side <= 0:
            raise ValueError("Spar inner side <= 0 (outer_d too small or wall_thk too large).")
        
        inner = cq.Workplane("XY").rect(inner_side, inner_side)
        spar=outer.extrude(SPAN).cut(inner.extrude(SPAN))
        spar_traslated = spar.translate(SPAR_X_RELATIVE*CHORD, 0, 0)
        return spar_traslated

    else:
        raise ValueError("SPAR_SHAPE must be 'circular' or 'square'.")

def spar_mass(spar_part, density):

    #Spar mass calculation with density (kg/m³).
    #Conversion from mm³ to m³: (1 mm³ = 1e-9 m³)
    VOLUME_TO_M3 = 1e-9
    
    volume_mm3 = spar_part.val().Volume()
    mass_kg = volume_mm3 * VOLUME_TO_M3 * density
    
    return mass_kg