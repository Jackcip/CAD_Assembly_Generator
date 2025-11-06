import cadquery as cq
import numpy as np

def generate_naca_points(code: str, n_points_per_surface: int, chord: float):
    """
    Genera i punti 2D di un profilo NACA a 4 cifre (simmetrico o non simmetrico)
    utilizzando NumPy per calcoli vettoriali.
    """
    # Decodifica il codice NACA
    m = int(code[0]) / 100.0  # camber massimo
    p = int(code[1]) / 10.0   # posizione del camber massimo
    t = int(code[2:]) / 100.0 # spessore relativo massimo

    # Distribuzione dei punti lungo la corda (cosinusoidale)
    beta = np.linspace(0, np.pi, n_points_per_surface + 1)
    x = 0.5 * (1 - np.cos(beta))  # distribuzione più densa vicino al bordo d’attacco

    # Formula dello spessore (valida per tutti i profili NACA a 4 cifre)
    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    # Linea media e derivata dyc/dx
    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if p != 0:  # profilo non simmetrico
        for i, xi in enumerate(x):
            if xi < p:
                yc[i] = (m / p**2) * (2 * p * xi - xi**2)
                dyc_dx[i] = (2 * m / p**2) * (p - xi)
            else:
                yc[i] = (m / (1 - p)**2) * ((1 - 2 * p) + 2 * p * xi - xi**2)
                dyc_dx[i] = (2 * m / (1 - p)**2) * (p - xi)

    # Angolo di inclinazione della linea media
    theta = np.arctan(dyc_dx)

    # Coordinate superficie superiore e inferiore
    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # Combina le due superfici
    upper_surface = np.column_stack((xu * chord, yu * chord))
    lower_surface = np.column_stack((xl * chord, yl * chord))
    lower_surface[-1] = np.array([chord, 0.0])
    upper_surface = upper_surface[:-1]

    airfoil_points = np.vstack((upper_surface, lower_surface[::-1]))

    return airfoil_points



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
