import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import pandas as pd

# Matplotlib imports for Tkinter integration
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class ScopeCalculatorGUI(ttk.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Apply theme
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # App state variables
        self.df = None
        self.file_path = tk.StringVar(value="No file selected")

        self.wire_col_var = tk.StringVar()
        self.port_col_var = tk.StringVar()
        self.stbd_col_var = tk.StringVar()

        self.calc_mode_var = tk.StringVar(value="direct")  # "direct" or "ratio"

        # Form input variables
        self.direct_scope_var = tk.StringVar()
        self.scope_ratio_var = tk.StringVar()
        self.bottom_depth_var = tk.StringVar()
        self.waterline_offset_var = tk.StringVar(value="0.0")

        self._build_ui()

    def _build_ui(self):
        # Outer container frame inside the widget
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # WIDGET TITLE & DESCRIPTION (Converted to ttk.Label for matching bg)
        # -------------------------------------------------------------
        title_text = "Calculate Winch Scope"
        self.lbl_header = ttk.Label(
            main_frame,
            text=title_text,
            font=("Arial", 12, "bold"),
            wraplength=500,
            justify="center",
        )
        self.lbl_header.pack(pady=(0, 2))

        description_text = (
            "Calculate port and starboard trawl winch wire out values using a "
            "vessel-specific calibration table."
        )
        self.lbl_desc = ttk.Label(
            main_frame,
            text=description_text,
            font=("Arial", 10, "italic"),
            wraplength=500,
            justify="center",
        )
        self.lbl_desc.pack(pady=(0, 10))

        # -------------------------------------------------------------
        # 1. FILE SELECTION
        # -------------------------------------------------------------
        file_frame = ttk.LabelFrame(
            main_frame, text=" 1. Load Calibration CSV ", padding="10"
        )
        file_frame.pack(fill=tk.X, pady=(0, 8))

        top_desc_label = ttk.Label(
            file_frame,
            text="Load a .csv file containing three columns with (1) measured warp values, (2) port winch measurements, and (3) starboard winch values.",
            wraplength=500,
            justify="left",
            font=("TkDefaultFont", 9),
        )
        top_desc_label.pack(anchor=tk.W, pady=(0, 6))

        btn_browse = ttk.Button(
            file_frame, text="Browse CSV File...", command=self.load_csv
        )
        btn_browse.pack(side=tk.LEFT, padx=(0, 10))

        lbl_file = ttk.Label(
            file_frame,
            textvariable=self.file_path,
            foreground="gray",
            wraplength=350,
        )
        lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # -------------------------------------------------------------
        # 2. COLUMN MAPPING
        # -------------------------------------------------------------
        self.col_frame = ttk.LabelFrame(
            main_frame, text=" 2. Map CSV Columns ", padding="10"
        )
        self.col_frame.pack(fill=tk.X, pady=(0, 8))

        # Wire Out Dropdown
        ttk.Label(self.col_frame, text="Actual Wire Out Column:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.cb_wire = ttk.Combobox(
            self.col_frame,
            textvariable=self.wire_col_var,
            state="disabled",
            width=25,
        )
        self.cb_wire.grid(row=0, column=1, sticky=tk.E, pady=2, padx=5)

        # Port Winch Dropdown
        ttk.Label(self.col_frame, text="Port Winch Column:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.cb_port = ttk.Combobox(
            self.col_frame,
            textvariable=self.port_col_var,
            state="disabled",
            width=25,
        )
        self.cb_port.grid(row=1, column=1, sticky=tk.E, pady=2, padx=5)

        # Starboard Winch Dropdown
        ttk.Label(self.col_frame, text="Starboard Winch Column:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.cb_stbd = ttk.Combobox(
            self.col_frame,
            textvariable=self.stbd_col_var,
            state="disabled",
            width=25,
        )
        self.cb_stbd.grid(row=2, column=1, sticky=tk.E, pady=2, padx=5)

        # -------------------------------------------------------------
        # 3. TARGET CALCULATIONS / INPUTS (Horizontal Layout)
        # -------------------------------------------------------------
        calc_frame = ttk.LabelFrame(
            main_frame, text=" 3. Target Parameters ", padding="10"
        )
        calc_frame.pack(fill=tk.X, pady=(0, 8))

        # Left Column: Direct Target
        left_calc_frame = ttk.Frame(calc_frame)
        left_calc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        rb_direct = ttk.Radiobutton(
            left_calc_frame,
            text="Direct Target Wire Out",
            variable=self.calc_mode_var,
            value="direct",
            command=self.toggle_mode_inputs,
        )
        rb_direct.pack(anchor=tk.W, pady=(0, 4))

        direct_input_frame = ttk.Frame(left_calc_frame)
        direct_input_frame.pack(anchor=tk.W, padx=15)

        ttk.Label(direct_input_frame, text="Target Wire Out (fm):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.ent_direct = ttk.Entry(
            direct_input_frame, textvariable=self.direct_scope_var, width=12
        )
        self.ent_direct.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        # Vertical Separator
        ttk.Separator(calc_frame, orient="vertical").pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )

        # Right Column: Scope Ratio & Depth
        right_calc_frame = ttk.Frame(calc_frame)
        right_calc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        rb_ratio = ttk.Radiobutton(
            right_calc_frame,
            text="Scope Ratio & Bottom Depth",
            variable=self.calc_mode_var,
            value="ratio",
            command=self.toggle_mode_inputs,
        )
        rb_ratio.pack(anchor=tk.W, pady=(0, 4))

        ratio_input_frame = ttk.Frame(right_calc_frame)
        ratio_input_frame.pack(anchor=tk.W, padx=15)

        ttk.Label(ratio_input_frame, text="Target Scope Ratio:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.ent_ratio = ttk.Entry(
            ratio_input_frame, textvariable=self.scope_ratio_var, width=10
        )
        self.ent_ratio.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        ttk.Label(ratio_input_frame, text="Bottom Depth (m):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.ent_depth = ttk.Entry(
            ratio_input_frame, textvariable=self.bottom_depth_var, width=10
        )
        self.ent_depth.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        ttk.Label(ratio_input_frame, text="Waterline Offset (m):").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.ent_offset = ttk.Entry(
            ratio_input_frame, textvariable=self.waterline_offset_var, width=10
        )
        self.ent_offset.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        # -------------------------------------------------------------
        # 4. ACTION BUTTONS (Calculate & Plot)
        # -------------------------------------------------------------
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=8)

        btn_calc = tk.Button(
            action_frame,
            text="Calculate Winch Settings",
            command=self.calculate,
            bg="#02a54b",
            fg="white",
            activebackground="#02823b",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            relief="raised",
            bd=1,
            cursor="hand2",
        )
        btn_calc.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=4)

        btn_plot = tk.Button(
            action_frame,
            text="Plot Calibration Data",
            command=self.plot_calibration,
            bg="#0275d8",
            fg="white",
            activebackground="#025aa5",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            relief="raised",
            bd=1,
            cursor="hand2",
        )
        btn_plot.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0), ipady=4)

        # -------------------------------------------------------------
        # 5. OUTPUTS / RESULTS DISPLAY (Single Horizontal Line)
        # -------------------------------------------------------------
        out_frame = ttk.LabelFrame(
            main_frame, text=" Results ", padding="10"
        )
        out_frame.pack(fill=tk.X, pady=(0, 5))

        res_container = ttk.Frame(out_frame)
        res_container.pack(fill=tk.X, expand=True)

        self.lbl_res_scope = ttk.Label(
            res_container,
            text="True Scope: -- fm",
            font=("Arial", 10, "bold"),
        )
        self.lbl_res_scope.pack(side=tk.LEFT, expand=True, anchor=tk.CENTER)

        self.lbl_res_port = ttk.Label(
            res_container, text="Port Winch: -- fm", font=("Arial", 10)
        )
        self.lbl_res_port.pack(side=tk.LEFT, expand=True, anchor=tk.CENTER)

        self.lbl_res_stbd = ttk.Label(
            res_container, text="Starboard Winch: -- fm", font=("Arial", 10)
        )
        self.lbl_res_stbd.pack(side=tk.LEFT, expand=True, anchor=tk.CENTER)

        # Initialize input box states
        self.toggle_mode_inputs()

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select Calibration CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            self.df = pd.read_csv(path)
            self.file_path.set(os.path.basename(path))

            columns = list(self.df.columns)

            for cb in [self.cb_wire, self.cb_port, self.cb_stbd]:
                cb["values"] = columns
                cb["state"] = "readonly"

            self._auto_select_columns(columns)

            messagebox.showinfo(
                "Success", f"CSV loaded successfully with {len(self.df)} rows."
            )

        except Exception as e:
            messagebox.showerror(
                "Error Loading CSV", f"Could not parse the CSV file:\n{e}"
            )

    def _auto_select_columns(self, columns):
        cols_lower = [str(c).lower() for c in columns]

        for col, col_lower in zip(columns, cols_lower):
            if "wire" in col_lower or "scope" in col_lower:
                self.wire_col_var.set(col)
            elif "port" in col_lower:
                self.port_col_var.set(col)
            elif "stbd" in col_lower or "starboard" in col_lower:
                self.stbd_col_var.set(col)

    def toggle_mode_inputs(self):
        mode = self.calc_mode_var.get()
        if mode == "direct":
            self.ent_direct.config(state="normal")
            self.ent_ratio.config(state="disabled")
            self.ent_depth.config(state="disabled")
            self.ent_offset.config(state="disabled")
        else:
            self.ent_direct.config(state="disabled")
            self.ent_ratio.config(state="normal")
            self.ent_depth.config(state="normal")
            self.ent_offset.config(state="normal")

    def _get_validated_calib_data(self):
        """Helper to validate file/column mapping and return extracted data arrays."""
        if self.df is None:
            messagebox.showwarning(
                "Missing Data", "Please select and load a calibration CSV file."
            )
            return None

        wire_col = self.wire_col_var.get()
        port_col = self.port_col_var.get()
        stbd_col = self.stbd_col_var.get()

        if not (wire_col and port_col and stbd_col):
            messagebox.showwarning(
                "Missing Selection",
                "Please map all three CSV columns before proceeding.",
            )
            return None

        if len({wire_col, port_col, stbd_col}) < 3:
            messagebox.showwarning(
                "Duplicate Selection", "Each dropdown must select a distinct column."
            )
            return None

        try:
            calib_data = self.df[[wire_col, port_col, stbd_col]].dropna().copy()
            calib_data[wire_col] = pd.to_numeric(calib_data[wire_col])
            calib_data[port_col] = pd.to_numeric(calib_data[port_col])
            calib_data[stbd_col] = pd.to_numeric(calib_data[stbd_col])
            calib_data = calib_data.sort_values(by=wire_col)
            return calib_data, wire_col, port_col, stbd_col
        except Exception as e:
            messagebox.showerror(
                "Data Error",
                f"Selected columns must contain numeric values.\nError: {e}",
            )
            return None

    def calculate(self):
        result = self._get_validated_calib_data()
        if result is None:
            return

        calib_data, wire_col, port_col, stbd_col = result

        wire_arr = calib_data[wire_col].values
        port_arr = calib_data[port_col].values
        stbd_arr = calib_data[stbd_col].values

        mode = self.calc_mode_var.get()
        target_scope_fm = None

        try:
            if mode == "direct":
                target_scope_fm = float(self.direct_scope_var.get())
            else:
                ratio = float(self.scope_ratio_var.get())
                depth_m = float(self.bottom_depth_var.get())
                offset_m = (
                    float(self.waterline_offset_var.get())
                    if self.waterline_offset_var.get()
                    else 0.0
                )

                bottom_depth_fm = (depth_m + offset_m) / 1.8288
                target_scope_fm = ratio * bottom_depth_fm

        except ValueError:
            messagebox.showerror(
                "Input Error",
                "Please enter valid numeric values for the target inputs.",
            )
            return

        max_wire = np.max(wire_arr)
        min_wire = np.min(wire_arr)

        if target_scope_fm > max_wire:
            messagebox.showerror(
                "Out of Bounds",
                f"Target wire out ({target_scope_fm:.2f} fm) exceeds table maximum ({max_wire:.2f} fm).",
            )
            return
        elif target_scope_fm < min_wire:
            messagebox.showerror(
                "Out of Bounds",
                f"Target wire out ({target_scope_fm:.2f} fm) is below table minimum ({min_wire:.2f} fm).",
            )
            return

        port_target = float(np.interp(target_scope_fm, wire_arr, port_arr))
        stbd_target = float(np.interp(target_scope_fm, wire_arr, stbd_arr))

        self.lbl_res_scope.config(
            text=f"True Target Scope: {target_scope_fm:.2f} fm"
        )
        self.lbl_res_port.config(text=f"Port Winch Setting: {port_target:.2f} fm")
        self.lbl_res_stbd.config(
            text=f"Starboard Winch Setting: {stbd_target:.2f} fm"
        )

    def plot_calibration(self):
        """Generates a pop-up Matplotlib figure plotting Actual Scope vs Winch Scope."""
        result = self._get_validated_calib_data()
        if result is None:
            return

        calib_data, wire_col, port_col, stbd_col = result

        x_wire = calib_data[wire_col].values
        y_port = calib_data[port_col].values
        y_stbd = calib_data[stbd_col].values

        # 1. Create a popup window for the plot
        plot_window = tk.Toplevel(self)
        plot_window.title("Winch Scope Calibration Curves")
        plot_window.geometry("750x600")

        # 2. Build the Figure
        fig = Figure(figsize=(7, 5), dpi=100)
        ax = fig.add_subplot(111)

        # Plot Port and Starboard calibration points and connecting lines
        ax.plot(
            x_wire,
            y_port,
            "o-",
            label=f"Port Winch ({port_col})",
            color="#1f77b4",
            linewidth=2,
            markersize=6,
        )
        ax.plot(
            x_wire,
            y_stbd,
            "s-",
            label=f"Starboard Winch ({stbd_col})",
            color="#ff7f0e",
            linewidth=2,
            markersize=6,
        )

        # Plot 1:1 reference line for comparison
        min_val = min(x_wire.min(), y_port.min(), y_stbd.min())
        max_val = max(x_wire.max(), y_port.max(), y_stbd.max())
        ax.plot(
            [min_val, max_val],
            [min_val, max_val],
            "k--",
            alpha=0.5,
            label="1:1 Reference Line",
        )

        ax.set_xlabel("Actual Wire Out (fathoms)", fontsize=10, fontweight="bold")
        ax.set_ylabel("Winch Scope Reading (fathoms)", fontsize=10, fontweight="bold")
        ax.set_title(
            "Actual Scope vs. Winch Scope Calibration",
            fontsize=12,
            fontweight="bold",
            pad=12,
        )
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper left")

        fig.tight_layout()

        # 3. Embed Matplotlib canvas into Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add native plot toolbar (Zoom, Pan, Save image)
        toolbar = NavigationToolbar2Tk(canvas, plot_window)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


# Testing block
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Trawl Winch Calculator Test")
    root.geometry("620x650")
    calculator = ScopeCalculatorGUI(root)
    calculator.pack(fill="both", expand=True)
    root.mainloop()