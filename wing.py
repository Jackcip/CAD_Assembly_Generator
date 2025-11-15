import cadquery as cq
import numpy as np

def generate_naca_points(code: str, n_points_per_surface: int, chord: float):
    """
    2D Profile generator (simmetrico o non simmetrico)
    """
    # retrieving airfoil info from NACA code
    m = int(code[0]) / 100.0  # max camber
    p = int(code[1]) / 10.0   # max camber position
    t = int(code[2:]) / 100.0 # max relative thickness

    # chord-wise panelization (cosine law)
    beta = np.linspace(0, np.pi, n_points_per_surface + 1)
    x = 0.5 * (1 - np.cos(beta))  # more density near leading edge

    # thickness law
    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    # mid line and derivative dyc/dx
    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if p != 0:  # asymmetrical profile
        for i, xi in enumerate(x):
            if xi < p:
                yc[i] = (m / p**2) * (2 * p * xi - xi**2)
                dyc_dx[i] = (2 * m / p**2) * (p - xi)
            else:
                yc[i] = (m / (1 - p)**2) * ((1 - 2 * p) + 2 * p * xi - xi**2)
                dyc_dx[i] = (2 * m / (1 - p)**2) * (p - xi)

    # angle of attack (WRT mid line)
    theta = np.arctan(dyc_dx)

    # upper and lower surfaces coordinates
    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # joining surfaces
    upper_surface = np.column_stack((xu * chord, yu * chord))
    lower_surface = np.column_stack((xl * chord, yl * chord))
    lower_surface[-1] = np.array([chord, 0.0])
    upper_surface = upper_surface[:-1]

    airfoil_points = np.vstack((upper_surface, lower_surface[::-1]))

    return airfoil_points

# solid creation

def build_wing_shell(params):
    chord = params["CHORD"]
    span = params["SPAN"]
    wall_thickness = params["WALL_THICKNESS"]
    naca = params["NACA_PROFILE"]
    num_points = params["NUM_POINTS_PER_SURFACE"]

    outer_points = generate_naca_points(naca, num_points, chord)
    outer_profile = cq.Workplane("XY").polyline(outer_points).close()
    outer_solid = outer_profile.extrude(span)
    hollow_wing = outer_solid.faces("<Z").shell(wall_thickness, kind="intersection")
    return hollow_wing

def wing_mass(wing_shell, density):

    #Wing mass calculation with density (kg/m³).
    #Conversion from mm³ to m³: (1 mm³ = 1e-9 m³)
    VOLUME_TO_M3 = 1e-9
    
    volume_mm3 = wing_shell.val().Volume()
    mass_kg = volume_mm3 * VOLUME_TO_M3 * density
    
    return mass_kg
