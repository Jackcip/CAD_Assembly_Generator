import cadquery as cq


def build_single_spar(shape, outer_d, wall_thk, x_rel, center_h, length, chord):
    if outer_d <= 0:
        raise ValueError("outer_d must be > 0")
    if wall_thk < 0:
        raise ValueError("wall_thickness must be >= 0")

    if shape.lower() == "circular":
        outer = cq.Workplane("XY").circle(outer_d / 2)
        inner_radius = (outer_d / 2) - wall_thk

        if inner_radius <= 0:
            raise ValueError("Spar inner radius <= 0")

        inner = cq.Workplane("XY").circle(inner_radius)
        spar = outer.extrude(length).cut(inner.extrude(length))

        return spar.translate((float(x_rel * chord), center_h, 0))

    elif shape.lower() == "square":
        outer = cq.Workplane("XY").rect(outer_d, outer_d)
        inner_side = outer_d - 2 * wall_thk

        if inner_side <= 0:
            raise ValueError("Spar inner side <= 0")

        inner = cq.Workplane("XY").rect(inner_side, inner_side)
        spar = outer.extrude(length).cut(inner.extrude(length))

        return spar.translate((float(x_rel * chord), center_h, 0))

    else:
        raise ValueError("Shape must be 'circular' or 'square'.")


def build_spars(params):
    span = params["SPAN"]
    chord = params["CHORD"]
    protrusion = 80.0

    main_length = span + (protrusion)
    main_spar = build_single_spar(
        params["SPAR_SHAPE"],
        params["SPAR_OUTER_DIAMETER"],
        params["SPAR_WALL_THICKNESS"],
        params["SPAR_X_RELATIVE"],
        params["SPAR_CENTER_HEIGHT"],
        params["RIB_THICKNESS"],
        main_length,
        chord,
    )
    main_spar = main_spar.translate((0, 0, -protrusion))
    spars = [main_spar]

    if params.get("SPAR2_ENABLE", False):
        rib_positions = sorted(params["RIB_POSITIONS"])
        end_rib = params.get("SPAR2_END_RIB", len(rib_positions))
        end_rib_idx = max(1, min(end_rib, len(rib_positions))) - 1

        spar2_span = span * rib_positions[end_rib_idx] + params["RIB_THICKNESS"]
        spar2_length = spar2_span + (protrusion)

        spar2 = build_single_spar(
            params.get("SPAR2_SHAPE", "circular"),
            params.get("SPAR2_OUTER_DIAMETER", 0),
            params.get("SPAR2_WALL_THICKNESS", 0),
            params.get("SPAR2_X_RELATIVE", 0),
            params.get("SPAR2_CENTER_HEIGHT", 0),
            spar2_length,
            chord,
        )
        spar2 = spar2.translate((0, 0, -protrusion))
        spars.append(spar2)

    all_spars = spars[0]
    for s in spars[1:]:
        all_spars = all_spars.union(s)

    return all_spars


def spar_mass(spar_part, density):
    VOLUME_TO_M3 = 1e-9
    volume_mm3 = spar_part.val().Volume()
    mass_kg = volume_mm3 * VOLUME_TO_M3 * density
    return mass_kg
