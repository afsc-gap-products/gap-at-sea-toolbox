import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class XMLToBTDConverterGUI(tk.Frame):  # Inherits from tk.Frame

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.xml_path = tk.StringVar()
        self.df_data = None  
        self.cleaned_df = None

        self._create_widgets()

    def _create_widgets(self):
        tk.Label(self, text="SCS XML to BTD/BTH Converter", font=('Arial', 12, 'bold')).pack(pady=10)
        top_desc_label = ttk.Label(
            self, 
            text="Extracts temperature/depth data from an SCS .xml file and write to .BTD/.BTH that can be loaded by Poseidon.",
            wraplength=500,
            justify="left",
            font=("TkDefaultFont", 10)
        )
        top_desc_label.pack(fill="x", padx=15, pady=(15, 5))

        file_frame = tk.LabelFrame(self, text=" File Selection ", font=('Arial', 10, 'bold'), padx=10, pady=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Entry(file_frame, textvariable=self.xml_path, width=40).pack(
            side="left", expand=True, fill="x", padx=5
        )
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(
            side="right"
        )

        meta_frame = tk.LabelFrame(self, text=" Metadata Inputs ", font=('Arial', 10, 'bold'), padx=10, pady=10)
        meta_frame.pack(fill="x", padx=10, pady=5)

        # Auto-import info notice text
        auto_import_label = ttk.Label(
            meta_frame,
            text="Vessel, cruise, and haul will be imported automatically from the selected file.",
            font=("TkDefaultFont", 10),
            wraplength=500,
            justify="left"
        )
        auto_import_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        metadata_fields = [
            ("Vessel (e.g. 162):", "vessel_entry", ""),
            ("Cruise (e.g. 202601):", "cruise_entry", ""),
            ("Haul (e.g. 99):", "haul_entry", ""),
            ("Model Number (e.g. Marport Trident Pro):", "model_entry", "Marport Trident Pro"),
            ("Version Number (optional):", "version_entry", ""),
            ("Serial Number (optional):", "serial_entry", ""),
        ]

        for idx, (label, attr, default) in enumerate(metadata_fields):
            ttk.Label(meta_frame, text=label).grid(row=idx + 1, column=0, sticky="w", pady=4)
            entry = ttk.Entry(meta_frame, width=30)
            entry.insert(0, default)
            entry.grid(row=idx + 1, column=1, padx=10, pady=4, sticky="ew")
            setattr(self, attr, entry)

        meta_frame.columnconfigure(1, weight=1)

        filter_frame = tk.LabelFrame(self, text=" Window Filters ", font=('Arial', 10, 'bold'), padx=10, pady=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Row 0: Header text spanning all 4 columns
        filter_label = ttk.Label(
            filter_frame,
            text="Window filter for screening outliers; OK to use default values.",
            font=("TkDefaultFont", 10),
            wraplength=500,
            justify="left"
        )
        filter_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Row 1: Depth (Min and Max side-by-side)
        ttk.Label(filter_frame, text="Min Depth (m):").grid(row=1, column=0, sticky="w", pady=2)
        self.min_depth_entry = ttk.Entry(filter_frame, width=12)
        self.min_depth_entry.insert(0, "-0.1")
        self.min_depth_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(filter_frame, text="Max Depth (m):").grid(row=1, column=2, sticky="w", pady=2, padx=(10, 0))
        self.max_depth_entry = ttk.Entry(filter_frame, width=12)
        self.max_depth_entry.insert(0, "800")
        self.max_depth_entry.grid(row=1, column=3, padx=5, pady=2, sticky="w")

        # Row 2: Temperature (Min and Max side-by-side)
        ttk.Label(filter_frame, text="Min Temp (°C):").grid(row=2, column=0, sticky="w", pady=2)
        self.min_temp_entry = ttk.Entry(filter_frame, width=12)
        self.min_temp_entry.insert(0, "-2")
        self.min_temp_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(filter_frame, text="Max Temp (°C):").grid(row=2, column=2, sticky="w", pady=2, padx=(10, 0))
        self.max_temp_entry = ttk.Entry(filter_frame, width=12)
        self.max_temp_entry.insert(0, "24")
        self.max_temp_entry.grid(row=2, column=3, padx=5, pady=2, sticky="w")

        # Action Button Frame
        btn_frame = ttk.Frame(self, padding=2)
        btn_frame.pack(fill="x", padx=10, pady=2)

        self.process_btn = tk.Button(
            btn_frame,
            text="Load XML & Open Interactive Cleaner", bg="#2e7d32", fg="white",
            font=('Arial', 10, 'bold'),
            command=self._process_xml,
        )
        self.process_btn.pack(fill="x", ipady=5)

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if file_path:
            self.xml_path.set(file_path)
            self._autofill_metadata_from_xml(file_path)

    def _autofill_metadata_from_xml(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for log_entry in root.findall(".//DiagnosticsLogEntry"):
                text = log_entry.text or ""
                if "Meta Item (Vessel) updated to:" in text:
                    vessel = text.split("to:")[-1].strip().split("|")[0].strip()
                    if "Northwest Explorer" in vessel:
                        vessel = "134"
                    self.vessel_entry.delete(0, tk.END)
                    self.vessel_entry.insert(0, vessel)
                elif "Meta Item (Cruise) updated to:" in text:
                    cruise = text.split("to:")[-1].strip()
                    self.cruise_entry.delete(0, tk.END)
                    self.cruise_entry.insert(0, cruise)
                elif "Meta Item (Haul) updated to:" in text:
                    haul = text.split("to:")[-1].strip()
                    self.haul_entry.delete(0, tk.END)
                    self.haul_entry.insert(0, haul)
        except Exception:
            pass

    def _process_xml(self):
        path = self.xml_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid XML file path.")
            return

        try:
            min_d = float(self.min_depth_entry.get())
            max_d = float(self.max_depth_entry.get())
            min_t = float(self.min_temp_entry.get())
            max_t = float(self.max_temp_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Filter window boundaries must be numerical expressions.")
            return

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            messagebox.showerror("XML Parse Error", f"Could not read XML file:\n{e}")
            return

        depth_records = []
        temp_records = []

        for data_item in root.findall(".//DataItem"):
            timestamp_str = data_item.get("timestamp")
            text = data_item.text or ""

            if not timestamp_str or "HR," not in text:
                continue

            try:
                dt = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue

            dt = dt.replace(microsecond=0)

            val_match = re.search(r",([^,]+)\*[0-9A-Fa-f]{2}$", text.strip())
            if not val_match:
                continue
            try:
                value = float(val_match.group(1))
            except ValueError:
                continue

            if "DPT" in text:
                depth_records.append({"DATE_TIME": dt, "DEPTH": value})
            elif "TMP" in text:
                temp_records.append({"DATE_TIME": dt, "TEMPERATURE": value})

        if not depth_records and not temp_records:
            messagebox.showwarning("Warning", "No valid Marport Trident Pro strings found in XML log.")
            return

        df_depth = pd.DataFrame(depth_records)
        df_temp = pd.DataFrame(temp_records)

        if not df_depth.empty and not df_temp.empty:
            df_depth = df_depth.drop_duplicates(subset=["DATE_TIME"])
            df_temp = df_temp.drop_duplicates(subset=["DATE_TIME"])
            self.df_data = pd.merge(df_depth, df_temp, on="DATE_TIME", how="outer")
        elif not df_depth.empty:
            self.df_data = df_depth
            self.df_data["TEMPERATURE"] = np.nan
        else:
            self.df_data = df_temp
            self.df_data["DEPTH"] = np.nan

        self.df_data = self.df_data.sort_values("DATE_TIME").reset_index(drop=True)
        self.df_data["DATE_TIME"] = self.df_data["DATE_TIME"].dt.tz_convert("America/Anchorage")

        if "DEPTH" in self.df_data.columns:
            self.df_data.loc[(self.df_data["DEPTH"] < min_d) | (self.df_data["DEPTH"] > max_d), "DEPTH"] = np.nan
        if "TEMPERATURE" in self.df_data.columns:
            self.df_data.loc[(self.df_data["TEMPERATURE"] < min_t) | (self.df_data["TEMPERATURE"] > max_t), "TEMPERATURE"] = np.nan

        self.df_data = self.df_data.dropna(subset=["DEPTH", "TEMPERATURE"], how="all").reset_index(drop=True)
        self._launch_interactive_plot()

    def _launch_interactive_plot(self):
        plot_window = tk.Toplevel(self.winfo_toplevel())
        plot_window.title("Interactive Point Removal Window")
        plot_window.geometry("800x750")

        self.working_df = self.df_data.copy()

        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        fig.suptitle(
            "Left-click on a point to remove it.\nUse control buttons below to save or cancel.",
            fontsize=10,
            color="darkblue",
        )

        times = self.working_df["DATE_TIME"].dt.to_pydatetime()

        (line1,) = ax1.plot(times, self.working_df["TEMPERATURE"], "ro", picker=True, pickradius=5, label="Temp")
        ax1.set_ylabel("Temperature (°C)")
        ax1.grid(True)

        (line2,) = ax2.plot(times, self.working_df["DEPTH"], "bo", picker=True, pickradius=5, label="Depth")
        ax2.set_ylabel("Depth (m)")
        ax2.set_xlabel("Time (Alaska)")
        ax2.grid(True)

        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas_widget = canvas.get_tk_widget()  
        canvas_widget.pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, plot_window)
        toolbar.update()

        control_frame = ttk.Frame(plot_window, padding=10)
        control_frame.pack(side="bottom", fill="x")

        def save_and_close():
            self.cleaned_df = self.working_df.copy()
            plt.close(fig)
            plot_window.destroy()
            self._write_output_files()

        def close_without_saving():
            plt.close(fig)
            plot_window.destroy()

        save_btn = ttk.Button(control_frame, text="Close and Save", command=save_and_close)
        save_btn.pack(side="right", padx=5)

        close_btn = ttk.Button(control_frame, text="Close", command=close_without_saving)
        close_btn.pack(side="right", padx=5)

        plot_window.protocol("WM_DELETE_WINDOW", close_without_saving)

        def on_pick(event):
            if toolbar.mode != "":
                return

            artist = event.artist
            ind = event.ind[0]  

            if ind >= len(self.working_df):
                return

            target_idx = self.working_df.index[ind]

            if artist == line1:
                self.working_df.loc[target_idx, "TEMPERATURE"] = np.nan
            elif artist == line2:
                self.working_df.loc[target_idx, "DEPTH"] = np.nan

            if pd.isna(self.working_df.loc[target_idx, "DEPTH"]) and pd.isna(self.working_df.loc[target_idx, "TEMPERATURE"]):
                self.working_df = self.working_df.drop(target_idx)

            current_times = self.working_df["DATE_TIME"].dt.to_pydatetime()
            line1.set_data(current_times, self.working_df["TEMPERATURE"])
            line2.set_data(current_times, self.working_df["DEPTH"])

            ax1.relim()
            ax1.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()
            canvas.draw()

        fig.canvas.mpl_connect("pick_event", on_pick)

    def _write_output_files(self):
        if self.cleaned_df is None or self.cleaned_df.empty:
            messagebox.showwarning("Export Cancelled", "No valid data remaining to output.")
            return

        vessel = self.vessel_entry.get()
        cruise = self.cruise_entry.get()
        haul = self.haul_entry.get()
        model_num = self.model_entry.get()
        version_num = self.version_entry.get()
        serial_num = self.serial_entry.get()

        try:
            haul_val = int(haul)
            padded_haul = f"{haul_val:04d}"
        except ValueError:
            padded_haul = str(haul)

        suggested_name = f"HAUL{padded_haul}.BTD"

        btd_path = filedialog.asksaveasfilename(
            initialfile=suggested_name,
            defaultextension=".BTD",
            filetypes=[("BTD files", "*.BTD"), ("All files", "*.*")],
            title="Save BTD Data File"
        )

        if not btd_path:
            messagebox.showwarning("Export Cancelled", "The file save operation was canceled.")
            return

        base_path, _ = os.path.splitext(btd_path)
        bth_path = base_path + ".BTH"

        btd_filename = os.path.basename(btd_path)
        bth_filename = os.path.basename(bth_path)

        max_time_str = self.cleaned_df["DATE_TIME"].max().strftime("%m/%d/%Y %H:%M:%S")
        min_time_str = self.cleaned_df["DATE_TIME"].min().strftime("%m/%d/%Y %H:%M:%S")

        time_diffs = self.cleaned_df["DATE_TIME"].diff().dropna()
        sample_period = int(time_diffs.median().total_seconds()) if not time_diffs.empty else 1

        bth_data = {
            "VESSEL": [vessel],
            "CRUISE": [cruise],
            "HAUL": [haul],
            "MODEL_NUMBER": [model_num],
            "VERSION_NUMBER": [version_num if version_num else ""],
            "SERIAL_NUMBER": [serial_num if serial_num else ""],
            "HOST_TIME": [max_time_str],
            "LOGGER_TIME": [max_time_str],
            "LOGGING_START": [min_time_str],
            "LOGGING_END": [max_time_str],
            "SAMPLE_PERIOD": [sample_period],
            "NUMBER_CHANNELS": [2],
            "NUMBER_SAMPLES": [len(self.cleaned_df)],
            "MODE": [2],
        }

        df_bth_out = pd.DataFrame(bth_data)
        df_bth_out.to_csv(bth_path, index=False, quotechar='"')

        def format_date_btd(dt_series):
            raw_strs = dt_series.dt.strftime("%m/%d/%Y %H:%M:%S")
            cleaned = []
            for s in raw_strs:
                if s.startswith("0"):
                    s = s[1:]
                s = s.replace("/0", "/")
                cleaned.append(s)
            return cleaned

        df_btd_out = pd.DataFrame()
        df_btd_out["VESSEL"] = [vessel] * len(self.cleaned_df)
        df_btd_out["CRUISE"] = [cruise] * len(self.cleaned_df)
        df_btd_out["HAUL"] = [haul] * len(self.cleaned_df)
        df_btd_out["SERIAL_NUMBER"] = [serial_num] * len(self.cleaned_df)
        df_btd_out["DATE_TIME"] = format_date_btd(self.cleaned_df["DATE_TIME"])

        df_btd_out["TEMPERATURE"] = self.cleaned_df["TEMPERATURE"].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else ""
        )
        df_btd_out["DEPTH"] = self.cleaned_df["DEPTH"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else ""
        )

        df_btd_out.to_csv(btd_path, index=False, quotechar='"')

        msg = f"Files exported successfully:\n\n1. {btd_filename}\n2. {bth_filename}\n\nSaved to directory: {os.path.dirname(btd_path)}"
        messagebox.showinfo("Success", msg)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Debug Mode Root Container")
    root.geometry("540x650")
    app = XMLToBTDConverterGUI(root)
    app.pack(fill="both", expand=True)
    root.mainloop()