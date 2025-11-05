import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ttkbootstrap as tb
from ttkbootstrap import Style
import assembly
import os
import sys

# ============================
#   GESTIONE ICONA E PERCORSI
# ============================

def resource_path(relative_path):
    """Ottiene il percorso assoluto per le risorse, funziona per dev e per PyInstaller"""
    try:
        # PyInstaller crea una cartella temp e memorizza il percorso in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    path = os.path.join(base_path, relative_path)
    return path

# ============================
#   GUI SETUP
# ============================

style = Style("flatly")
root = style.master
root.title("CAD Wing Assembly Generator")
root.geometry("900x650")
root.minsize(850, 600)
root.resizable(True, True)

# Imposta l'icona
try:
    icon_path = resource_path("icon.ico")
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"Impossibile caricare l'icona: {e}")

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

# Configurare i pesi per la responsività
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(2, weight=1)
main_frame.rowconfigure(1, weight=1)

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
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))

def configure_scroll_region(event=None):
    rib_canvas.configure(scrollregion=rib_canvas.bbox("all"))

def on_canvas_configure(event):
    rib_canvas.itemconfig("inner_frame", width=event.width)

def confirm_inputs():
    import traceback
    try:
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
                # warn about ribs too close to tips
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
#   LAYOUT MIGLIORATO
# ============================

title = ttk.Label(main_frame, text="CAD Wing Assembly Generator", font=("Segoe UI", 16, "bold"))
title.grid(row=0, column=0, columnspan=3, pady=15)

# === GENERAL PARAMETERS FRAME ===
general_frame = ttk.LabelFrame(main_frame, text="General Parameters", padding=15)
general_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
general_frame.columnconfigure(1, weight=1)

def add_row(frame, label, default, row, unit=None):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=4)
    e = ttk.Entry(frame, width=12, justify="right")
    e.insert(0, default)
    e.grid(row=row, column=1, padx=5, pady=4, sticky="ew")
    if unit:
        ttk.Label(frame, text=unit).grid(row=row, column=2, sticky="w", padx=(0, 5))
    return e

entry_naca = add_row(general_frame, "NACA Code:", "2412", 0)
entry_span = add_row(general_frame, "Wing Span:", "1000", 1, "mm")
entry_chord = add_row(general_frame, "Chord Length:", "350", 2, "mm")
entry_wall = add_row(general_frame, "Wall Thickness:", "2.0", 3, "mm")
entry_points = add_row(general_frame, "Num. Points/Surface:", "100", 4)

# Export Path
ttk.Label(general_frame, text="Export Path:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
entry_export_path = ttk.Entry(general_frame, width=20, justify="right")
entry_export_path.insert(0, "C:/Users/ospite/Desktop")
entry_export_path.grid(row=5, column=1, padx=5, pady=4, sticky="ew")
ttk.Button(general_frame, text="Browse", command=browse_folder, width=8).grid(row=5, column=2, padx=5, pady=4)

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

# Separatore verticale
sep_vert = ttk.Separator(main_frame, orient="vertical")
sep_vert.grid(row=1, column=1, rowspan=2, sticky="ns", padx=10, pady=10)

# === RIB PARAMETERS FRAME ===
rib_frame = ttk.LabelFrame(main_frame, text="Rib Parameters", padding=15)
rib_frame.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=10, pady=5)
rib_frame.columnconfigure(0, weight=1)
rib_frame.rowconfigure(3, weight=1)

# Rib thickness e count
entry_rib_thickness = add_row(rib_frame, "Thickness:", "3.0", 0, "mm")

ttk.Label(rib_frame, text="Rib Count:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
spin_rib_count = ttk.Spinbox(rib_frame, from_=1, to=20, width=8, justify="right", command=update_rib_positions)
spin_rib_count.set(5)
spin_rib_count.grid(row=1, column=1, padx=5, pady=4, sticky="w")

# Area scrollable per rib positions
rib_positions_container = ttk.LabelFrame(rib_frame, text="Rib Positions (0-1)")
rib_positions_container.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)
rib_positions_container.columnconfigure(0, weight=1)
rib_positions_container.rowconfigure(0, weight=1)

# Frame per canvas e scrollbar
rib_scroll_frame = ttk.Frame(rib_positions_container)
rib_scroll_frame.grid(row=0, column=0, sticky="nsew")
rib_scroll_frame.columnconfigure(0, weight=1)
rib_scroll_frame.rowconfigure(0, weight=1)

rib_canvas = tk.Canvas(rib_scroll_frame, height=180, highlightthickness=0)
rib_scrollbar = ttk.Scrollbar(rib_scroll_frame, orient="vertical", command=rib_canvas.yview)
rib_positions_inner = ttk.Frame(rib_canvas)

rib_canvas.create_window((0, 0), window=rib_positions_inner, anchor="nw", tags="inner_frame")
rib_canvas.configure(yscrollcommand=rib_scrollbar.set)

# Binding per il resize
rib_positions_inner.bind("<Configure>", configure_scroll_region)
rib_canvas.bind("<Configure>", on_canvas_configure)

rib_canvas.grid(row=0, column=0, sticky="nsew")
rib_scrollbar.grid(row=0, column=1, sticky="ns")

# Inizializza le rib positions
update_rib_positions()

# === BOTTOM CONTROLS ===
bottom_frame = ttk.Frame(main_frame, padding=15)
bottom_frame.grid(row=3, column=0, columnspan=3, pady=20, sticky="ew")

# Centrare i controlli bottom
bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=0)
bottom_frame.columnconfigure(2, weight=1)

export_switch = ttk.Checkbutton(bottom_frame, text="Export Single Parts", bootstyle="round-toggle")
export_switch.grid(row=0, column=1, padx=10)

generate_btn = ttk.Button(bottom_frame, text="Generate Assembly", bootstyle="success", command=confirm_inputs)
generate_btn.grid(row=0, column=2, padx=10)

# Status bar
status_bar = ttk.Label(main_frame, text="Ready", relief="sunken", anchor="w")
status_bar.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

# === START APP ===
root.mainloop()