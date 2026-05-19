import tkinter as tk
from tkinter import messagebox
from convert_tzdb_gps import TZDBConverterGUI
from convert_xml_btd import XMLToBTDConverterGUI
from convert_ctd_btd import CTDConverterGUI
from get_sunrise_sunset import SunriseSunsetGUI
from about_gaptools import AboutWidget

class ParentWidget(tk.Tk):
    widget_mapping = {
        "BT: Convert CTD Hex to BTD": CTDConverterGUI,
        "BT: Convert XML to BTD": XMLToBTDConverterGUI,
        "GPS: Convert TimeZero DB to GPS": TZDBConverterGUI,
        "Sunrise/Sunset": SunriseSunsetGUI,
        "About": AboutWidget
    }

    def __init__(self):
        super().__init__()

        self.title("GAP Toolbox")
        self.geometry("1000x700")

        # 1. Create a PanedWindow for the split layout
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4, bg="#cccccc")
        self.paned_window.pack(fill="both", expand=True)

        # 2. Left Sidebar Frame
        self.sidebar = tk.Frame(self.paned_window, width=250, padx=10, pady=10)
        self.paned_window.add(self.sidebar)

        self.title_label = tk.Label(self.sidebar, text="Tools:", font=("Arial", 11, "bold"))
        self.title_label.pack(pady=(0, 10), anchor="w")

        # Listbox for navigation
        self.listbox = tk.Listbox(self.sidebar, font=("Arial", 10), exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.open_selected_widget())

        self.submit_button = tk.Button(self.sidebar, text="Open Tool", command=self.open_selected_widget)
        self.submit_button.pack(fill="x", pady=(10, 0))

        # 3. Right Workspace Frame
        self.workspace = tk.Frame(self.paned_window, bg="white")
        self.paned_window.add(self.workspace)

        # Initialize listbox content
        self.original_widget_names = list(self.widget_mapping.keys())
        for name in self.original_widget_names:
            self.listbox.insert(tk.END, name)

    def open_selected_widget(self):
        """Clears the workspace and loads the new tool frame."""
        selection = self.listbox.curselection()
        if not selection:
            return

        widget_name = self.listbox.get(selection[0])
        widget_class = self.widget_mapping.get(widget_name)

        # Clear existing tool from workspace
        for widget in self.workspace.winfo_children():
            widget.destroy()

        if widget_class:
            try:
                # Instantiate tool inside the workspace frame
                current_tool = widget_class(self.workspace)
                current_tool.pack(fill="both", expand=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load {widget_name}: {e}")
        else:
            lbl = tk.Label(self.workspace, text=f"{widget_name}\n(Not yet implemented)", 
                           bg="white", font=("Arial", 14))
            lbl.pack(expand=True)

if __name__ == '__main__':
    app = ParentWidget()
    app.mainloop()
