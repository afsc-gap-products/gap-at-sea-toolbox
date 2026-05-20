import sqlite3
import pandas as pd
import math
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
import zoneinfo

def transform_3857_to_4326(x_3857, y_3857):
    """Converts EPSG:3857 (Pseudo-Mercator) to EPSG:4326 (WGS84)"""
    x_const = 20037508.34
    lon = (x_3857 * 180.0) / x_const
    lat_val = y_3857 / (x_const / 180.0)
    exp_const = (math.pi / 180.0) * lat_val
    lat = math.atan(math.exp(exp_const)) / (math.pi / 360.0) - 90.0
    return lon, lat

def dd_to_dmm(dd):
    """Converts decimal degrees to degree decimal minutes (DMM)"""
    abs_dd = abs(dd)
    degrees = math.floor(abs_dd)
    minutes = (abs_dd % 1) * 60
    return (degrees * 100 + minutes) * (1 if dd >= 0 else -1)

def convert_tzdb_to_gps(path_tzdb, output_file, vessel, cruise, haul, start_dt, end_dt):
    tz_origin = datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
    start_offset = (start_dt.astimezone(zoneinfo.ZoneInfo("UTC")) - tz_origin).total_seconds()
    end_offset = (end_dt.astimezone(zoneinfo.ZoneInfo("UTC")) - tz_origin).total_seconds()

    query = f"SELECT date, x, y FROM data WHERE date >= {start_offset} AND date <= {end_offset}"
    
    try:
        conn = sqlite3.connect(path_tzdb)
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        raise Exception(f"Database error: {e}")

    if df.empty:
        raise ValueError("No data found in the selected time range.")

    df.columns = [c.lower() for c in df.columns] 
    df = df.dropna(subset=['date', 'x', 'y'])

    df['x'] = df['x'] / 100.0
    df['y'] = df['y'] / 100.0

    coords = df.apply(lambda row: transform_3857_to_4326(row['x'], row['y']), axis=1)
    df['X_wgs'], df['Y_wgs'] = zip(*coords)

    df['X_final'] = df['X_wgs'].apply(dd_to_dmm).round(4)
    df['Y_final'] = df['Y_wgs'].apply(dd_to_dmm).round(4)

    df['Date_str'] = df['date'].apply(lambda d: (tz_origin + timedelta(seconds=d)).strftime("%m/%d/%y %H:%M:%S"))

    df['vessel'] = vessel
    df['cruise'] = cruise
    df['haul'] = haul

    output = df[['vessel', 'cruise', 'haul', 'Date_str', 'Y_final', 'X_final']]
    output.to_csv(output_file, index=False, header=False, quoting=3, sep=",")
    return len(output)

