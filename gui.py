import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style, ttk
import assembly   # <-- contiene generate_assembly()
import os

# ============================
#   GUI SETUP
# ============================

style = Style("flatly")
root = style.master
root.title("Assembly Generator")
root.geometry("850x600")
root.resizable(False, True)  # altezza ridimensionabile

# Scroll container principale
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

# ============================
#   FUNZIONI
# ============================

rib_entries = []

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_export_path.delete(0, tk.END)
        entry_export_path.insert(0, folder)

def update_rib_positions():
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

def confirm_inputs():
    import traceback
    try:
        # Leggi valori grezzi
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

        rib_thk = float(entry_rib_thickness.get())
        rib_count = int(spin_rib_count.get())
        rib_positions = [float(e.get()) for e in rib_entries]
        export_parts_flag = export_switch.instate(['selected'])

        # --- VALIDAZIONI ---
        if chord <= 0:
            raise ValueError("Computed chord <= 0. Check chord length and wall thickness.")
        if num_points < 4:
            raise ValueError("Num. Points/Surface must be >= 4.")
        if not (naca.isdigit() and len(naca) == 4):
            raise ValueError("NACA code must be 4 digits, e.g. 2412.")
        if spar_d <= 0:
            raise ValueError("Spar outer diameter must be positive.")
        if spar_thk < 0:
            raise ValueError("Spar wall thickness must be >= 0.")
        if spar_thk*2 >= spar_d:
            raise ValueError("Spar wall thickness too large: inner radius <= 0. Reduce thickness or outer diameter.")
        if not (0.0 <= spar_x_rel <= 1.0):
            raise ValueError("Spar X relative must be between 0 and 1.")
        if not os.path.isdir(os.path.dirname(export_path)) and export_path != "":
            raise ValueError("Export path folder does not exist.")
        if len(rib_positions) != rib_count:
            raise ValueError("Rib count doesn't match number of rib position entries.")
        for p in rib_positions:
            if not (0.0 <= p <= 1.0):
                raise ValueError("Each rib position must be between 0 and 1.")
            if p < 0.01 or p > 0.99:
                # optional: warn about ribs too close to tips
                pass

        # Build params dict
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
            "EXPORT_SINGLE_PARTS": export_parts_flag
        }

        # Conferma all'utente
        messagebox.showinfo("Parameters Loaded", "Parameters validated and loaded!")

        # Chiama assembly con try/except per mostrare errore completo se fallisce
        try:
            assembly.generate_assembly(params)
            messagebox.showinfo("Done", "Assembly successfully generated!")
        except Exception as e:
            tb = traceback.format_exc()
            messagebox.showerror("Assembly error", f"{e}\n\nTraceback:\n{tb}")

    except Exception as e:
        messagebox.showerror("Invalid value", f"{e}")


# ============================
#   LAYOUT
# ============================

title = ttk.Label(main_frame, text="Assembly Generator", font=("Segoe UI", 16, "bold"))
title.grid(row=0, column=0, columnspan=3, pady=10)

# === LEFT COLUMN ===
left_col = ttk.Frame(main_frame, padding=10)
left_col.grid(row=1, column=0, sticky="n")

# === RIGHT COLUMN ===
right_col = ttk.Frame(main_frame, padding=10)
right_col.grid(row=1, column=2, sticky="n")

# Vertical separator
sep_vert = ttk.Separator(main_frame, orient="vertical")
sep_vert.grid(row=1, column=1, sticky="ns", padx=10)

# Helper per righe standard
def add_row(frame, label, default, row, unit=None):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=3)
    e = ttk.Entry(frame, width=10, justify="right")
    e.insert(0, default)
    e.grid(row=row, column=1, padx=5, pady=3)
    if unit:
        ttk.Label(frame, text=unit).grid(row=row, column=2, sticky="w")
    return e

