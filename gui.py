import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkbootstrap import Style
import assembly
import os
import sys
import traceback
import threading

rib_entries = []


# Directory browse handler
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_export_path.delete(0, tk.END)
        entry_export_path.insert(0, folder)


# Rib layout handler
def update_rib_positions():
    try:
        count = int(spin_rib_count.get())
    except ValueError:
        return
    for widget in rib_positions_inner.winfo_children():
        widget.destroy()
    rib_entries.clear()
    for i in range(count):
        ttk.Label(rib_positions_inner, text=f"{i + 1}. Pos (0–1):").grid(
            row=i, column=0, sticky="e", padx=5, pady=2
        )
        e = ttk.Entry(rib_positions_inner, width=8, justify="right")
        e.insert(0, f"{(i + 1) / (count + 1):.2f}")
        e.grid(row=i, column=1, padx=5, pady=2)
        rib_entries.append(e)
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))


def configure_scroll_region(event=None):
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))


def on_canvas_configure(event):
    rib_canvas.itemconfig("inner_frame", width=event.width)


def update_unit_label(event, combo, label):
    if combo.get() == "Density":
        label.config(text="kg/m³")
    else:
        label.config(text="kg")


# Fetch and validate parameters
def build_params():
    naca = str(entry_naca.get().strip())
    span = float(entry_span.get())
    wall = float(entry_wall.get())
    chord_entry = float(entry_chord.get())
    chord = chord_entry - 2.0 * wall
    num_points = int(entry_points.get())
    export_path = entry_export_path.get().strip()

    spar_shape = combo_spar_shape.get()
    spar_d = float(entry_spar_diam.get())
    spar_thk = float(entry_spar_thick.get())
    spar_x_rel = float(entry_spar_x.get())
    spar_h = float(entry_spar_h.get())

    spar2_enabled = spar2_var.get()
    if spar2_enabled:
        spar2_shape = combo_spar2_shape.get()
        spar2_d = float(entry_spar2_diam.get())
        spar2_thk = float(entry_spar2_thick.get())
        spar2_x_rel = float(entry_spar2_x.get())
        spar2_h = float(entry_spar2_h.get())
        spar2_end_rib = int(entry_spar2_end_rib.get())
    else:
        spar2_shape = "circular"
        spar2_d = 0.0
        spar2_thk = 0.0
        spar2_x_rel = 0.0
        spar2_h = 0.0
        spar2_end_rib = 0

    rib_thk = float(entry_rib_thickness.get())
    rib_count = int(spin_rib_count.get())
    rib_positions = [float(e.get()) for e in rib_entries]
    export_parts_flag = export_switch.instate(["selected"])

    wing_mass_type = combo_wing_type.get()
    wing_mass_val = float(entry_wing_val.get())
    spar_mass_type = combo_spar_type.get()
    spar_mass_val = float(entry_spar_val.get())
    ribs_mass_type = combo_ribs_type.get()
    ribs_mass_val = float(entry_ribs_val.get())

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

    if spar2_enabled:
        if spar2_d <= 0:
            raise ValueError("Second spar outer diameter must be positive.")
        if spar2_thk < 0:
            raise ValueError("Second spar wall thickness must be >= 0.")
        if spar2_thk * 2 >= spar2_d:
            raise ValueError("Second spar wall thickness too large. Inner radius <= 0.")
        if not (0.0 <= spar2_x_rel <= 1.0):
            raise ValueError("Second spar X relative position must be between 0 and 1.")
        if not (1 <= spar2_end_rib <= rib_count):
            raise ValueError(
                "Second spar end rib index must be between 1 and the total rib count."
            )

    if not os.path.isdir(os.path.dirname(export_path)) and export_path != "":
        raise ValueError("Export path folder does not exist.")
    if len(rib_positions) != rib_count:
        raise ValueError("Rib count doesn't match number of position entries.")
    for p in rib_positions:
        if not (0.0 <= p <= 1.0):
            raise ValueError("Each rib position must be between 0 and 1.")

    return {
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
        "SPAR2_ENABLE": spar2_enabled,
        "SPAR2_SHAPE": spar2_shape,
        "SPAR2_OUTER_DIAMETER": spar2_d,
        "SPAR2_WALL_THICKNESS": spar2_thk,
        "SPAR2_X_RELATIVE": spar2_x_rel,
        "SPAR2_CENTER_HEIGHT": spar2_h,
        "SPAR2_END_RIB": spar2_end_rib,
        "RIB_THICKNESS": rib_thk,
        "RIB_COUNT": rib_count,
        "RIB_POSITIONS": rib_positions,
        "NUM_POINTS_PER_SURFACE": num_points,
        "EXPORT_SINGLE_PARTS": export_parts_flag,
        "WING_MASS_TYPE": wing_mass_type,
        "WING_MASS_VAL": wing_mass_val,
        "SPAR_MASS_TYPE": spar_mass_type,
        "SPAR_MASS_VAL": spar_mass_val,
        "RIBS_MASS_TYPE": ribs_mass_type,
        "RIBS_MASS_VAL": ribs_mass_val,
    }


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def toggle_spar2():
    state = "normal" if spar2_var.get() else "disabled"
    state_readonly = "readonly" if spar2_var.get() else "disabled"
    combo_spar2_shape.config(state=state_readonly)
    entry_spar2_diam.config(state=state)
    entry_spar2_thick.config(state=state)
    entry_spar2_x.config(state=state)
    entry_spar2_h.config(state=state)
    entry_spar2_end_rib.config(state=state)