class TZDBConverterGUI(tk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Title
        title_text = "TimeZero to GPS"
        self.lbl_header = tk.Label(main_container, text=title_text, font=('Arial', 12, 'bold'), 
                                   fg="#000000", wraplength=500, justify="center")
        self.lbl_header.pack(pady=(2, 5))

        # Description
        description_text = "Extract data from a TimeZero database (.tzdb) and write it to a .gps file that can be imported by Poseidon."
        self.lbl_desc = tk.Label(main_container, text=description_text, font=('Arial', 10, 'italic'), 
                                 fg="#333333", wraplength=500, justify="center")
        self.lbl_desc.pack(pady=(5, 10))

        # 1. CRUISE METADATA FRAME
        metadata_frame = tk.LabelFrame(main_container, text=" Metadata Inputs ", font=('Arial', 10, 'bold'), padx=15, pady=10)
        metadata_frame.pack(fill="x", padx=10, pady=5)

        inner_id_frame = tk.Frame(metadata_frame)
        inner_id_frame.pack(pady=5, expand=True)

        tk.Label(inner_id_frame, text="Vessel (e.g. 162):", font=('Arial', 9, 'bold')).pack(side="left", padx=(5, 2))
        self.ent_vessel = tk.Entry(inner_id_frame, width=8)
        self.ent_vessel.pack(side="left", padx=5)

        tk.Label(inner_id_frame, text="Cruise (e.g. 202601):", font=('Arial', 9, 'bold')).pack(side="left", padx=(10, 2))
        self.ent_cruise = tk.Entry(inner_id_frame, width=10)
        self.ent_cruise.pack(side="left", padx=5)

        tk.Label(inner_id_frame, text="Haul (e.g. 99):", font=('Arial', 9, 'bold')).pack(side="left", padx=(10, 2))
        self.ent_haul = tk.Entry(inner_id_frame, width=8)
        self.ent_haul.pack(side="left", padx=5)

        # 2. TIME FILTERING FRAME
        time_frame = tk.LabelFrame(main_container, text=" Time Filtering (Alaska Time) ", font=('Arial', 10, 'bold'), padx=15, pady=10)
        time_frame.pack(fill="x", padx=10, pady=5)

        time_text = "Select the date/time range for the haul (OK to add time at the beginning/end)"
        self.lbl_time = tk.Label(time_frame, text=time_text, font=('Arial', 10, 'italic'), 
                                 fg="#333333", wraplength=500, justify="center")
        self.lbl_time.pack(pady=(5, 10))

        time_outer_frame = tk.Frame(time_frame)
        time_outer_frame.pack(expand=True)

        # Start Date Configuration Group
        start_group = tk.LabelFrame(time_outer_frame, text="Start", font=('Arial', 8, 'bold'), padx=10, pady=5)
        start_group.pack(side="left", padx=15)
        self.cal_start = DateEntry(start_group, width=12, background='darkblue', foreground='white')
        self.cal_start.pack(pady=2)
        self.time_start = tk.Entry(start_group, width=12, justify="center")
        self.time_start.insert(0, "14:30:00")
        self.time_start.pack(pady=2)

        # End Date Configuration Group
        end_group = tk.LabelFrame(time_outer_frame, text="End Time", font=('Arial', 8, 'bold'), padx=10, pady=5)
        end_group.pack(side="left", padx=15)
        self.cal_end = DateEntry(end_group, width=12, background='darkblue', foreground='white')
        self.cal_end.pack(pady=2)
        self.time_end = tk.Entry(end_group, width=12, justify="center")
        self.time_end.insert(0, "14:33:15")
        self.time_end.pack(pady=2)

        # 3. FILE SELECTION FRAME
        files_frame = tk.LabelFrame(main_container, text=" File Selection ", font=('Arial', 10, 'bold'), padx=15, pady=10)
        files_frame.pack(fill="x", padx=10, pady=5)

        files_text = " Note: Default path to the TimeZero database is C:/ProgramData/TimeZero/DATA/OwnShipRecorder.tzdb "
        self.files_text = tk.Label(files_frame, text=files_text, font=('Arial', 10, 'italic'), 
                                 fg="#333333", wraplength=500, justify="center")
        self.files_text.pack(pady=(5, 10))

        # Input File Layout
        tk.Label(files_frame, text="Input TimeZero Tracks Database (.tzdb):", font=('Arial', 9, 'bold')).pack(anchor="w")
        in_frame = tk.Frame(files_frame)
        in_frame.pack(pady=5, fill="x")
        self.path_in = tk.StringVar()
        tk.Entry(in_frame, textvariable=self.path_in).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(in_frame, text="Browse...", width=10, command=self.browse_input).pack(side="right")

        # Output File Layout
        tk.Label(files_frame, text="Output GPS File (.gps; e.g. HAUL0099.gps):", font=('Arial', 9, 'bold')).pack(anchor="w", pady=(10, 0))
        out_frame = tk.Frame(files_frame)
        out_frame.pack(pady=5, fill="x")
        self.path_out = tk.StringVar()
        tk.Entry(out_frame, textvariable=self.path_out).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(out_frame, text="Browse...", width=10, command=self.browse_output).pack(side="right")

        # 4. ACTION BUTTONS FRAME
        button_frame = tk.Frame(main_container)
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="CONVERT DATA", bg="#2e7d32", fg="white", 
                  font=('Arial', 10, 'bold'), height=2, width=20, 
                  command=self.run_process).pack(side="left", padx=10)

        tk.Button(button_frame, text="CLEAR", bg="#c62828", fg="white", 
                  font=('Arial', 10, 'bold'), height=2, width=10, 
                  command=self.destroy).pack(side="left", padx=10)

    def browse_input(self):
        file = filedialog.askopenfilename(filetypes=[("TimeZero Database", "*.tzdb")])
        if file: self.path_in.set(file)

    def browse_output(self):
        file = filedialog.asksaveasfilename(defaultextension=".gps", filetypes=[("GPS file", "*.gps")])
        if file: self.path_out.set(file)

    def run_process(self):
        if not self.path_in.get() or not self.path_out.get():
            messagebox.showwarning("Missing Info", "Please select both input and output files.")
            return
            
        try:
            tz_ak = zoneinfo.ZoneInfo("America/Anchorage")
            s_dt_str = f"{self.cal_start.get_date()} {self.time_start.get()}"
            e_dt_str = f"{self.cal_end.get_date()} {self.time_end.get()}"
            
            start_dt = datetime.strptime(s_dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_ak)
            end_dt = datetime.strptime(e_dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_ak)

            count = convert_tzdb_to_gps(
                self.path_in.get(),
                self.path_out.get(),
                self.ent_vessel.get(),
                self.ent_cruise.get(),
                self.ent_haul.get(),
                start_dt,
                end_dt
            )
            
            messagebox.showinfo("Success", f"Done! {count} records written.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Data Engine Workspace")
    root.geometry("600x700")
    app = TZDBConverterGUI(root)
    app.pack(fill="both", expand=True)
    root.mainloop()