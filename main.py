import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)

class FM24Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FM24 Squad Viewer")
        self.resize(1200, 600)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #000000;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #2979ff;
                color: #ffffff;
                border: none;
                border-radius: 15px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1c54b2;
            }
            QTableWidget {
                background-color: #121212;
                alternate-background-color: #1e1e1e;
                border: 1px solid #2979ff;
                border-radius: 10px;
                gridline-color: #1e1e1e;
                color: #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #2979ff;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2979ff;
                color: #ffffff;
                border: none;
                padding: 6px;
                font-weight: bold;
            }
            """
        )

        layout = QVBoxLayout(self)
        self.open_button = QPushButton("Open Squad HTML")
        self.open_button.clicked.connect(self.open_file)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.open_button)
        layout.addWidget(self.table)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select squad file",
            "",
            "HTML Files (*.html *.htm)"
        )
        if path:
            dataframes = pd.read_html(path)
            if dataframes:
                df = dataframes[0]
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.table.setColumnCount(len(df.columns))
                self.table.setHorizontalHeaderLabels(df.columns)
                for row_index, row in df.iterrows():
                    self.table.insertRow(row_index)
                    for column_index, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        self.table.setItem(row_index, column_index, item)


def main():
    app = QApplication(sys.argv)
    window = FM24Tool()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