# Main window setup
style = Style("flatly")
root = style.master
root.title("CAD Wing Assembly Generator")
root.geometry("1000x850")
root.minsize(950, 750)
root.resizable(True, True)

canvas = tk.Canvas(root)
scroll_y = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
main_frame = ttk.Frame(canvas)

main_frame.bind(
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=main_frame, anchor="nw")
canvas.configure(yscrollcommand=scroll_y.set)
canvas.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=0)
main_frame.columnconfigure(2, weight=1)

main_frame.rowconfigure(0, weight=0)
main_frame.rowconfigure(1, weight=1)
main_frame.rowconfigure(2, weight=1)
main_frame.rowconfigure(3, weight=1)

title = ttk.Label(
    main_frame, text="CAD Wing Assembly Generator", font=("Segoe UI", 16, "bold")
)
title.grid(row=0, column=0, columnspan=3, pady=15)

# General Parameters
general_frame = ttk.LabelFrame(main_frame, text="General Parameters", padding=15)
general_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
general_frame.columnconfigure(1, weight=1)


def add_row(frame, label, default, row, unit=None):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=4)
    e = ttk.Entry(frame, width=12, justify="right")
    e.insert(0, default)
    e.grid(row=row, column=1, padx=5, pady=4, sticky="ew")
    if unit:
        ttk.Label(frame, text=unit, foreground="#888888").grid(
            row=row, column=2, sticky="w", padx=(0, 5)
        )
    return e


entry_naca = add_row(general_frame, "NACA Code:", "2412", 0)
entry_span = add_row(general_frame, "Wing Span:", "1320", 1, "mm")
entry_chord = add_row(general_frame, "Chord Length:", "350", 2, "mm")
entry_wall = add_row(general_frame, "Wall Thickness:", "0.45", 3, "mm")
entry_points = add_row(general_frame, "Num. Points/Surface:", "100", 4)

# Main Spar Parameters
spar_frame = ttk.LabelFrame(main_frame, text="Main Spar Parameters", padding=15)
spar_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
spar_frame.columnconfigure(1, weight=1)

