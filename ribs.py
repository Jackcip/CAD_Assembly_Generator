import cadquery as cq
from wing import generate_naca_points

def build_rib(params):
    chord = params["CHORD"]
    t = params["RIB_THICKNESS"]
    spar_d = params["SPAR_OUTER_DIAMETER"]
    spar_x_rel = params["SPAR_X_RELATIVE"]
    spar_center_height = params["SPAR_CENTER_HEIGHT"]
    spar_shape = params["SPAR_SHAPE"]
    naca = params["NACA_PROFILE"]
    num_points = params["NUM_POINTS_PER_SURFACE"]

    airfoil_points = generate_naca_points(naca, num_points, chord)
    profile = cq.Workplane("XY").polyline(airfoil_points).close()
    rib = profile.extrude(t)

    hole_x = spar_x_rel * chord
    # safety checks
    if not (0.0 <= hole_x <= chord):
        raise ValueError("Spar hole x-position is outside chord range.")
    if spar_d <= 0:
        raise ValueError("Spar diameter/size must be > 0.")
    if spar_d > chord * 0.9:
        raise ValueError("Spar diameter/size is unreasonably large relative to chord.")

    # define workplane
    wp = rib.faces(">Z").workplane().moveTo(hole_x, spar_center_height)

    # add hole
    if spar_shape == "circular":
        rib = wp.hole(spar_d)
    elif spar_shape == "square":
        rib = wp.rect(spar_d, spar_d, centered=True).cutThruAll()
    else:
        raise ValueError("Spar shape must be 'circular' or 'square'.")

    return rib


def build_all_ribs(params):
    ribs = cq.Assembly()
    span = params["SPAN"]
    rib_positions = params["RIB_POSITIONS"]

    for i, rel_pos in enumerate(rib_positions):
        pos_z = rel_pos * span
        rib = build_rib(params)
        rib = rib.translate((0, 0, pos_z))
        ribs.add(rib, name=f"Rib_{i}", color=cq.Color(0, 0, 1, 1))
    return ribs
