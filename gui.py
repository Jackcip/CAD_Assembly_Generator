import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkbootstrap import Style
import assembly
import os
import sys
import traceback
import threading

# ============================
#   FUNCTIONS
# ============================

rib_entries = []

def browse_folder():
    """Open folder selection dialog for export path."""
    folder = filedialog.askdirectory()
    if folder:
        entry_export_path.delete(0, tk.END)
        entry_export_path.insert(0, folder)

def update_rib_positions():
    """Update the list of rib position input boxes based on rib count."""
    try:
        count = int(spin_rib_count.get())
    except ValueError:
        return
    for widget in rib_positions_inner.winfo_children():
        widget.destroy()
    rib_entries.clear()
    for i in range(count):
        ttk.Label(rib_positions_inner, text=f"{i+1}. Pos (0–1):").grid(row=i, column=0, sticky="e", padx=5, pady=2)
        e = ttk.Entry(rib_positions_inner, width=8, justify="right")
        e.insert(0, f"{(i+1)/(count+1):.2f}")
        e.grid(row=i, column=1, padx=5, pady=2)
        rib_entries.append(e)
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))

def configure_scroll_region(event=None):
    """Adjust scroll region when the inner frame size changes."""
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))

def on_canvas_configure(event):
    """Ensure the inner frame width matches the canvas width."""
    rib_canvas.itemconfig("inner_frame", width=event.width)

def confirm_inputs():
    """Validate inputs, build parameter dictionary, and generate the assembly.
    Returns True on success, False on failure (shows messageboxes for details)."""
    try:
        naca = str(entry_naca.get().strip())
        span = float(entry_span.get())
        wall = float(entry_wall.get())
        chord_entry = float(entry_chord.get())
        chord = chord_entry - 2.0 * wall
        num_points = int(entry_points.get())
        export_path = entry_export_path.get().strip()
        wing_density = float(entry_density_wing.get())

        spar_shape = combo_spar_shape.get()
        spar_d = float(entry_spar_diam.get())
        spar_thk = float(entry_spar_thick.get())
        spar_x_rel = float(entry_spar_x.get())
        spar_h = float(entry_spar_h.get())
        spar_density = float(entry_density_spar.get())

        rib_thk = float(entry_rib_thickness.get())
        rib_count = int(spin_rib_count.get())
        rib_positions = [float(e.get()) for e in rib_entries]
        rib_density = float(entry_density_ribs.get())
        export_parts_flag = export_switch.instate(['selected'])

        # --- Input validation ---
        if chord <= 0:
            raise ValueError("Computed chord <= 0. Check chord length and wall thickness.")
        if num_points < 4:
            raise ValueError("Num. Points per surface must be >= 4.")
        if not (naca.isdigit() and len(naca) == 4):
            raise ValueError("NACA code must be 4 digits, e.g. 2412.")
        if spar_d <= 0:
            raise ValueError("Spar outer diameter must be positive.")
        if spar_thk < 0:
            raise ValueError("Spar wall thickness must be >= 0.")
        if spar_thk * 2 >= spar_d:
            raise ValueError("Spar wall thickness too large. Inner radius <= 0.")
        if not (0.0 <= spar_x_rel <= 1.0):
            raise ValueError("Spar X relative position must be between 0 and 1.")
        if not os.path.isdir(os.path.dirname(export_path)) and export_path != "":
            raise ValueError("Export path folder does not exist.")
        if len(rib_positions) != rib_count:
            raise ValueError("Rib count doesn't match number of position entries.")
        for p in rib_positions:
            if not (0.0 <= p <= 1.0):
                raise ValueError("Each rib position must be between 0 and 1.")
            if p < 0.01 or p > 0.99:
                # Warn about ribs too close to the tips (you can add a warning if desired)
                pass

        # Build parameter dictionary
        params = {
            "NACA_PROFILE": naca,
            "SPAN": span,
            "WALL_THICKNESS": wall,
            "CHORD": chord,
            "EXPORT_PATH": export_path,
            "SPAR_SHAPE": spar_shape,
            "SPAR_OUTER_DIAMETER": spar_d,
            "SPAR_WALL_THICKNESS": spar_thk,
            "SPAR_X_RELATIVE": spar_x_rel,
            "SPAR_CENTER_HEIGHT": spar_h,
            "RIB_THICKNESS": rib_thk,
            "RIB_COUNT": rib_count,
            "RIB_POSITIONS": rib_positions,
            "NUM_POINTS_PER_SURFACE": num_points,
            "EXPORT_SINGLE_PARTS": export_parts_flag,
            "SPAR_DENSITY": spar_density,
            "RIBS_DENSITY": rib_density,
            "WING_DENSITY": wing_density
        }

        # Try to generate the full assembly
        try:
            #mass calculation from the assembly
            total_mass = assembly.generate_assembly(params)
            # success: inform user and return True
            messagebox.showinfo("Done", "Assembly successfully generated!")
            # Variable update in the GUI frame
            mass_var.set(f"{total_mass:,.3f} kg")
            return True
        except Exception as e:
            #throws exception
            tb = traceback.format_exc()
            messagebox.showerror("Assembly Error", f"{e}\n\nTraceback:\n{tb}")
            mass_var.set("Error kg") # Update the error
            return False

    except Exception as e:
        messagebox.showerror("Invalid Value", f"{e}")
        mass_var.set("Invalid kg") # Update the input error
        return False

    except Exception as e:
        messagebox.showerror("Invalid Value", f"{e}")
        return False