ttk.Label(spar_frame, text="Shape:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
combo_spar_shape = ttk.Combobox(
    spar_frame,
    values=["circular", "square"],
    state="readonly",
    width=10,
    justify="right",
)
combo_spar_shape.current(0)
combo_spar_shape.grid(row=0, column=1, padx=5, pady=4, sticky="w")

entry_spar_diam = add_row(spar_frame, "Outer Diameter:", "30.0", 1, "mm")
entry_spar_thick = add_row(spar_frame, "Wall Thickness:", "0.875", 2, "mm")
entry_spar_x = add_row(spar_frame, "X Relative Pos.:", "0.15", 3)
entry_spar_h = add_row(spar_frame, "Center Height:", "4.5", 4, "mm")

# Second Spar Parameters
spar2_frame = ttk.LabelFrame(main_frame, text="Second Spar Parameters", padding=15)
spar2_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
spar2_frame.columnconfigure(1, weight=1)

spar2_var = tk.BooleanVar(value=False)
chk_spar2 = ttk.Checkbutton(
    spar2_frame,
    text="Enable Second Spar",
    variable=spar2_var,
    command=toggle_spar2,
    bootstyle="round-toggle",
)
chk_spar2.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

ttk.Label(spar2_frame, text="Shape:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
combo_spar2_shape = ttk.Combobox(
    spar2_frame,
    values=["circular", "square"],
    state="disabled",
    width=10,
    justify="right",
)
combo_spar2_shape.current(0)
combo_spar2_shape.grid(row=1, column=1, padx=5, pady=4, sticky="w")

entry_spar2_diam = add_row(spar2_frame, "Outer Diameter:", "20.0", 2, "mm")
entry_spar2_thick = add_row(spar2_frame, "Wall Thickness:", "0.875", 3, "mm")
entry_spar2_x = add_row(spar2_frame, "X Relative Pos.:", "0.65", 4)
entry_spar2_h = add_row(spar2_frame, "Center Height:", "1.5", 5, "mm")
entry_spar2_end_rib = add_row(spar2_frame, "End Rib Index:", "4", 6)

toggle_spar2()

# Separator
sep_vert = ttk.Separator(main_frame, orient="vertical")
sep_vert.grid(row=1, column=1, rowspan=3, sticky="ns", padx=10, pady=10)

# Rib Parameters
rib_frame = ttk.LabelFrame(main_frame, text="Rib Parameters", padding=15)
rib_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=5)
rib_frame.columnconfigure(1, weight=1)
rib_frame.columnconfigure(0, weight=0)
rib_frame.rowconfigure(0, weight=1)

left_rib_frame = ttk.Frame(rib_frame)
left_rib_frame.grid(row=0, column=0, sticky="n", padx=(0, 10), pady=10)

entry_rib_thickness = add_row(left_rib_frame, "Thickness:", "0.45", 0, "mm")

ttk.Label(left_rib_frame, text="Rib Count:").grid(
    row=1, column=0, sticky="e", padx=5, pady=4
)
spin_rib_count = ttk.Spinbox(
    left_rib_frame,
    from_=1,
    to=20,
    width=8,
    justify="right",
    command=update_rib_positions,
)
spin_rib_count.set(11)
spin_rib_count.grid(row=1, column=1, padx=5, pady=4, sticky="w")

right_rib_frame = ttk.LabelFrame(rib_frame, text="Rib Positions (0–1)", padding=5)
right_rib_frame.grid(row=0, column=1, sticky="n", padx=(0, 5))
right_rib_frame.columnconfigure(0, weight=1)
right_rib_frame.rowconfigure(0, weight=1)

rib_scroll_frame = ttk.Frame(right_rib_frame)
rib_scroll_frame.grid(row=0, column=0, sticky="nsew")
rib_scroll_frame.columnconfigure(0, weight=1)
rib_scroll_frame.rowconfigure(0, weight=1)

rib_canvas = tk.Canvas(rib_scroll_frame, width=150, height=150, highlightthickness=0)
rib_scrollbar = ttk.Scrollbar(
    rib_scroll_frame, orient="vertical", command=rib_canvas.yview
)
rib_positions_inner = ttk.Frame(rib_canvas)

rib_canvas.create_window(
    (0, 0), window=rib_positions_inner, anchor="nw", tags="inner_frame"
)
rib_canvas.configure(yscrollcommand=rib_scrollbar.set)

rib_positions_inner.bind("<Configure>", configure_scroll_region)
rib_canvas.bind("<Configure>", on_canvas_configure)

rib_canvas.grid(row=0, column=0, sticky="nsew")
rib_scrollbar.grid(row=0, column=1, sticky="ns", padx=(2, 0))

update_rib_positions()

# Right Bottom Section Layout
right_bottom_frame = ttk.Frame(main_frame)
right_bottom_frame.grid(row=2, column=2, rowspan=2, sticky="nsew", padx=10, pady=5)
right_bottom_frame.columnconfigure(0, weight=1)
right_bottom_frame.columnconfigure(1, weight=1)
right_bottom_frame.rowconfigure(0, weight=1)
right_bottom_frame.rowconfigure(1, weight=1)

# Mass / Density
mass_frame = ttk.LabelFrame(
    right_bottom_frame, text="Mass / Density Parameters", padding=15
)
mass_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10), padx=(0, 5))
for i in range(8):
    mass_frame.columnconfigure(i, weight=1)

