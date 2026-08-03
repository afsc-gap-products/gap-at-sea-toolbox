import tkinter as tk
from tkinter import ttk
import webbrowser

class AboutWidget(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        container = tk.Frame(self, padx=25, pady=25)
        container.pack(fill="both", expand=True)

        # 1. TITLE
        tk.Label(
            container, 
            text="Groundfish Assessment Program (GAP) Toolbox", 
            font=('Arial', 14, 'bold'),
            justify="center"
        ).pack(pady=(10, 5))

        # 2. OVERVIEW
        desc_text = (
            "Operations and data utilities designed for GAP survey operations. "
        )
        tk.Label(
            container, 
            text=desc_text, 
            font=('Arial', 10, 'italic'),
            wraplength=550,
            justify="center",
            fg="#333333"
        ).pack(pady=(0, 20))

        ttk.Separator(container, orient='horizontal').pack(fill='x', pady=10)

        # 3. METADATA & SYSTEM INFORMATION FRAME
        info_frame = tk.LabelFrame(
            container, 
            text=" Application Deployment Details ", 
            font=('Arial', 10, 'bold'), 
            padx=20, 
            pady=15
        )
        info_frame.pack(fill="x", padx=10, pady=15)

        details = [
            ("Version:", "0.0.7"),
            ("Last Updated:", "August 8, 2026"),
            ("Primary Contact:", "Sean Rohan"),
            ("Email Support:", "sean.rohan@noaa.gov")
        ]

        for idx, (label_text, value_text) in enumerate(details):
            tk.Label(
                info_frame, 
                text=label_text, 
                font=('Arial', 9, 'bold'), 
                anchor="w"
            ).grid(row=idx, column=0, sticky="w", pady=5, padx=(0, 15))
            
            # Text Values
            if "@" in value_text:
                lbl_val = tk.Label(
                    info_frame, 
                    text=value_text, 
                    font=('Arial', 9, 'underline'), 
                    fg="#1565c0", 
                    anchor="w",
                    cursor="hand2"
                )
                lbl_val.bind("<Button-1>", lambda e, email=value_text: webbrowser.open(f"mailto:{email}"))
            else:
                lbl_val = tk.Label(
                    info_frame, 
                    text=value_text, 
                    font=('Arial', 9), 
                    anchor="w"
                )
            lbl_val.grid(row=idx, column=1, sticky="w", pady=5)

        tk.Label(
            container, 
            text="NOAA Fisheries/AFSC/RACE Groundfish Assessment Program", 
            font=('Arial', 8), 
            fg="gray"
        ).pack(side="bottom", pady=(20, 0))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("App Hub Workspace Launcher")
    root.geometry("620x450")
    
    app = AboutWidget(root)
    app.pack(fill="both", expand=True)
    
    root.mainloop()