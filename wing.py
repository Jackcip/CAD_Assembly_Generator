import cadquery as cq
import numpy as np

def generate_naca_points(code, n_points, chord):
    # NACA 4-digit parameters
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0

    # Cosine spacing for better LE resolution
    beta = np.linspace(0, np.pi, n_points)
    x = 0.5 * (1 - np.cos(beta))

    # Thickness distribution
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)

    # Camber line and gradient
    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)
    
    if p > 0:
        idx1 = x <= p
        idx2 = x > p
        yc[idx1] = (m / p**2) * (2 * p * x[idx1] - x[idx1]**2)
        yc[idx2] = (m / (1 - p)**2) * ((1 - 2 * p) + 2 * p * x[idx2] - x[idx2]**2)
        dyc_dx[idx1] = (2 * m / p**2) * (p - x[idx1])
        dyc_dx[idx2] = (2 * m / (1 - p)**2) * (p - x[idx2])

    theta = np.arctan(dyc_dx)

    # Surface coordinates
    xu, yu = x - yt * np.sin(theta), yc + yt * np.cos(theta)
    xl, yl = x + yt * np.sin(theta), yc - yt * np.cos(theta)

    # Combine into single profile
    upper = np.column_stack((xu, yu)) * chord
    lower = np.column_stack((xl, yl)) * chord
    
    # Close the profile correctly (leading edge to trailing edge)
    return list(upper) + list(lower[::-1])[1:]

def build_wing_shell(params):
    chord = params["CHORD"]
    span = params["SPAN"]
    wall_thickness = params["WALL_THICKNESS"]
    
    points = generate_naca_points(params["NACA_PROFILE"], params["NUM_POINTS_PER_SURFACE"], chord)
    
    # Create the base profile wire
    profile = cq.Workplane("XY").polyline(points).close()
    
    # Create shell using offset2D
    inner_wire = profile
    # Extrude both and subtract
    inner_vol = inner_wire.extrude(span)
    return inner_vol.faces("|Z").shell(wall_thickness)

def get_wing_mass(wing_obj, density_kg_m3):
    # Convert mm3 to m3
    volume_m3 = wing_obj.val().Volume() * 1e-9
    return volume_m3 * density_kg_m3