# === GENERAL PARAMETERS ===
ttk.Label(left_col, text="General Parameters", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", columnspan=3)
entry_naca = add_row(left_col, "NACA Code:", "2412", 1)
entry_span = add_row(left_col, "Wing Span:", "1000", 2, "mm")
entry_chord = add_row(left_col, "Chord Length:", "350", 3, "mm")
entry_wall = add_row(left_col, "Wall Thickness:", "2.0", 4, "mm")
entry_points = add_row(left_col, "Num. Points/Surface:", "100", 5)

ttk.Label(left_col, text="Export Path:").grid(row=6, column=0, sticky="e", padx=5, pady=3)
entry_export_path = ttk.Entry(left_col, width=25, justify="right")
entry_export_path.insert(0, "C:/Users/ospite/Desktop")
entry_export_path.grid(row=6, column=1, padx=5, pady=3)
ttk.Button(left_col, text="Browse Folder", command=browse_folder).grid(row=6, column=2, padx=5, pady=3)

# === SPAR PARAMETERS ===
ttk.Separator(left_col, orient="horizontal").grid(row=7, column=0, columnspan=3, sticky="ew", pady=5)
ttk.Label(left_col, text="Spar Parameters", font=("Segoe UI", 11, "bold")).grid(row=8, column=0, sticky="w", columnspan=3)

ttk.Label(left_col, text="Shape:").grid(row=9, column=0, sticky="e", padx=5, pady=3)
combo_spar_shape = ttk.Combobox(left_col, values=["circular", "square"], state="readonly", width=10, justify="right")
combo_spar_shape.current(0)
combo_spar_shape.grid(row=9, column=1, padx=5, pady=3)
entry_spar_diam = add_row(left_col, "Outer Diameter:", "10.0", 10, "mm")
entry_spar_thick = add_row(left_col, "Wall Thickness:", "2.0", 11, "mm")
entry_spar_x = add_row(left_col, "X Relative Pos.:", "0.25", 12)
entry_spar_h = add_row(left_col, "Center Height:", "0.0", 13, "mm")

# === RIB PARAMETERS (scrollable only for positions) ===
ttk.Label(right_col, text="Rib Parameters", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", columnspan=3)
entry_rib_thickness = add_row(right_col, "Thickness:", "3.0", 1, "mm")

ttk.Label(right_col, text="Rib Count:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
spin_rib_count = ttk.Spinbox(right_col, from_=1, to=20, width=5, justify="right", command=update_rib_positions)
spin_rib_count.set(5)
spin_rib_count.grid(row=2, column=1, padx=5, pady=3, sticky="w")

# Scrollable area for rib positions only
rib_frame_scroll = ttk.Frame(right_col)
rib_frame_scroll.grid(row=3, column=0, columnspan=3, pady=5)

rib_canvas = tk.Canvas(rib_frame_scroll, height=200)
rib_scrollbar = ttk.Scrollbar(rib_frame_scroll, orient="vertical", command=rib_canvas.yview)
rib_positions_inner = ttk.Frame(rib_canvas)
rib_positions_inner.bind(
    "<Configure>", lambda e: rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))
)
rib_canvas.create_window((0, 0), window=rib_positions_inner, anchor="nw")
rib_canvas.configure(yscrollcommand=rib_scrollbar.set)
rib_canvas.pack(side="left", fill="both", expand=True)
rib_scrollbar.pack(side="right", fill="y")

update_rib_positions()

# === BOTTOM CONTROLS ===
bottom_frame = ttk.Frame(main_frame, padding=10)
bottom_frame.grid(row=2, column=0, columnspan=3, pady=15)

export_switch = ttk.Checkbutton(bottom_frame, text="Export Single Parts", bootstyle="round-toggle")
export_switch.grid(row=0, column=0, padx=10)
ttk.Button(bottom_frame, text="Generate Assembly", bootstyle="success", command=confirm_inputs).grid(row=0, column=1, padx=10)

# === START APP ===
root.mainloop()
