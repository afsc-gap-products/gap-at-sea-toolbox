import os
import re
import math
import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET

def integer_to_temperature(t_int, A0, A1, A2, A3, Offset=0, **kwargs):
    par0, par1, par2, par3, par4, par5 = 524288, 1.6e7, 2.9e9, 1.024e8, 2.048e4, 2e5
    t_v = (t_int - par0) / par1
    t_r = (t_v * par2 + par3) / (par4 - t_v * par5)
    ln_r = math.log(t_r)
    t_kelvin = 1.0 / (A0 + A1 * ln_r + A2 * (ln_r**2) + A3 * (ln_r**3))
    return (t_kelvin - 273.15) + Offset

def integer_to_pressure(p_int, tv_int, PA0, PA1, PA2, PTEMPA0, PTEMPA1, PTEMPA2, 
                         PTCA0, PTCA1, PTCA2, PTCB0, PTCB1, PTCB2, **kwargs):
    t_v = tv_int / 13107.0
    t_x = PTEMPA0 + PTEMPA1 * t_v + PTEMPA2 * (t_v**2)
    p_x = p_int - PTCA0 - PTCA1 * t_x - PTCA2 * (t_x**2)
    p_n = p_x * PTCB0 / (PTCB0 + PTCB1 * t_x + PTCB2 * (t_x**2))
    psi = PA0 + PA1 * p_n + PA2 * (p_n**2)
    return (psi - 14.7) * 0.689476

def calc_depth(lat, pressure):
    lat_rad = lat * (math.atan2(1, 1) / 45.0)
    x = math.sin(lat_rad)**2
    gr = 9.780318 * (1 + (0.0052788 + 2.36e-05 * x) * x) + 1.092e-06 * pressure
    depth = ((((-1.82e-15 * pressure + 2.279e-10) * pressure - 2.2512e-05) * pressure + 9.72659) * pressure) / gr
    return depth

def extract_calibration(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    params = {}
    def safe_find_float(parent, tag):
        element = parent.find(tag)
        return float(element.text) if element is not None and element.text else 0.0

    t_sensor = root.find(".//TemperatureSensor")
    params['temp'] = {k: safe_find_float(t_sensor, k) for k in ['A0', 'A1', 'A2', 'A3', 'Offset']}
    
    p_sensor = root.find(".//PressureSensor")
    p_keys = ['PA0', 'PA1', 'PA2', 'PTEMPA0', 'PTEMPA1', 'PTEMPA2', 'PTCA0', 'PTCA1', 'PTCA2', 'PTCB0', 'PTCB1', 'PTCB2']
    params['press'] = {k: safe_find_float(p_sensor, k) for k in p_keys}
    return params

def process_ctd(hex_file, xml_file, btd_output_path, lat, vessel, cruise, haul, model, version, sn, tz_offset):
    bth_output_path = os.path.splitext(btd_output_path)[0] + ".BTH"
    cal = extract_calibration(xml_file)
    
    with open(hex_file, 'r') as f:
        lines = f.readlines()

    start_idx = 0
    cast_time = None
    for i, line in enumerate(lines):
        if "* cast" in line.lower():
            match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})', line)
            if match:
                try:
                    cast_time = datetime.strptime(match.group(1), "%d %b %Y %H:%M:%S")
                except:
                    cast_time = datetime.strptime(match.group(1), "%b %d %Y %H:%M:%S")
        if "*END*" in line:
            start_idx = i + 1
            break

    if cast_time is None: raise ValueError("Start time not found.")

    results = []
    for i, line in enumerate(lines[start_idx:]):
        line = line.strip()
        if len(line) < 18: continue
        t_int, p_int, tv_int = int(line[0:6], 16), int(line[12:18], 16), int(line[18:22], 16) if len(line) >= 22 else 0
        temp = integer_to_temperature(t_int, **cal['temp'])
        press = integer_to_pressure(p_int, tv_int, **cal['press'])
        depth = calc_depth(lat, press)
        timestamp = cast_time + timedelta(seconds=(i * 0.25) + ((float(tz_offset)+8.0) * 3600))
        results.append({'time_elapsed': int(i * 0.25), 'temp': temp, 'depth': depth, 'dt': timestamp})

    df = pd.DataFrame(results).groupby('time_elapsed').agg({'temp':'mean', 'depth':'mean', 'dt':'first'}).reset_index()

    # Write BTD    
    btd_out = pd.DataFrame({
        'VESSEL': vessel, 'CRUISE': cruise, 'HAUL': haul, 'SERIAL': sn,
        'DATE_TIME': df['dt'].dt.strftime("%m/%d/%Y %H:%M:%S"),
        'TEMPERATURE': df['temp'].round(4), 'DEPTH': df['depth'].round(4)
    })
    btd_out.to_csv(btd_output_path, index=False)

    # Write BTH
    # Aggregate by second (mean)
    df_agg = df.groupby('time_elapsed').agg({'temp':'mean', 'depth':'mean', 'dt':'first'}).reset_index()

    bth_out = {
        'VESSEL': [vessel], 'CRUISE': [cruise], 'HAUL': [haul], 
        'MODEL': [model], 'VERSION': [version], 'SERIAL_NUMBER': [sn],
        'HOST_TIME': [df_agg['dt'].iloc[-1].strftime("%m/%d/%Y %H:%M:%S")],
        'LOGGER_TIME': [df_agg['dt'].iloc[0].strftime("%m/%d/%Y %H:%M:%S")],
        'LOGGING_START': [df_agg['dt'].iloc[0].strftime("%m/%d/%Y %H:%M:%S")],
        'LOGGING_END': [df_agg['dt'].iloc[-1].strftime("%m/%d/%Y %H:%M:%S")],
        'SAMPLE_PERIOD': [1], 'NUMBER_CHANNELS': [2],
        'NUMBER_SAMPLES': len(df),
        'MODE': [2]
    }
    pd.DataFrame(bth_out).to_csv(bth_output_path, index=False)

    return btd_output_path, bth_output_path

