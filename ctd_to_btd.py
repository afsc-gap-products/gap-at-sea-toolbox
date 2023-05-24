import os
import subprocess
import sqlite3
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QMessageBox)
from datetime import datetime
import pandas as pd
import numpy as np


class CtdToBtdWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convert CTD to BTD")
        self.setGeometry(100, 100, 450, 300)

        self.label_hex = QLabel("CTD binary data file (.hex):")
        self.line_hex = QLineEdit()
        self.button_hex = QPushButton("Browse")

        self.label_xmlcon = QLabel("CTD configuration file (.xmlcon):")
        self.line_xmlcon = QLineEdit()
        self.button_xmlcon = QPushButton("Browse")

        self.label_output_dir = QLabel("Output folder:")
        self.line_output_dir = QLineEdit()
        self.button_output_dir = QPushButton("Browse")

        self.label_vessel = QLabel("Vessel Number (e.g. 162):")
        self.line_vessel = QLineEdit()

        self.label_cruise = QLabel("Cruise Number (e.g. 202401):")
        self.line_cruise = QLineEdit()

        self.label_haul = QLabel("Haul Number (e.g. 24):")
        self.line_haul = QLineEdit()

        self.label_psa = QLabel(
            "Data Conversion PSA file (default path pre-filled)")
        self.line_psa = QLineEdit()
        self.line_psa.setText("C:/CTD/assets/DatCnv.psa")
        self.button_psa = QPushButton("Browse")

        self.label_bat = QLabel("Batch file (default path pre-filled)")
        self.line_bat = QLineEdit()
        self.line_psa.setText("C:/CTD/assets/getdata.bat")
        self.button_bat = QPushButton("Browse")

        self.submit_button = QPushButton("Convert")
        self.exit_button = QPushButton("Close")

        layout = QVBoxLayout()

        layouts = [
            (self.line_hex, self.button_hex),
            (self.line_xmlcon, self.button_xmlcon),
            (self.line_output_dir, self.button_output_dir),
            (self.line_vessel,),
            (self.line_cruise,),
            (self.line_haul,),
            (self.line_psa, self.button_psa),
            (self.line_bat, self.button_bat),
            (self.submit_button, self.exit_button)
        ]

        labels = [self.label_hex, self.label_xmlcon, self.label_output_dir, self.label_vessel,
                  self.label_cruise, self.label_haul, self.label_psa, self.label_bat]

        for ii, items in enumerate(layouts):
            h_layout = QHBoxLayout()
            for item in items:
                h_layout.addWidget(item)
            layout.addWidget(labels[ii]) if ii < len(labels) else None
            layout.addLayout(h_layout)

        self.setLayout(layout)

        self.button_hex.clicked.connect(lambda: self.browse_file(
            file_filter="Hexadecimal File (*.hex)",
            attribute='line_hex'))
        self.button_xmlcon.clicked.connect(lambda: self.browse_file(
            file_filter="Configuration File (*.xmlcon)",
            attribute='line_xmlcon'))
        self.button_output_dir.clicked.connect(self.browse_output_dir)
        self.button_psa.clicked.connect(lambda: self.browse_file(
            file_filter="Program Setup File (*.psa)",
            attribute='line_psa'))
        self.button_bat.clicked.connect(
            lambda: self.browse_file(file_filter="Batch File (*.bat)",
                                     attribute='line_bat'))

        self.submit_button.clicked.connect(self.submit_files)
        self.exit_button.clicked.connect(self.close)
        # self.exit_button.clicked.connect(QApplication.quit)

    def browse_file(self, file_filter, attribute):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", file_filter)
        if filepath:
            getattr(self, attribute).setText(filepath)

    def browse_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory")
        if folder_path:
            self.line_output_dir.setText(folder_path)

    def check_file_exists(self, path, extension):
        if not os.path.exists(path):
            QMessageBox.critical(
                self, "Error", "No file found at the specified path({})".format(path), QMessageBox.StandardButton.Ok)
        if not path.lower().endswith(extension):
            QMessageBox.critical(
                self, "Error", "Selected {} file has the wrong file type ({}).".format(extension, path), QMessageBox.StandardButton.Ok)

    def check_dir_exists(self, path):
        if not os.path.exists(path):
            QMessageBox.critical(
                self, "Error", "Invalid output directory. {} does not exist.".format(path), QMessageBox.StandardButton.Ok)

    def check_file_created(self, path, silent=False):
        if not os.path.exists(path):
            QMessageBox.critical(
                self, "Error", "Error: {} not created.".format(path), QMessageBox.StandardButton.Ok)
        if not silent:
            QMessageBox.information(
                self, "File Created", "{} created!".format(path), QMessageBox.StandardButton.Ok)

    def extract_value(filepath, search_string):
        with open(filepath, 'r') as file:
            for line in file:
                if search_string in line:
                    first_value = line.split('=')[
                        1].strip().strip().split(' [')[0].strip()
                    return first_value
        raise ValueError(["{} not found in the file".format(search_string)])

    def open_text_file(filepath):
        with open(filepath, 'r') as file:
            # Find the line number that contains '*END*'
            end_line = next((i for i, line in enumerate(file)
                             if '*END*' in line), None)

        if end_line is not None:
            # Read the file, skipping rows up to '*END*'
            df = pd.read_csv(filepath, sep='\s+',
                             skiprows=end_line + 1, header=None)
        else:
            # If '*END*' is not found, read the entire file
            df = pd.read_csv(filepath, sep='\s+', header=None)
        return df

    def submit_files(self):
        filepath_hex = self.line_hex.text()
        filepath_xmlcon = self.line_xmlcon.text()
        filepath_output_dir = self.line_output_dir.text()
        filepath_psa = self.line_psa.text()
        filepath_bat = self.line_bat.text()
        vessel_str = self.line_vessel.text()
        cruise_str = self.line_cruise.text()
        haul_str = self.line_haul.text()

        # Check that vessel, cruise, and haul are provided
        if vessel_str == "" or cruise_str == "" or haul_str == "":
            error_message = "Please enter values for all fields."
            QMessageBox.critical(self, "Error", error_message,
                                 QMessageBox.StandardButton.Ok)

        # Check that file paths and extensions are valid
        self.check_file_exists(filepath_hex,
                               extension='.hex')

        self.check_file_exists(filepath_psa,
                               extension='.psa')

        self.check_file_exists(filepath_bat,
                               extension='.bat')

        self.check_file_exists(filepath_xmlcon,
                               extension='.xmlcon')

        self.check_dir_exists(filepath_output_dir)

        # Run SBE Data Processing to do the conversion
        cnv_filename = "{}_{}_{}.cnv".format(vessel_str, cruise_str, haul_str)
        cnv_output_filename = "{}/{}_{}_{}_raw.cnv".format(
            filepath_output_dir, vessel_str, cruise_str, haul_str)

        subprocess.run(['sbebatch', filepath_bat, filepath_hex,
                        filepath_xmlcon, filepath_output_dir, filepath_psa, cnv_filename, '_raw'])

        self.check_file_created(cnv_output_filename)

        # Extract data from cnv file
        SERIAL_NUMBER = extract_value(
            cnv_output_filename, "* Temperature SN = ")

        # Get start time
        btd_time_format = "%m/%d/%Y %H:%M:%S"

        start_time = datetime.strptime(extract_value(
            cnv_output_filename, "# start_time"), "%b %d %Y %H:%M:%S")

        # Use start time and scan times in seconds to calculate scan time
        cnv_data = open_text_file(cnv_output_filename)

        cnv_data = cnv_data.iloc[:, [0, 1, 2]].rename(
            columns={0: "Time", 1: "Depth", 2: "Temperature"})

        cnv_data = cnv_data.astype(float)
        cnv_data['Time'] = np.floor(cnv_data['Time'])
        cnv_data = cnv_data.set_index('Time').groupby(cnv_data['Time']).mean(
            numeric_only=True).reset_index()

        DT_OUT = start_time + pd.to_timedelta(cnv_data['Time'], unit='s')

        SCAN_TIME = (start_time + pd.to_timedelta(cnv_data['Time'], unit='s'))

        max_time = DT_OUT.max().strftime(btd_time_format)
        min_time = DT_OUT.min().strftime(btd_time_format)

        HOST_TIME = max_time
        LOGGER_TIME = max_time
        LOGGING_START = min_time
        LOGGING_END = max_time

        cnv_data['VESSEL'] = float(vessel_str)
        cnv_data['CRUISE'] = float(cruise_str)
        cnv_data['HAUL'] = float(haul_str)
        cnv_data['SERIAL_NUMBER'] = float(SERIAL_NUMBER)
        cnv_data['DATE_TIME'] = SCAN_TIME
        cnv_data['TEMPERATURE'] = cnv_data['Temperature']
        cnv_data['DEPTH'] = cnv_data['Depth']

        btd_data = cnv_data.drop(columns=['Time', 'Depth', 'Temperature'])

        # Defaults
        SAMPLE_PERIOD = 1
        NUMBER_CHANNELS = 2
        NUMBER_SAMPLES = btd_data[btd_data.columns[0]].count()
        MODE = 2

        bth_data = pd.DataFrame(
            {
                'VESSEL': [int(vessel_str)],
                'CRUISE': [int(cruise_str)],
                'HAUL': [int(haul_str)],
                'MODEL_NUMBER': [''],
                'VERSION_NUMBER': [''],
                'SERIAL_NUMBER': [int(SERIAL_NUMBER)],
                'HOST_TIME': [HOST_TIME],
                'LOGGER_TIME': [LOGGER_TIME],
                'LOGGING_START': [LOGGING_START],
                'LOGGING_END': [LOGGING_END],
                'SAMPLE_PERIOD': [SAMPLE_PERIOD],
                'NUMBER_CHANNELS': [NUMBER_CHANNELS],
                'NUMBER_SAMPLES': [int(NUMBER_SAMPLES)],
                'MODE': [MODE]
            }
        )

        # Write BTH and BTD files to output
        bth_path = "{}/HAUL{}.BTH".format(filepath_output_dir,
                                          haul_str.zfill(4))
        btd_path = "{}/HAUL{}.BTD".format(filepath_output_dir,
                                          haul_str.zfill(4))

        bth_data.to_csv(bth_path, index=False)
        btd_data.to_csv(btd_path, index=False)

        self.check_file_created(bth_path, silent=True)
        self.check_file_created(btd_path, silent=False)


class ChildWidget(QWidget):
    def __init__(self, widget_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(widget_name)
        self.layout = QVBoxLayout()
        self.exit_button = QPushButton("Exit")
        self.layout.addWidget(self.exit_button)
        self.setLayout(self.layout)

        self.exit_button.clicked.connect(self.close)
