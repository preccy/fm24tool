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
    QHeaderView,
    QTabWidget,
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

        self.tabs = QTabWidget()

        self.table = QTableWidget()
        self._prep_table(self.table)
        self.tabs.addTab(self.table, "Squad")

        self.formations_table = QTableWidget()
        self._prep_table(self.formations_table)
        self.tabs.addTab(self.formations_table, "Formations")

        self.tactics_table = QTableWidget()
        self._prep_table(self.tactics_table)
        self.tabs.addTab(self.tactics_table, "Tactics")

        self.best_table = QTableWidget()
        self._prep_table(self.best_table)
        self.tabs.addTab(self.best_table, "Best")

        self.worst_table = QTableWidget()
        self._prep_table(self.worst_table)
        self.tabs.addTab(self.worst_table, "Worst")

        self.wonder_table = QTableWidget()
        self._prep_table(self.wonder_table)
        self.tabs.addTab(self.wonder_table, "Wonderkids")

        layout.addWidget(self.open_button)
        layout.addWidget(self.tabs)

    def _prep_table(self, table):
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


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

                if 'Acc' in df.columns:
                    start = df.columns.get_loc('Acc')
                    self.attribute_cols = list(df.columns[start:])
                else:
                    self.attribute_cols = []
                for col in ['CA', 'PA', 'Age'] + self.attribute_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                self.df = df
                self.populate_table(self.table, df)
                self.update_analysis()

    def populate_table(self, table, data):
        table.setRowCount(0)
        table.setColumnCount(0)
        if data is None or data.empty:
            return
        table.setColumnCount(len(data.columns))
        table.setHorizontalHeaderLabels([str(c) for c in data.columns])
        for _, row in data.iterrows():
            row_index = table.rowCount()
            table.insertRow(row_index)
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                table.setItem(row_index, column_index, item)

    def update_analysis(self):
        df = getattr(self, 'df', None)
        if df is None:
            return
        best = df.sort_values('CA', ascending=False).head(5)
        self.populate_table(self.best_table, best[['Name', 'CA', 'PA', 'Age']])

        worst = df.sort_values('CA').head(5)
        self.populate_table(self.worst_table, worst[['Name', 'CA', 'PA', 'Age']])

        wonder = df[(df['Age'] <= 21) & (df['PA'] >= 150)]
        self.populate_table(self.wonder_table, wonder[['Name', 'CA', 'PA', 'Age']])

        form_rows = []
        for name, positions in FORMATIONS.items():
            score = formation_score(df, positions)
            form_rows.append({'Formation': name, 'Score': round(score, 2)})
        self.populate_table(self.formations_table, pd.DataFrame(form_rows))

        tactic_rows = []
        for name, attrs in STYLE_ATTRS.items():
            score = style_score(df, attrs)
            tactic_rows.append({'Style': name, 'Score': round(score, 2)})
        self.populate_table(self.tactics_table, pd.DataFrame(tactic_rows))


def formation_score(df, positions):
    used = set()
    total = 0
    for pos in positions:
        candidates = df[(df['Position Selected'] == pos) & (~df['Name'].isin(used))]
        if candidates.empty:
            continue
        best = candidates.sort_values('CA', ascending=False).iloc[0]
        total += best['CA']
        used.add(best['Name'])
    return (total / (200 * len(positions))) * 100


def style_score(df, attrs):
    top = df.sort_values('CA', ascending=False).head(11)
    cols = [a for a in attrs if a in top.columns]
    if not cols:
        return 0
    return (top[cols].mean().mean() / 20) * 100


FORMATIONS = {
    '4-3-3': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'DM', 'MCR', 'MCL', 'AMR', 'AML', 'STC'],
    '4-4-2': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MR', 'ML', 'MCR', 'MCL', 'STCR', 'STCL'],
    '3-5-2': ['GK', 'DCR', 'DC', 'DCL', 'MR', 'ML', 'DM', 'MCR', 'MCL', 'STCR', 'STCL'],
}


STYLE_ATTRS = {
    'Attacking': ['Fin', 'Dri', 'Tec'],
    'Defensive': ['Tck', 'Mar', 'Pos'],
    'Possession': ['Pas', 'Tec', 'Cmp'],
}



def main():
    app = QApplication(sys.argv)
    window = FM24Tool()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