# ============================
#   ICON AND RESOURCE PATH
# ============================

def resource_path(relative_path):
    """Get the absolute path for resource files (used for PyInstaller)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# ============================
#   GUI SETUP
# ============================

style = Style("flatly")
root = style.master
root.title("CAD Wing Assembly Generator")
root.geometry("750x650")
root.minsize(850, 600)
root.resizable(True, True)

# App icon setup
try:
    icon_path = resource_path("icon.ico")
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"Unable to load icon: {e}")

# Scrollable container
canvas = tk.Canvas(root)
scroll_y = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
main_frame = ttk.Frame(canvas)

main_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=main_frame, anchor="nw")
canvas.configure(yscrollcommand=scroll_y.set)
canvas.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

main_frame.columnconfigure(0, weight=1)  # General / Spar
main_frame.columnconfigure(1, weight=0)  # Vertical separator
main_frame.columnconfigure(2, weight=1)  # Rib / Density

main_frame.rowconfigure(0, weight=0)  # Title
main_frame.rowconfigure(1, weight=1)  # General + Rib
main_frame.rowconfigure(2, weight=1)  # Spar + Density
main_frame.rowconfigure(3, weight=0)  # Bottom section (button & progress bar)

# ============================
#   LAYOUT
# ============================

title = ttk.Label(main_frame, text="CAD Wing Assembly Generator", font=("Segoe UI", 16, "bold"))
title.grid(row=0, column=0, columnspan=3, pady=15)

# === GENERAL PARAMETERS FRAME ===
general_frame = ttk.LabelFrame(main_frame, text="General Parameters", padding=15)
general_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
general_frame.columnconfigure(1, weight=1)

def add_row(frame, label, default, row, unit=None):
    """Helper function to create labeled entry rows with optional unit labels."""
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=4)
    e = ttk.Entry(frame, width=12, justify="right")
    e.insert(0, default)
    e.grid(row=row, column=1, padx=5, pady=4, sticky="ew")
    if unit:
        ttk.Label(frame, text=unit, foreground="#888888").grid(row=row, column=2, sticky="w", padx=(0, 5))
    return e

entry_naca = add_row(general_frame, "NACA Code:", "2412", 0)
entry_span = add_row(general_frame, "Wing Span:", "1000", 1, "mm")
entry_chord = add_row(general_frame, "Chord Length:", "350", 2, "mm")
entry_wall = add_row(general_frame, "Wall Thickness:", "2.0", 3, "mm")
entry_points = add_row(general_frame, "Num. Points/Surface:", "100", 4)

# === SPAR PARAMETERS FRAME ===
spar_frame = ttk.LabelFrame(main_frame, text="Spar Parameters", padding=15)
spar_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
spar_frame.columnconfigure(1, weight=1)

ttk.Label(spar_frame, text="Shape:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
combo_spar_shape = ttk.Combobox(spar_frame, values=["circular", "square"], state="readonly", width=10, justify="right")
combo_spar_shape.current(0)
combo_spar_shape.grid(row=0, column=1, padx=5, pady=4, sticky="w")

entry_spar_diam = add_row(spar_frame, "Outer Diameter:", "10.0", 1, "mm")
entry_spar_thick = add_row(spar_frame, "Wall Thickness:", "2.0", 2, "mm")
entry_spar_x = add_row(spar_frame, "X Relative Pos.:", "0.25", 3)
entry_spar_h = add_row(spar_frame, "Center Height:", "0.0", 4, "mm")

# Vertical separator
sep_vert = ttk.Separator(main_frame, orient="vertical")
sep_vert.grid(row=1, column=1, rowspan=2, sticky="ns", padx=10, pady=10)

# === RIB PARAMETERS FRAME ===
rib_frame = ttk.LabelFrame(main_frame, text="Rib Parameters", padding=15)
rib_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=5)
rib_frame.columnconfigure(1, weight=1)

rib_frame.columnconfigure(0, weight=0)
rib_frame.columnconfigure(1, weight=0)
rib_frame.rowconfigure(0, weight=1)

# === left column ===
left_rib_frame = ttk.Frame(rib_frame)
left_rib_frame.grid(row=0, column=0, sticky="n", padx=(0, 10), pady= 10)

entry_rib_thickness = add_row(left_rib_frame, "Thickness:", "3.0", 0, "mm")

ttk.Label(left_rib_frame, text="Rib Count:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
spin_rib_count = ttk.Spinbox(left_rib_frame, from_=1, to=20, width=8, justify="right", command=update_rib_positions)
spin_rib_count.set(5)
spin_rib_count.grid(row=1, column=1, padx=5, pady=4, sticky="w")

# === rigth column ===
right_rib_frame = ttk.LabelFrame(rib_frame, text="Rib Positions (0–1)", padding=5)
right_rib_frame.grid(row=0, column=1, sticky="n", padx=(0, 5))
right_rib_frame.columnconfigure(0, weight=1)
right_rib_frame.rowconfigure(0, weight=1)

# canvas and scrollbar
rib_scroll_frame = ttk.Frame(right_rib_frame)
rib_scroll_frame.grid(row=0, column=0, sticky="nsew")
rib_scroll_frame.columnconfigure(0, weight=1)
rib_scroll_frame.rowconfigure(0, weight=1)

rib_canvas = tk.Canvas(rib_scroll_frame, width=150, height=150, highlightthickness=0)
rib_scrollbar = ttk.Scrollbar(rib_scroll_frame, orient="vertical", command=rib_canvas.yview)
rib_positions_inner = ttk.Frame(rib_canvas)

# inner scrollable frame for positions
rib_canvas.create_window((0, 0), window=rib_positions_inner, anchor="nw", tags="inner_frame")
rib_canvas.configure(yscrollcommand=rib_scrollbar.set)

# Binding
rib_positions_inner.bind("<Configure>", configure_scroll_region)
rib_canvas.bind("<Configure>", on_canvas_configure)

rib_canvas.grid(row=0, column=0, sticky="nsew")
rib_scrollbar.grid(row=0, column=1, sticky="ns", padx=(2, 0))

update_rib_positions()

# === RIGHT BOTTOM SECTION (Density + Export) ===
right_bottom_frame = ttk.Frame(main_frame)
right_bottom_frame.grid(row=2, column=2, sticky="nsew", padx=10, pady=5)
right_bottom_frame.columnconfigure(0, weight=1)
right_bottom_frame.rowconfigure(0, weight=1)
right_bottom_frame.rowconfigure(1, weight=0)

# === DENSITY PARAMETERS ===
density_frame = ttk.LabelFrame(right_bottom_frame, text="Density Parameters", padding=15)
density_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
density_frame.columnconfigure(0, weight=1)
density_frame.columnconfigure(1, weight=1)
density_frame.columnconfigure(2, weight=1)
density_frame.columnconfigure(3, weight=1)
density_frame.columnconfigure(4, weight=1)
density_frame.columnconfigure(5, weight=1)

# Wing density
ttk.Label(density_frame, text="Wing Density:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
entry_density_wing = ttk.Entry(density_frame, width=10, justify="right")
entry_density_wing.insert(0, "1500.00")
entry_density_wing.grid(row=0, column=1, padx=2, pady=4, sticky="w")
ttk.Label(density_frame, text="kg/m³", foreground="#888888").grid(row=0, column=2, sticky="w", padx=(0, 10))

# Spar density
ttk.Label(density_frame, text="Spar Density:").grid(row=0, column=3, sticky="e", padx=5, pady=4)
entry_density_spar = ttk.Entry(density_frame, width=10, justify="right")
entry_density_spar.insert(0, "1500.00")
entry_density_spar.grid(row=0, column=4, padx=2, pady=4, sticky="w")
ttk.Label(density_frame, text="kg/m³", foreground="#888888").grid(row=0, column=5, sticky="w", padx=(0, 10))

# Ribs density 
ttk.Label(density_frame, text="Ribs Density:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
entry_density_ribs = ttk.Entry(density_frame, width=10, justify="right")
entry_density_ribs.insert(0, "1500.00")
entry_density_ribs.grid(row=1, column=1, padx=2, pady=4, sticky="w")
ttk.Label(density_frame, text="kg/m³", foreground="#888888").grid(row=1, column=2, sticky="w", padx=(0, 10))

# Export data
export_frame = ttk.LabelFrame(right_bottom_frame, text="Export Data", padding=15)
export_frame.grid(row=1, column=0, sticky="nsew")
export_frame.columnconfigure(1, weight=1)

# Assembly total mass
mass_result_frame = ttk.LabelFrame(right_bottom_frame, text="Total Mass Result", padding=15)
mass_result_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
mass_result_frame.columnconfigure(1, weight=1)
ttk.Label(mass_result_frame, text="Assembly Mass:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
mass_var = tk.StringVar(value="--- kg")
mass_label = ttk.Label(mass_result_frame, textvariable=mass_var, font=("Segoe UI", 10, "bold"), foreground="#000000")
mass_label.grid(row=0, column=1, sticky="e", padx=5, pady=4)

# Export Path
ttk.Label(export_frame, text="Export Path:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
entry_export_path = ttk.Entry(export_frame, width=20, justify="right")
entry_export_path.insert(0, "C:/Users/ospite/Desktop")
entry_export_path.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
ttk.Button(export_frame, text="Browse", command=browse_folder, width=8).grid(row=0, column=2, padx=5, pady=4)

# Export Single Parts Switch
export_switch = ttk.Checkbutton(export_frame, text="Export Single Parts", bootstyle="round-toggle")
export_switch.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))

# === BOTTOM CONTROLS (Button + Progress Bar + Status Label) ===
bottom_frame = ttk.Frame(main_frame, padding=10)
bottom_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
bottom_frame.columnconfigure(0, weight=1)  # Status label
bottom_frame.columnconfigure(1, weight=0)  # Button
bottom_frame.columnconfigure(2, weight=0)  # Progress bar

# Status label (on the left side)
status_label = ttk.Label(bottom_frame, text="", font=("Segoe UI", 9))
status_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

# Generate button
generate_btn = ttk.Button(
    bottom_frame,
    text="Generate Assembly",
    bootstyle="success",
    width=20,
    command=lambda: start_generation(progress_bar, progress_var)
)
generate_btn.grid(row=0, column=1, padx=(0, 10), sticky="e")

# Progress bar (always visible)
progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(
    bottom_frame,
    variable=progress_var,
    mode="determinate",
    maximum=100,
    bootstyle="info-striped",
    length=200
)
progress_bar.grid(row=0, column=2, padx=(10, 0), sticky="w")



def start_generation(progress_bar, progress_var):
    # disable UI
    generate_btn.config(state="disabled")

    # reset progress and styles
    progress_var.set(0)
    progress_bar.config(bootstyle="info")   # neutral/blue
    progress_bar.config(mode="indeterminate")
    progress_bar.start(10)  # start indefinite animation
    status_label.config(text="Generating...", foreground="#0d6efd")
    root.update_idletasks()

    result = {"ok": False}

    def worker():
        # call confirm_inputs() which returns True/False
        try:
            ok = confirm_inputs()
            result["ok"] = bool(ok)
        except Exception as e:
            # unexpected exception in worker
            result["ok"] = False
            # optionally log traceback to console
            print("Worker exception:", e)
            traceback.print_exc()

    # start worker thread
    t = threading.Thread(target=worker, daemon=True)
    t.start()

    # poll for thread completion
    def poll():
        if t.is_alive():
            root.after(100, poll)
            return
        # worker finished
        progress_bar.stop()
        progress_bar.config(mode="determinate")
        progress_var.set(100)

        if result["ok"]:
            # success
            progress_bar.config(bootstyle="success")
            status_label.config(text="✔ Assembly generated successfully!", foreground="#198754")
        else:
            # failure
            progress_bar.config(bootstyle="danger")
            status_label.config(text="✖ Assembly failed.", foreground="#dc3545")

        # re-enable button and clear message after a timeout
        generate_btn.config(state="normal")
        root.after(4000, lambda: status_label.config(text=""))

    root.after(100, poll)


# === START APP ===
root.mainloop()