class CTDConverterGUI(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        tk.Label(self, text="CTD to BTD/BTH Converter", font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(self, text="Extracts data from SeaBird SBE19plus .hex and converts to BTD/BTH that can be loaded by Poseidon.", 
                 font=('Arial', 10, 'italic')).pack(pady=5)

        # 1. METADATA INPUT FRAME
        input_frame = tk.LabelFrame(self, text=" Metadata Inputs ", font=('Arial', 10, 'bold'), padx=15, pady=10)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        fields = [
            ("Vessel (e.g. 162)", "vessel"), ("Cruise (e.g. 202601)", "cruise"), ("Haul (e.g. 99)", "haul"),
            ("Latitude (e.g. 54)", "lat"), ("Model (e.g. SBE19plus)", "model"), ("Version (optional)", "ver"),
            ("Serial (e.g. 8102)", "sn"), ("UTC TZ (hrs; e.g. -8 for AKDT/UTC-8)", "tz")
        ]

        self.entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(input_frame, text=label, width=30, anchor='e').grid(row=i, column=0, padx=5, pady=3)
            ent = tk.Entry(input_frame, width=25)
            ent.grid(row=i, column=1, padx=5, pady=3)
            self.entries[key] = ent

        self.entries['tz'].insert(0, "-8")
        self.entries['model'].insert(0, "SBE19plus")

        # 2. IMPORT FILE PATH FRAME
        files_frame = tk.LabelFrame(self, text=" File Selection ", font=('Arial', 10, 'bold'), padx=15, pady=10)
        files_frame.pack(fill="x", padx=20, pady=10)

        files_label = tk.Label(
            files_frame,
            text="Select the data file (.hex) from your haul and configuration (.xmlcon) file for the CTD (identified by serial number, e.g. 8102).",
            font=("TkDefaultFont", 10),
            wraplength=600,
            justify="left"
        )

        files_label.pack(anchor="w", pady=(0, 10))

        self.hex_path = tk.StringVar()
        self.xml_path = tk.StringVar()
        self.btd_path = tk.StringVar()

        self.add_file_row("Input .hex File:", self.hex_path, "open", files_frame)
        self.add_file_row("Input .xmlcon File:", self.xml_path, "open", files_frame)
        self.add_file_row("Output .BTD File:", self.btd_path, "save", files_frame)

        # 3. ACTION BUTTON FRAME
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="CONVERT DATA", bg="#2e7d32", fg="white", 
                  font=('Arial', 10, 'bold'), height=2, width=22, 
                  command=self.run_conversion).pack(side="left", padx=10)

    def add_file_row(self, label, var, mode, master_frame):
        row = tk.Frame(master_frame)
        tk.Label(row, text=label, width=20, anchor='e').pack(side='left', padx=5)
        tk.Entry(row, textvariable=var, width=45).pack(side='left', padx=5, expand=True, fill='x')
        
        if mode == "open":
            ftype = [("Sea-Bird Files", "*.hex")] if ".hex" in label else [("Config Files", "*.xmlcon")]
            cmd = lambda: var.set(filedialog.askopenfilename(filetypes=ftype))
        else:
            cmd = lambda: var.set(filedialog.asksaveasfilename(defaultextension=".BTD", 
                                                               filetypes=[("BTD file", "*.BTD")]))
        tk.Button(row, text="Browse...", width=10, command=cmd).pack(side='left', padx=5)
        row.pack(fill='x', pady=4)

    def run_conversion(self):
        try:
            btd, bth = process_ctd(
                self.hex_path.get(), self.xml_path.get(), self.btd_path.get(),
                float(self.entries['lat'].get()), self.entries['vessel'].get(),
                self.entries['cruise'].get(), self.entries['haul'].get(),
                self.entries['model'].get(), self.entries['ver'].get(),
                self.entries['sn'].get(), self.entries['tz'].get()
            )
            messagebox.showinfo("Success", f"Files created successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            

class ParentWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GAP Toolbox")
        self.geometry("950x750")

        # Layout
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4, bg="#cccccc")
        self.paned_window.pack(fill="both", expand=True)

        # Left Sidebar
        self.sidebar = tk.Frame(self.paned_window, width=200, padx=10, pady=10)
        self.paned_window.add(self.sidebar)

        tk.Label(self.sidebar, text="Tools:", font=("Arial", 11, "bold")).pack(pady=(0, 10), anchor="w")

        self.listbox = tk.Listbox(self.sidebar, font=("Arial", 10), exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.insert(tk.END, "Convert CTD to BTD")
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.open_selected_widget())

        # Right Workspace
        self.workspace = tk.Frame(self.paned_window, bg="white")
        self.paned_window.add(self.workspace)

    def open_selected_widget(self):
        selection = self.listbox.curselection()
        if not selection: return

        # Clear workspace
        for widget in self.workspace.winfo_children():
            widget.destroy()

        # Load CTD Tool
        tool = CTDConverterGUI(self.workspace)
        tool.pack(fill="both", expand=True)

if __name__ == '__main__':
    app = ParentWidget()
    app.mainloop()