ttk.Label(mass_frame, text="Wing:").grid(row=0, column=0, sticky="e", padx=2, pady=4)
combo_wing_type = ttk.Combobox(
    mass_frame, values=["Density", "Mass"], state="readonly", width=8
)
combo_wing_type.current(0)
combo_wing_type.grid(row=0, column=1, sticky="w", padx=2, pady=4)
entry_wing_val = ttk.Entry(mass_frame, width=10, justify="right")
entry_wing_val.insert(0, "1500.00")
entry_wing_val.grid(row=0, column=2, padx=2, pady=4, sticky="w")
lbl_wing_unit = ttk.Label(mass_frame, text="kg/m³", foreground="#888888")
lbl_wing_unit.grid(row=0, column=3, sticky="w", padx=(0, 10))
combo_wing_type.bind(
    "<<ComboboxSelected>>",
    lambda e: update_unit_label(e, combo_wing_type, lbl_wing_unit),
)

ttk.Label(mass_frame, text="Spar:").grid(row=0, column=4, sticky="e", padx=2, pady=4)
combo_spar_type = ttk.Combobox(
    mass_frame, values=["Density", "Mass"], state="readonly", width=8
)
combo_spar_type.current(0)
combo_spar_type.grid(row=0, column=5, sticky="w", padx=2, pady=4)
entry_spar_val = ttk.Entry(mass_frame, width=10, justify="right")
entry_spar_val.insert(0, "1500.00")
entry_spar_val.grid(row=0, column=6, padx=2, pady=4, sticky="w")
lbl_spar_unit = ttk.Label(mass_frame, text="kg/m³", foreground="#888888")
lbl_spar_unit.grid(row=0, column=7, sticky="w", padx=(0, 10))
combo_spar_type.bind(
    "<<ComboboxSelected>>",
    lambda e: update_unit_label(e, combo_spar_type, lbl_spar_unit),
)

ttk.Label(mass_frame, text="Ribs:").grid(row=1, column=0, sticky="e", padx=2, pady=4)
combo_ribs_type = ttk.Combobox(
    mass_frame, values=["Density", "Mass"], state="readonly", width=8
)
combo_ribs_type.current(0)
combo_ribs_type.grid(row=1, column=1, sticky="w", padx=2, pady=4)
entry_ribs_val = ttk.Entry(mass_frame, width=10, justify="right")
entry_ribs_val.insert(0, "1500.00")
entry_ribs_val.grid(row=1, column=2, padx=2, pady=4, sticky="w")
lbl_ribs_unit = ttk.Label(mass_frame, text="kg/m³", foreground="#888888")
lbl_ribs_unit.grid(row=1, column=3, sticky="w", padx=(0, 10))
combo_ribs_type.bind(
    "<<ComboboxSelected>>",
    lambda e: update_unit_label(e, combo_ribs_type, lbl_ribs_unit),
)

# Export Config
export_frame = ttk.LabelFrame(right_bottom_frame, text="Export Data", padding=15)
export_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
export_frame.columnconfigure(1, weight=1)

ttk.Label(export_frame, text="Export Path:").grid(
    row=0, column=0, sticky="e", padx=5, pady=4
)
entry_export_path = ttk.Entry(export_frame, width=20, justify="right")
entry_export_path.insert(0, os.path.join(os.path.expanduser("~"), "Desktop"))
entry_export_path.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
ttk.Button(export_frame, text="Browse", command=browse_folder, width=8).grid(
    row=0, column=2, padx=5, pady=4
)

export_switch = ttk.Checkbutton(
    export_frame, text="Export Single Parts", bootstyle="round-toggle"
)
export_switch.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))

# Results Section
results_frame = ttk.LabelFrame(right_bottom_frame, text="Mass & CG Results", padding=15)
results_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 10), padx=(5, 0))
results_frame.columnconfigure(1, weight=1)
results_frame.columnconfigure(3, weight=1)

ttk.Label(results_frame, text="Total Mass:").grid(
    row=0, column=0, sticky="w", padx=5, pady=2
)
mass_var = tk.StringVar(value="--- kg")
ttk.Label(
    results_frame,
    textvariable=mass_var,
    font=("Segoe UI", 10, "bold"),
    foreground="#000000",
).grid(row=0, column=1, sticky="w", padx=5, pady=2)

