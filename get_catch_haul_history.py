import sqlite3
import pandas as pd
import numpy as np
import itertools
import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog

SETTINGS_FILE = "catch_gui_settings.txt"

def get_catch_haul_history_sqlite(db_path, survey, species_codes=None, years=None, station=None, grid_buffer=0):
    """
    Queries data from a SQLite database.
    Provides catch means and haul information.
    Sorts haul data by year, and catch data by cpue_kgkm2.
    """
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        return f"Database connection error: {str(e)}"
    
    # Target columns matching the R script subset selection
    columns = [
        "year", "srvy", "haul", "stratum", "station", "vessel_name", "vessel_id", 
        "date_time", "latitude_dd_start", "longitude_dd_start", "species_code", 
        "common_name", "scientific_name", "taxon_confidence", "cpue_kgkm2", 
        "cpue_nokm2", "weight_kg", "count", "bottom_temperature_c", 
        "surface_temperature_c", "depth_m", "distance_fished_km", "net_width_m", 
        "net_height_m", "area_swept_km2", "duration_hr"
    ]
    
    # 1. Initial extraction filtered by survey
    query = f"SELECT {', '.join(columns)} FROM public_data WHERE srvy = ?"
    query_params = (survey,)
    
    try:
        df_base = pd.read_sql_query(query, conn, params=query_params)
    except Exception as e:
        conn.close()
        return f"SQL Query Error: {str(e)}\nEnsure table 'public_data' exists with matching columns."
    conn.close()
    
    if df_base.empty:
        return "Your query returned 0 results."
        
    # Convert numeric Unix Epoch time to human-readable date/time string
    if 'date_time' in df_base.columns:
        df_base['date_time'] = pd.to_datetime(df_base['date_time'], unit='s', errors='coerce')
        df_base['date_time'] = df_base['date_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
    # 2. Filter by Years
    if years and len(years) > 0:
        df_base = df_base[df_base['year'].isin(years)]
    else:
        # Default: use the top 10 most recent years available
        unique_years = sorted(df_base['year'].dropna().unique(), reverse=True)[:10]
        df_base = df_base[df_base['year'].isin(unique_years)]
        
    if df_base.empty:
        return "Your query returned 0 results."

    # 3. Handle grid buffer & station processing
    df_p1 = df_base.copy()  # Duplicate array for total weight calculations (public_data1)
    
    # If buffer is 0, treat it as unbuffered station lookups
    if grid_buffer == 0 or grid_buffer is None or pd.isna(grid_buffer):
        df_base = df_base[df_base['station'] == station]
        df_p1 = df_p1[df_p1['station'] == station]
        
    # 4. Filter by Species Codes
    if species_codes and len(species_codes) > 0:
        df_base = df_base[df_base['species_code'].isin(species_codes)]
        
    if df_base.empty:
        return "Your query returned 0 results."
        
    # 5. Survey-specific transformations
    if survey in ["AI", "GOA"] and grid_buffer > 0:
        try:
            y = [int(x) for x in station.split('-')]
        except Exception:
            return "Invalid station format for AI/GOA. Expected format like '324-73'."
            
        # Generalized dynamic implementation of R's asymmetric step matrix logic
        B = int(grid_buffer)
        x1_vals = [y[0] + B - j for j in range(B)] + [y[0]] + [y[0] - B - j for j in range(B)]
        x2_vals = [y[1] + B - j for j in range(B)] + [y[1]] + [y[1] - B - j for j in range(B)]
        possible_stations = [f"{x1}-{x2}" for x1, x2 in itertools.product(x1_vals, x2_vals)]
        
        df_base = df_base[df_base['station'].isin(possible_stations)]
        df_p1 = df_p1[df_p1['station'].isin(possible_stations)]
        
        if df_base.empty:
            return "Your query returned 0 results."
            
        # Aggregate catch data
        catch = df_base.groupby(['haul', 'year', 'scientific_name', 'common_name', 'station'], as_index=False)[
            ['count', 'weight_kg', 'cpue_kgkm2', 'cpue_nokm2']
        ].sum()
        
    elif survey in ["EBS", "NBS", "BSS"]:
        catch_cols = ["year", "station", "scientific_name", "common_name", "count", "weight_kg", "cpue_kgkm2", "cpue_nokm2"]
        catch = df_base[catch_cols].copy()
    else:
        catch = df_base[["year", "station", "scientific_name", "common_name", "count", "weight_kg", "cpue_kgkm2", "cpue_nokm2"]].copy()

    # Extract Haul metadata
    haul_cols = ["year", "haul", "station", "stratum", "vessel_name", "date_time", 
                 "latitude_dd_start", "longitude_dd_start", "bottom_temperature_c", 
                 "surface_temperature_c", "depth_m", "distance_fished_km", 
                 "net_width_m", "net_height_m", "area_swept_km2", "duration_hr"]
    haul = df_base[haul_cols].drop_duplicates()

    if catch.empty:
        return "Your query returned 0 results."

    # 6. Append total catch weight to haul metrics
    p1_agg = df_p1.groupby(['year', 'station'], as_index=False)['weight_kg'].sum()
    p1_agg.rename(columns={'weight_kg': 'total_weight_kg'}, inplace=True)
    p1_agg['total_weight_kg'] = p1_agg['total_weight_kg'].round(2)
    haul = pd.merge(haul, p1_agg, on=['year', 'station'], how='inner')
    
    # Sort Haul data by year (most recent first)
    haul = haul.sort_values(by='year', ascending=False).reset_index(drop=True)
    
    # Final catch manipulations & sorting catch by cpue_kgkm2 descending
    catch['year'] = catch['year'].astype(int)
    catch = catch.sort_values(by='cpue_kgkm2', ascending=False).reset_index(drop=True)
    catch['count'] = catch['count'].replace(0, np.nan)
    
    # Separate data into yearly dictionary tabs (sorting each tab by cpue_kgkm2 descending)
    cc = {}
    for yr, group in catch.groupby('year'):
        sorted_group = group.sort_values(by='cpue_kgkm2', ascending=False)
        cc[int(yr)] = sorted_group.drop(columns=['year']).reset_index(drop=True)
        
    # 7. Generate Catch Means (Unconditional execution)
    freq_temp = catch['scientific_name'].value_counts().reset_index()
    freq_temp.columns = ['scientific_name', 'Freq']
    
    catch_means = catch.groupby(['scientific_name', 'common_name', 'station'], as_index=False)[
        ['count', 'weight_kg', 'cpue_kgkm2', 'cpue_nokm2']
    ].mean()
    
    catch_means = pd.merge(catch_means, freq_temp, on='scientific_name', how='inner')
    
    if catch_means.empty:
        catch_means_out = "There was no data available for these function parameters"
    else:
        catch_means = catch_means.sort_values(by='cpue_kgkm2', ascending=False).reset_index(drop=True)
        catch_means['count'] = catch_means['count'].round(1)
        catch_means['weight_kg'] = catch_means['weight_kg'].round(2)
        catch_means['cpue_kgkm2'] = catch_means['cpue_kgkm2'].round(2)
        catch_means['cpue_nokm2'] = catch_means['cpue_nokm2'].round(2)
        catch_means_out = catch_means
        
    catch['weight_kg'] = catch['weight_kg'].round(2)
    catch['cpue_kgkm2'] = catch['cpue_kgkm2'].round(2)
    catch['cpue_nokm2'] = catch['cpue_nokm2'].round(2)
    
    return {
        "catch_yearly": cc,
        "catch_means": catch_means_out,
        "haul": haul,
        "raw_query": query,
        "raw_params": query_params
    }


class CatchHistoryGUI(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Grid Configuration for main workspace scaling
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Input parameters frame
        input_frame = ttk.LabelFrame(self, text=" Query Parameters ", padding=15)
        input_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # Load default database path from settings file if it exists
        initial_db_path = r"C:\Users\fpc.survey\Documents\RACE_Survey_App\Manuals\gaptools\public_data.sqlite"
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved_path = f.read().strip()
                    if saved_path:
                        initial_db_path = saved_path
            except Exception:
                pass

        # Database Path Selection
        ttk.Label(input_frame, text="SQLite Database Path:").grid(row=0, column=0, sticky="w", pady=3)
        self.db_var = tk.StringVar(value=initial_db_path)
        self.db_entry = ttk.Entry(input_frame, textvariable=self.db_var)
        self.db_entry.grid(row=0, column=1, sticky="ew", padx=(0,5), pady=3)
        
        # Action Buttons for Database Row
        db_btn_frame = ttk.Frame(input_frame)
        db_btn_frame.grid(row=0, column=2, sticky="w")
        ttk.Button(db_btn_frame, text="Browse...", command=self.browse_db).pack(side="left", padx=2)
        ttk.Button(db_btn_frame, text="Set as Default", command=self.save_default_db).pack(side="left", padx=2)

        # Survey Selection Dropdown
        ttk.Label(input_frame, text="Survey:").grid(row=1, column=0, sticky="w", pady=3)
        self.survey_var = tk.StringVar(value="AI")
        self.survey_combo = ttk.Combobox(input_frame, textvariable=self.survey_var, values=["AI", "GOA", "EBS", "NBS", "BSS"], state="readonly")
        self.survey_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=3)
        
        # Station Code
        ttk.Label(input_frame, text="Station Name (e.g. 324-73, B-12):").grid(row=2, column=0, sticky="w", pady=3)
        self.station_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.station_var).grid(row=2, column=1, columnspan=2, sticky="ew", pady=3)
        
        # Species Codes
        ttk.Label(input_frame, text="Species Code(s) [Comma separated / Blank for All]:").grid(row=3, column=0, sticky="w", pady=3)
        self.species_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.species_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=3)
        
        # Years Array / Ranges
        ttk.Label(input_frame, text="Year(s) [range or comma separated: 2010-2024 or 2018, 2021]:").grid(row=4, column=0, sticky="w", pady=3)
        self.years_var = tk.StringVar(value="1982-2025")
        ttk.Entry(input_frame, textvariable=self.years_var).grid(row=4, column=1, columnspan=2, sticky="ew", pady=3)
        
        # Grid Buffer Dropdown
        ttk.Label(input_frame, text="Grid Buffer (# stations; 0 for BSS/NBS/EBS):").grid(row=5, column=0, sticky="w", pady=3)
        self.buffer_var = tk.StringVar(value="0")
        self.buffer_combo = ttk.Combobox(input_frame, textvariable=self.buffer_var, values=["0", "1", "2", "3", "4", "5"], state="readonly")
        self.buffer_combo.grid(row=5, column=1, columnspan=2, sticky="ew", pady=3)
        
        # Action Button Frame
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10)
        
        self.run_excel_btn = ttk.Button(btn_frame, text="Execute & Export Spreadsheet", command=lambda: self.run_analysis(export_excel=True))
        self.run_excel_btn.pack(side="left", padx=10)
        
        self.run_console_btn = ttk.Button(btn_frame, text="Execute & Print Only", command=lambda: self.run_analysis(export_excel=False))
        self.run_console_btn.pack(side="left", padx=10)
        
        # Output Text Area Window
        output_frame = ttk.LabelFrame(self, text=" Live Console Summary Window ", padding=10)
        output_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.text_box = tk.Text(output_frame, wrap="none", font=("Consolas", 10))
        self.text_box.grid(row=0, column=0, sticky="nsew")
        
        # Add a scrollbar to the text area
        ysb = ttk.Scrollbar(output_frame, orient="vertical", command=self.text_box.yview)
        xsb = ttk.Scrollbar(output_frame, orient="horizontal", command=self.text_box.xview)
        self.text_box.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

    def browse_db(self):
        filename = filedialog.askopenfilename(filetypes=[("SQLite Files", "*.db *.sqlite *.sqlite3"), ("All Files", "*.*")])
        if filename:
            self.db_var.set(filename)

    def save_default_db(self):
        """Saves the current database path into the settings text file."""
        path_to_save = self.db_var.get().strip()
        self.text_box.delete("1.0", tk.END)
        try:
            with open(SETTINGS_FILE, "w") as f:
                f.write(path_to_save)
            self.text_box.insert(tk.END, f"SYSTEM CONFIGURATION LOG:\nSuccessfully saved custom fallback database path as local system default:\n--> {path_to_save}\n")
        except Exception as e:
            self.text_box.insert(tk.END, f"CRITICAL SETTINGS ERROR: Could not commit file mapping metadata to disk: {str(e)}\n")

    def reset_inputs(self):
        """Resets all query entry configurations back to safe initial parameters."""
        self.survey_var.set("AI")
        self.station_var.set("")
        self.species_var.set("")
        self.years_var.set("1982-2025")
        self.buffer_var.set("0")

    def run_analysis(self, export_excel=True):
        self.text_box.delete("1.0", tk.END)
        db_path = self.db_var.get().strip()
        survey = self.survey_var.get().strip()
        station = self.station_var.get().strip()
        grid_buffer = int(self.buffer_var.get())
        
        if not os.path.exists(db_path):
            self.text_box.insert(tk.END, f"CRITICAL ERROR: Target SQLite file not found at: {db_path}\n")
            return
        if not station:
            self.text_box.insert(tk.END, "CRITICAL ERROR: Station Identifier is required.\n")
            return

        # Specific Validation Constraint Rule Check
        if survey in ["BSS", "NBS", "EBS"] and grid_buffer != 0:
            self.text_box.insert(tk.END, f"VALIDATION ERROR: For regional survey '{survey}', the Grid Buffer must be set to 0.\n")
            return

        # Parsing input fields
        try:
            sp_input = self.species_var.get().strip()
            species_codes = [int(x.strip()) for x in sp_input.split(',')] if sp_input else None
            
            # Smart parsing loop logic for mixed lists and range expressions (e.g., "2010-2015, 2018")
            yr_input = self.years_var.get().strip()
            years = []
            if yr_input:
                for part in yr_input.split(','):
                    part = part.strip()
                    if '-' in part:
                        range_bounds = part.split('-')
                        start_year = int(range_bounds[0].strip())
                        end_year = int(range_bounds[1].strip())
                        years.extend(list(range(start_year, end_year + 1)))
                    else:
                        years.append(int(part))
            else:
                years = None
        except ValueError:
            self.text_box.insert(tk.END, "PARSE ERROR: Check numeric formats. Species must be comma-separated integers. Years must be comma-separated integers or valid hyphenated ranges (e.g., 2010-2024).\n")
            return

        # Core data extraction execution
        results = get_catch_haul_history_sqlite(db_path, survey, species_codes, years, station, grid_buffer)
        
        if isinstance(results, str):
            self.text_box.insert(tk.END, results)
            return

        self.print_summary_to_box(results)

        if export_excel:
            export_filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if not export_filename:
                return # Canceled by user
                
            try:
                with pd.ExcelWriter(export_filename, engine='openpyxl') as writer:
                    results['haul'].to_excel(writer, sheet_name='haul', index=False)
                    
                    if isinstance(results['catch_means'], pd.DataFrame):
                        results['catch_means'].to_excel(writer, sheet_name='catch_means', index=False)
                    else:
                        pd.DataFrame([{"Summary Message": results['catch_means']}]).to_excel(writer, sheet_name='catch_means', index=False)
                    
                    for year, df_yr in results['catch_yearly'].items():
                        df_yr.to_excel(writer, sheet_name=f'catch_{year}', index=False)
                
                self.text_box.insert(tk.END, f"\n>>> Spreadsheet successfully saved to: {export_filename}\n")
                    
            except Exception as e:
                self.text_box.insert(tk.END, f"\nEXPORT ERROR: Failed to build Excel spreadsheet: {str(e)}\n")
                return

        # Clean environment and wipe variables once processing loop finishes successfully
        self.reset_inputs()

    def print_summary_to_box(self, results):
        summary_str = "=== RESULTS ===\n\n"
        summary_str += f"Haul Entries Processed (Sorted by Year): {len(results['haul'])} records.\n"
        if isinstance(results['catch_means'], pd.DataFrame):
            summary_str += f"Catch Means Processed (Sorted by CPUE): {len(results['catch_means'])} entries.\n"
        else:
            summary_str += f"Catch Means: {results['catch_means']}\n"
        summary_str += f"Retrieved data for years: {list(results['catch_yearly'].keys())}\n\n"
        
        summary_str += "--- HAUL DATA (Sorted by Year) ---\n"
        summary_str += results['haul'].to_string() + "\n\n"
        
        if isinstance(results['catch_means'], pd.DataFrame):
            summary_str += "--- MEAN CATCH (Sorted by CPUE) ---\n"
            summary_str += results['catch_means'].to_string() + "\n"
            
        self.text_box.insert(tk.END, summary_str)