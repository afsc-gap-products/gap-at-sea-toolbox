import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import numpy as np
import math

def astrocalc_python(day, month, year, hour, timezone, lat, lon):
    """
    Python port of astrcalc4r. Calculates solar variables based on 
    Jacobson et al. (2011).
    """
    deg2rad = np.pi / 180.0
    
    # Julian Day Calculation
    mm = month
    if mm <= 2:
        month += 12
        year -= 1
    
    xa = math.floor(year / 100)
    xb = 2 - xa + math.floor(xa / 4)
    xd = day + hour / 24.0
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + xd + xb - 1524.5
    
    jc = (jd - 2451545) / 36525
    
    # Geometric Mean Longitude Sun
    gmls = (280.46646 + 36000.76983 * jc + 0.0003032 * (jc**2)) % 360
    # Geometric Mean Anomaly Sun
    gmas = (357.52911 + 35999.05029 * jc - 0.0001537 * (jc**2)) % 360
    # Eccentricity Earth Orbit
    eeo = 0.016708634 - 0.000042037 * jc - 0.0000001267 * (jc**2)
    
    # Sun Equation of Center
    scx = (1.914602 - 0.004817 * jc - 0.000014 * (jc**2)) * np.sin(gmas * deg2rad) + \
          (0.019993 - 0.000101 * jc) * np.sin(2 * gmas * deg2rad) + \
          0.000289 * np.sin(3 * gmas * deg2rad)
    
    stl = gmls + scx
    sta = gmas + scx
    
    omega = 125.04 - 1934.136 * jc
    lambda_sun = stl - 0.00569 - 0.00478 * np.sin(omega * deg2rad)
    
    # Obliquity
    epsilon = (23 + 26/60 + 21.448/3600) - (46.815/3600) * jc - \
              (0.00059/3600) * (jc**2) + (0.001813/3600) * (jc**3)
    epsilon += 0.00256 * np.cos(omega * deg2rad)
    
    # Declination
    declin = np.arcsin(np.sin(epsilon * deg2rad) * np.sin(lambda_sun * deg2rad)) / deg2rad
    
    # Equation of Time
    y = np.tan(epsilon * deg2rad / 2)**2
    eqtime = (y * np.sin(2 * gmls * deg2rad) - 2 * eeo * np.sin(gmas * deg2rad) + 
              4 * eeo * y * np.sin(gmas * deg2rad) * np.cos(2 * gmls * deg2rad) - 
              0.5 * (y**2) * np.sin(4 * gmls * deg2rad) - 
              1.25 * (eeo**2) * np.sin(2 * gmas * deg2rad)) / deg2rad * 4
    
    # Sunrise/Sunset
    h0 = -0.8333 * deg2rad
    phi = lat * deg2rad
    
    # Hour Angle
    try:
        cos_hangle = (np.sin(h0) - np.sin(declin * deg2rad) * np.sin(phi)) / (np.cos(declin * deg2rad) * np.cos(phi))
        if cos_hangle > 1 or cos_hangle < -1:
            return None, None # Polar day/night
        hangle = np.arccos(cos_hangle) / deg2rad
    except:
        return None, None

    noon = (720 - 4 * lon + timezone * 60 - eqtime) / 1440.0
    sunrise_dec = (noon * 1440 - hangle * 4) / 1440.0 * 24.0
    sunset_dec = (noon * 1440 + hangle * 4) / 1440.0 * 24.0
    
    return sunrise_dec, sunset_dec

def parse_lat_lon(value):
    """Converts 'D MM.M' string or decimal number to float."""
    if isinstance(value, str) and " " in value.strip():
        parts = value.split()
        deg = float(parts[0])
        minutes = float(parts[1]) / 60.0
        return deg + (minutes if deg >= 0 else -minutes)
    return float(value)

