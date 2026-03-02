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
    spar2_enable = params["SPAR2_ENABLE"]

    spar2_shape = params.get("SPAR2_SHAPE", "circular")
    spar2_d = params.get("SPAR2_OUTER_DIAMETER", 0)
    spar2_x_rel = params.get("SPAR2_X_RELATIVE", 0)
    spar2_h = params.get("SPAR2_CENTER_HEIGHT", 0)

    points = generate_naca_points(naca, num_points, chord)
    profile = cq.Workplane("XY").polyline(points).close()
    rib1 = profile.extrude(t)

    hole_x = spar_x_rel * chord

    # Safety checks
    if not (0.0 <= hole_x <= chord):
        raise ValueError("Spar hole x-position is outside chord range.")
    if spar_d <= 0:
        raise ValueError("Spar diameter/size must be > 0.")
    if spar_d > chord * 0.9:
        raise ValueError("Spar diameter/size is unreasonably large relative to chord.")

    # Add first hole
    wp1 = rib1.faces(">Z").workplane().moveTo(hole_x, spar_center_height)

    if spar_shape == "circular":
        rib1 = wp1.hole(spar_d)
    elif spar_shape == "square":
        rib1 = wp1.rect(spar_d, spar_d, centered=True).cutThruAll()
    else:
        raise ValueError("Spar shape must be 'circular' or 'square'.")

    # Add second hole if enabled
    if spar2_enable:
        hole2_x = spar2_x_rel * chord
        wp2 = rib1.faces(">Z").workplane().moveTo(hole2_x, spar2_h)

        if spar2_shape == "circular":
            rib2 = wp2.hole(spar2_d)
        elif spar2_shape == "square":
            rib2 = wp2.rect(spar2_d, spar2_d, centered=True).cutThruAll()
        else:
            raise ValueError("Spar 2 shape must be 'circular' or 'square'.")

        # Return tuple: (rib with 2 holes, rib with 1 hole)
        return rib2, rib1

    # Return tuple: (rib with 1 hole, None)
    return rib1, None


def build_all_ribs(params):
    span = params["SPAN"]
    rib_positions = params["RIB_POSITIONS"]
    t = params["RIB_THICKNESS"]
    spar2_enable = params["SPAR2_ENABLE"]
    spar2_end = params.get("SPAR2_END_RIB", len(rib_positions))

    rib_positions = sorted(rib_positions)

    if not rib_positions:
        return cq.Workplane("XY")

    # Unpack the returned solids
    rib_2_holes, rib_1_hole = build_rib(params)
    ribs = []

    # Iterate cleanly through all ribs
    for i, rel_pos in enumerate(rib_positions):
        # Use the 2-hole rib up to spar2_end index, otherwise use 1-hole rib
        if spar2_enable and i < spar2_end:
            rib_copy = rib_2_holes.val().copy()
        else:
            rib_copy = rib_1_hole.val().copy()

        wp = cq.Workplane("XY").newObject([rib_copy])

        # Adjust position for the last rib to keep it inside the span
        if rel_pos == 1:
            wp = wp.translate((0, 0, (rel_pos * span) - t))
        else:
            wp = wp.translate((0, 0, rel_pos * span))

        ribs.append(wp)

    if not ribs:
        return cq.Workplane("XY")

    # Union all objects
    all_ribs = ribs[0]
    for r in ribs[1:]:
        all_ribs = all_ribs.union(r)

    return all_ribs


def ribs_mass(rib_part, density):
    # Conversion from mm³ to m³ (1 mm³ = 1e-9 m³)
    VOLUME_TO_M3 = 1e-9

    volume_mm3 = rib_part.val().Volume()
    mass_kg = volume_mm3 * VOLUME_TO_M3 * density

    return mass_kg
