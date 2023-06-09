import sys
import pandas as pd
import os
# import sqlite3 Reminder that a future option could be to read-in a SQLite database...
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QAbstractItemView, QLineEdit, QToolBar, QComboBox, QSlider, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDesktopServices, QFont
from PyQt6.QtCore import Qt, QUrl, QModelIndex




class surveyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Survey App Resources")
        self.resize(800, 600)

        self.model = QStandardItemModel()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(
            ["Name", "Description", "Location"])

        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)
        self.table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        toolbar = QToolBar(self)
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search_bar)

        self.search_mode_combo = QComboBox(self)
        self.search_mode_combo.addItem("All Fields")
        self.search_mode_combo.addItem("Name")
        self.search_mode_combo.addItem("Description")
        self.search_mode_combo.addItem("Location")
        self.search_mode_combo.addItem("Last Update")
        toolbar.addWidget(self.search_mode_combo)

        font_size_slider_label = QLabel('Font Size: ')
        font_size_slider = QSlider(Qt.Orientation.Horizontal)
        font_size_slider.setMinimum(10)
        font_size_slider.setMaximum(30)
        font_size_slider.setValue(12)
        font_size_slider.setTickInterval(2)
        font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        font_size_slider.valueChanged.connect(self.update_font_size)

        self.filepath_survey_app_label = QLabel('Survey App Directory: ')
        self.filepath_survey_app = 'G:/RACE_Survey_App'
        self.survey_app_bar = QLineEdit()
        self.survey_app_bar.setText('G:/RACE_Survey_App')
        self.survey_app_bar.textChanged.connect(self.update_filepath)
    
        bottom_right_layout = QHBoxLayout()
        bottom_right_layout.addWidget(self.filepath_survey_app_label) 
        bottom_right_layout.addWidget(self.survey_app_bar)
        bottom_right_layout.addStretch()
        bottom_right_layout.addWidget(font_size_slider_label)
        bottom_right_layout.addWidget(font_size_slider)

        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.table_view)
        main_layout.addLayout(bottom_right_layout)
        # main_layout.addLayout(self.survey_app_bar)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.populate_list()
        self.setup_table()

        self.table_view.doubleClicked.connect(self.open_item)

        self.filter_mode = 0  # All Fields

    def setup_table(self):
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.table_view.setColumnWidth(0, 300)
        self.table_view.setColumnWidth(1, 300)
        self.table_view.setColumnWidth(2, 200)

    # Future method to read data in from a csv file
    def populate_list(self):
        data = pd.read_csv('./inst/survey_app_data_gaptools_minimal.csv', usecols=['widget_title', 'widget_description', 'url_loc'])

        # Define the custom column names
        column_names = ['Name', 'Description', 'Location']
        self.model.setHorizontalHeaderLabels(column_names)

        for index, row in data.iterrows():
            name = row['widget_title']
            description = row['widget_description']
            location = row['url_loc']

            name_item = QStandardItem(name)
            description_item = QStandardItem(str(description))
            location_item = QStandardItem(location)

            self.model.appendRow([name_item, description_item, location_item])

    def open_item(self, index: QModelIndex):
        row = index.row()  # Get the row index of the double-clicked item
        column = 2  # Assuming the desired column index is 3

        item = self.model.item(row, column)  # Retrieve the item from the specified row and column

        if item is None:
            return  # Handle the case when the item does not exist

        location = item.text()  # Get the path from the item's text

        # Open the file using the default program for the file type
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(self.filepath_survey_app, location)))

    def update_filepath(self):
        self.filepath_survey_app = self.survey_app_bar.text()

    def filter_data(self, text):
        self.table_view.reset()
        if text == "":
            self.table_view.setRowHidden(-1, False)
        else:
            for row in range(self.model.rowCount()):
                hidden = True
                for column in range(self.model.columnCount()):
                    item = self.model.item(row, column)
                    if text.lower() in item.text().lower():
                        hidden = False
                        break
                self.table_view.setRowHidden(row, hidden)

    def update_font_size(self, value):
        font = self.table_view.font()
        font.setPointSize(value)
        self.table_view.setFont(font)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus:
                self.increase_font_size()
                event.accept()
            elif event.key() == Qt.Key.Key_Minus:
                self.decrease_font_size()
                event.accept()

    def increase_font_size(self):
        font = self.table_view.font()
        font_size = font.pointSize()
        if font_size < 30:
            font_size += 1
            font.setPointSize(font_size)
            self.table_view.setFont(font)

    def decrease_font_size(self):
        font = self.table_view.font()
        font_size = font.pointSize()
        if font_size > 10:
            font_size -= 1
            font.setPointSize(font_size)
            self.table_view.setFont(font)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
