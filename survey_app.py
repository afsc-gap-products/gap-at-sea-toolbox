import sys
# import sqlite3 Reminder that a future option could be to read-in a SQLite database...
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QAbstractItemView, QLineEdit, QToolBar, QComboBox, QSlider, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDesktopServices, QFont
from PyQt6.QtCore import Qt, QUrl, QModelIndex


class surveyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Explorer")
        self.resize(800, 600)

        self.model = QStandardItemModel()
        self.model.setColumnCount(4)
        self.model.setHorizontalHeaderLabels(
            ["Name", "Description", "Location", "Last Update"])

        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)
        self.table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
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

        font_size_slider = QSlider(Qt.Orientation.Horizontal)
        font_size_slider.setMinimum(10)
        font_size_slider.setMaximum(30)
        font_size_slider.setValue(12)
        font_size_slider.setTickInterval(2)
        font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        font_size_slider.valueChanged.connect(self.update_font_size)

        bottom_right_layout = QHBoxLayout()
        bottom_right_layout.addStretch()
        bottom_right_layout.addWidget(font_size_slider)

        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.table_view)
        main_layout.addLayout(bottom_right_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.populate_list()
        self.setup_table()

        self.table_view.doubleClicked.connect(self.open_item)

        self.filter_mode = 0  # All Fields

    def setup_table(self):
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(3, 150)

    def populate_list(self):
        sample_data = [
            ("Folder 1", "Folder 1 Description", "C:/Users", "2023-05-20"),
            ("File 1", "File 1 Description", "C:/Users/example.txt", "2023-05-21"),
            ("Folder 2", "Folder 2 Description", "C:/Program Files", "2023-05-22"),
            ("File 2", "File 2 Description",
             "C:/Program Files/example.exe", "2023-05-23")
        ]

        for name, description, location, last_update in sample_data:
            name_item = QStandardItem(name)
            description_item = QStandardItem(description)
            location_item = QStandardItem(location)
            last_update_item = QStandardItem(last_update)

            self.model.appendRow(
                [name_item, description_item, location_item, last_update_item])

    # Future method to read data in from a csv file
    # def populate_list(self):
    #     with open('data.csv', 'r', newline='') as file:
    #         reader = csv.reader(file)
    #         header = next(reader)  # Read the header row
    #         self.model.setHorizontalHeaderLabels(header)

    #         for row in reader:
    #             name = row[0]
    #             description = row[1]
    #             location = row[2]
    #             last_update = row[3]

    #             name_item = QStandardItem(name)
    #             description_item = QStandardItem(description)
    #             location_item = QStandardItem(location)
    #             last_update_item = QStandardItem(last_update)

    #             self.model.appendRow(
    #                 [name_item, description_item, location_item, last_update_item])

    # Or read from a SQLite database
    # def populate_list(self):
    #     connection = sqlite3.connect('database.db')
    #     cursor = connection.cursor()

    #     cursor.execute("SELECT name, description, location, last_update FROM items")
    #     rows = cursor.fetchall()

    #     for row in rows:
    #         name = row[0]
    #         description = row[1]
    #         location = row[2]
    #         last_update = row[3]

    #         name_item = QStandardItem(name)
    #         description_item = QStandardItem(description)
    #         location_item = QStandardItem(location)
    #         last_update_item = QStandardItem(last_update)

    #         self.model.appendRow([name_item, description_item, location_item, last_update_item])

    #     cursor.close()
    #     connection.close()

    def open_item(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        location = item.text()

        # Open the item in File Explorer if it's a folder
        if QDesktopServices.openUrl(QUrl.fromLocalFile(location)):
            return

        # Open the file using the default program for the file type
        QDesktopServices.openUrl(QUrl.fromLocalFile(location))

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