ttk.Label(results_frame, text="CG X:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
cg_x_var = tk.StringVar(value="--- mm")
ttk.Label(
    results_frame,
    textvariable=cg_x_var,
    font=("Segoe UI", 10, "bold"),
    foreground="#000000",
).grid(row=0, column=3, sticky="w", padx=5, pady=2)

ttk.Label(results_frame, text="CG Y:").grid(row=1, column=2, sticky="e", padx=5, pady=2)
cg_y_var = tk.StringVar(value="--- mm")
ttk.Label(
    results_frame,
    textvariable=cg_y_var,
    font=("Segoe UI", 10, "bold"),
    foreground="#000000",
).grid(row=1, column=3, sticky="w", padx=5, pady=2)

ttk.Label(results_frame, text="CG Z:").grid(row=2, column=2, sticky="e", padx=5, pady=2)
cg_z_var = tk.StringVar(value="--- mm")
ttk.Label(
    results_frame,
    textvariable=cg_z_var,
    font=("Segoe UI", 10, "bold"),
    foreground="#000000",
).grid(row=2, column=3, sticky="w", padx=5, pady=2)

# Action Section
action_frame = ttk.LabelFrame(right_bottom_frame, text="Action", padding=15)
action_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
action_frame.columnconfigure(0, weight=1)

generate_btn = ttk.Button(
    action_frame,
    text="Generate Assembly",
    bootstyle="success",
    command=lambda: start_generation(progress_bar, progress_var),
)
generate_btn.grid(row=0, column=0, sticky="ew", pady=(5, 15))

progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(
    action_frame,
    variable=progress_var,
    mode="determinate",
    maximum=100,
    bootstyle="info-striped",
)
progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

status_label = ttk.Label(action_frame, text="", font=("Segoe UI", 9))
status_label.grid(row=2, column=0, sticky="w")


# Assembly Generation Handler
def start_generation(progress_bar, progress_var):
    try:
        params = build_params()
    except Exception as e:
        messagebox.showerror("Invalid Value", str(e))
        mass_var.set("Invalid")
        cg_x_var.set("---")
        cg_y_var.set("---")
        cg_z_var.set("---")
        return

    generate_btn.config(state="disabled")
    progress_var.set(0)
    progress_bar.config(bootstyle="info", mode="indeterminate")
    progress_bar.start(10)
    status_label.config(text="Generating...", foreground="#0d6efd")
    root.update_idletasks()

    result = {"ok": False, "mass": None, "cg": None, "error": None}

    def worker():
        try:
            mass, cg = assembly.generate_assembly(params)
            result["mass"] = mass
            result["cg"] = cg
            result["ok"] = True
        except Exception as e:
            result["ok"] = False
            result["error"] = traceback.format_exc()
            result["error_msg"] = str(e)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def poll():
        if t.is_alive():
            root.after(100, poll)
            return

        progress_bar.stop()
        progress_bar.config(mode="determinate")
        progress_var.set(100)

        if result["ok"]:
            mass_var.set(f"{result['mass']:,.3f} kg")
            cg_x_var.set(f"{result['cg'][0]:.2f} mm")
            cg_y_var.set(f"{result['cg'][1]:.2f} mm")
            cg_z_var.set(f"{result['cg'][2]:.2f} mm")

            progress_bar.config(bootstyle="success")
            status_label.config(
                text="✔ Assembly generated successfully!", foreground="#198754"
            )
            messagebox.showinfo("Done", "Assembly successfully generated!")
        else:
            mass_var.set("Error kg")
            cg_x_var.set("Error mm")
            cg_y_var.set("Error mm")
            cg_z_var.set("Error mm")

            progress_bar.config(bootstyle="danger")
            status_label.config(text="✖ Assembly failed.", foreground="#dc3545")
            messagebox.showerror(
                "Assembly Error",
                f"{result['error_msg']}\n\nTraceback:\n{result['error']}",
            )

        generate_btn.config(state="normal")
        root.after(4000, lambda: status_label.config(text=""))

    root.after(100, poll)


# Global mouse wheel scroll event
def on_mousewheel(event):
    widget = root.winfo_containing(event.x_root, event.y_root)
    if not widget:
        return

    target_canvas = canvas
    curr = widget

    # Check if mouse is over the rib canvas
    while curr:
        if curr == rib_canvas:
            target_canvas = rib_canvas
            break
        curr = curr.master

    # Determine scroll delta (OS dependent)
    if event.num == 4:
        delta = -1
    elif event.num == 5:
        delta = 1
    elif sys.platform == "darwin":
        delta = -1 if event.delta > 0 else 1
    else:
        delta = int(-1 * (event.delta / 120))

    target_canvas.yview_scroll(delta, "units")


# Bind mouse wheel to the application root
root.bind_all("<MouseWheel>", on_mousewheel)
root.bind_all("<Button-4>", on_mousewheel)  # Linux scroll up
root.bind_all("<Button-5>", on_mousewheel)  # Linux scroll down

root.mainloop()