def format_decimal_to_time(decimal_hour, base_date, tz_offset):
    """Converts decimal hours to a datetime object with timezone offset."""
    if decimal_hour is None:
        return "Polar Day/Night"
    
    # Adjust decimal hour if it falls outside 0-24
    decimal_hour = decimal_hour % 24
    
    hours = int(decimal_hour)
    minutes = int((decimal_hour % 1) * 60)
    seconds = int(((decimal_hour % 1) * 60 % 1) * 60)
    
    # Construct timestamp in UTC, then shift by the offset used in calculation
    dt = datetime(base_date.year, base_date.month, base_date.day, hours, minutes, seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# --- GUI CLASS FOR INTEGRATION ---

class SunriseSunsetGUI(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Main Container
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Sunrise & Sunset Calculator", font=("Arial", 14, "bold")).pack(pady=10)

        # Form Frame
        form = tk.Frame(main_frame)
        form.pack(pady=10)

        # Date Entry
        tk.Label(form, text="Date (YYYY-MM-DD):", width=20, anchor="e").grid(row=0, column=0, padx=5, pady=5)
        self.ent_date = tk.Entry(form, width=15)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        # --- Latitude Row ---
        tk.Label(form, text="Latitude:", width=20, anchor="e").grid(row=1, column=0, padx=5, pady=5)
        self.lat_deg = tk.Entry(form, width=5)
        self.lat_deg.grid(row=1, column=1, padx=2)
        tk.Label(form, text="°").grid(row=1, column=2)
        
        self.lat_min = tk.Entry(form, width=8)
        self.lat_min.grid(row=1, column=3, padx=2)
        tk.Label(form, text="'").grid(row=1, column=4)

        self.lat_dir = tk.StringVar(value="N")
        self.lat_menu = tk.OptionMenu(form, self.lat_dir, "N", "S")
        self.lat_menu.grid(row=1, column=5, padx=5)

        # --- Longitude Row ---
        tk.Label(form, text="Longitude:", width=20, anchor="e").grid(row=2, column=0, padx=5, pady=5)
        self.lon_deg = tk.Entry(form, width=5)
        self.lon_deg.grid(row=2, column=1, padx=2)
        tk.Label(form, text="°").grid(row=2, column=2)
        
        self.lon_min = tk.Entry(form, width=8)
        self.lon_min.grid(row=2, column=3, padx=2)
        tk.Label(form, text="'").grid(row=2, column=4)

        self.lon_dir = tk.StringVar(value="W")
        self.lon_menu = tk.OptionMenu(form, self.lon_dir, "E", "W")
        self.lon_menu.grid(row=2, column=5, padx=5)

        # Timezone
        tk.Label(form, text="Timezone:", width=20, anchor="e").grid(row=3, column=0, padx=5, pady=5)
        self.tz_var = tk.StringVar(value="US/Alaska")
        tz_dropdown = tk.OptionMenu(form, self.tz_var, "US/Alaska", "US/Aleutian")
        tz_dropdown.grid(row=3, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        # Calculate Button
        tk.Button(main_frame, text="Get Times", command=self.calculate, 
                  bg="#1976d2", fg="white", width=20, height=2).pack(pady=20)

        # Results Area
        self.res_label = tk.Label(main_frame, text="", font=("Courier", 10), justify="left", 
                                  bg="#f5f5f5", relief="sunken", padx=10, pady=10)
        self.res_label.pack(fill="x", pady=10)

    def get_decimal_coords(self):
        """Helper to convert Deg/Min/Dir to Decimal Degrees"""
        try:
            # Latitude Calculation
            l_deg = float(self.lat_deg.get() or 0)
            l_min = float(self.lat_min.get() or 0) / 60.0
            lat_dec = l_deg + l_min
            if self.lat_dir.get() == "S":
                lat_dec *= -1
            
            # Longitude Calculation
            o_deg = float(self.lon_deg.get() or 0)
            o_min = float(self.lon_min.get() or 0) / 60.0
            lon_dec = o_deg + o_min
            if self.lon_dir.get() == "W":
                lon_dec *= -1
                
            return lat_dec, lon_dec
        except ValueError:
            raise ValueError("Degrees and Minutes must be numeric.")

    def calculate(self):
        try:
            date_str = self.ent_date.get()
            chosen_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Convert D/M/Dir to Decimal for the math function
            lat, lon = self.get_decimal_coords()
            
            sel_tz = -8 if self.tz_var.get() == "US/Alaska" else -9
            
            sr_dec, ss_dec = astrocalc_python(
                day=chosen_date.day,
                month=chosen_date.month,
                year=chosen_date.year,
                hour=12.0,
                timezone=sel_tz,
                lat=lat,
                lon=lon
            )

            if sr_dec is None:
                messagebox.showwarning("Polar Condition", "The sun does not rise/set at this location.")
                return

            sunrise_str = format_decimal_to_time(sr_dec, chosen_date, sel_tz)
            sunset_str = format_decimal_to_time(ss_dec, chosen_date, sel_tz)

            result_text = (f"Results for {date_str}:\n"
                           f"Coord: {abs(lat):.3f}°{self.lat_dir.get()}, {abs(lon):.3f}°{self.lon_dir.get()}\n"
                           f"---------------------------\n"
                           f"Sunrise: {sunrise_str} {self.tz_var.get()}\n"
                           f"Sunset:  {sunset_str} {self.tz_var.get()}")
            
            self.res_label.config(text=result_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {e}")