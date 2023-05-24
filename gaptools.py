import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout)
from ctd_to_btd import CtdToBtdWidget, ChildWidget
from survey_app import surveyApp


class ParentWidget(QMainWindow):

    # Dictionary mapping widget names to widget classes
    widget_mapping = {
        "Survey App Resource Locator": surveyApp,
        "Convert CTD to BTD": CtdToBtdWidget,
        # "Child Widget 2": CW2,
        # "Child Widget 3": CW3,
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GAP Toolbox")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.title_label = QLabel("File Conversion Tools:")
        self.search_box = QLineEdit()
        self.list_widget = QListWidget()
        self.submit_button = QPushButton("Submit")

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.submit_button)
        self.central_widget.setLayout(self.layout)

        self.list_widget.itemDoubleClicked.connect(self.open_selected_widget)
        self.submit_button.clicked.connect(self.open_selected_widget)
        self.search_box.textChanged.connect(self.filter_widget_names)

        # Original widget names
        self.original_widget_names = list(self.widget_mapping.keys())

        # Populate the list widget with original widget names
        self.list_widget.addItems(self.original_widget_names)

    def filter_widget_names(self):
        search_text = self.search_box.text().lower()
        self.list_widget.clear()
        filtered_widget_names = [
            name for name in self.original_widget_names if search_text in name.lower()]
        self.list_widget.addItems(filtered_widget_names)

    def open_selected_widget(self):
        selected_item = self.list_widget.currentItem()
        if selected_item is not None:
            widget_name = selected_item.text()
            if widget_name in self.widget_mapping:
                widget_class = self.widget_mapping[widget_name]
                child_widget = widget_class()
                child_widget.setAttribute(
                    Qt.WidgetAttribute.WA_DeleteOnClose, False)
                child_widget.show()
                self.child_widgets.append(child_widget)

    def closeEvent(self, event):
        for child_widget in self.child_widgets:
            child_widget.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    parent_widget = ParentWidget()
    parent_widget.child_widgets = []
    parent_widget.show()
    sys.exit(app.exec())
