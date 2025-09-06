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
    QDialog,
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
            QTabWidget::pane {
                border: 1px solid #2979ff;
            }
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #f0f0f0;
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2979ff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #1c54b2;
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
        self.formations_table.cellDoubleClicked.connect(self.show_best_xi)

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

    def show_best_xi(self, row, column):
        df = getattr(self, 'df', None)
        if df is None:
            return
        item = self.formations_table.item(row, 0)
        if item is None:
            return
        form_name = item.text()
        positions = FORMATIONS.get(form_name)
        if not positions:
            return
        xi_df, _ = best_xi_for_formation(df, positions)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Best XI - {form_name}")
        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        self._prep_table(table)
        self.populate_table(table, xi_df)
        layout.addWidget(table)
        dialog.resize(600, 400)
        dialog.show()
        if not hasattr(self, '_xi_dialogs'):
            self._xi_dialogs = []
        self._xi_dialogs.append(dialog)

def player_position_score(player, pos):
    attrs = POSITION_ATTRS.get(pos, [])
    vals = [player[a] for a in attrs if a in player.index and pd.notna(player[a])]
    attr_score = sum(vals) / len(vals) if vals else 0
    return player.get('CA', 0) * 0.7 + attr_score * 3


def best_xi_for_formation(df, positions):
    used = set()
    rows = []
    total = 0
    for pos in positions:
        remaining = df[~df['Name'].isin(used)]
        if remaining.empty:
            break
        candidates = remaining[remaining['Position Selected'].str.contains(pos, na=False)]
        if candidates.empty:
            candidates = remaining
        candidates = candidates.copy()
        candidates['Score'] = candidates.apply(lambda r: player_position_score(r, pos), axis=1)
        best = candidates.sort_values('Score', ascending=False).iloc[0]
        rows.append({'Position': pos, 'Name': best['Name'], 'Score': round(best['Score'], 2)})
        used.add(best['Name'])
        total += best['Score']
    avg = total / len(rows) if rows else 0
    return pd.DataFrame(rows), avg


def formation_score(df, positions):
    _, avg = best_xi_for_formation(df, positions)
    return (avg / 200) * 100


def style_score(df, attrs):
    top = df.sort_values('CA', ascending=False).head(11)
    cols = [a for a in attrs if a in top.columns]
    if not cols:
        return 0
    return (top[cols].mean().mean() / 20) * 100
 
POSITION_ATTRS = {
    'GK': ['Ref', 'One', 'Han', 'Aer'],
    'DL': ['Acc', 'Pac', 'Tck', 'Mar', 'Cro'],
    'DR': ['Acc', 'Pac', 'Tck', 'Mar', 'Cro'],
    'DCL': ['Tck', 'Mar', 'Pos', 'Jum', 'Hea'],
    'DCR': ['Tck', 'Mar', 'Pos', 'Jum', 'Hea'],
    'DC': ['Tck', 'Mar', 'Pos', 'Jum', 'Hea'],
    'DM': ['Tck', 'Pos', 'Tea', 'Sta', 'Pas'],
    'MCL': ['Pas', 'Tec', 'Sta', 'Dec'],
    'MCR': ['Pas', 'Tec', 'Sta', 'Dec'],
    'MC': ['Pas', 'Tec', 'Sta', 'Dec'],
    'ML': ['Cro', 'Pas', 'Tec', 'Sta', 'Acc'],
    'MR': ['Cro', 'Pas', 'Tec', 'Sta', 'Acc'],
    'AML': ['Dri', 'Pas', 'Tec', 'Fla', 'Fin'],
    'AMR': ['Dri', 'Pas', 'Tec', 'Fla', 'Fin'],
    'AMC': ['Dri', 'Pas', 'Tec', 'Fla', 'Fin'],
    'STC': ['Fin', 'Cmp', 'Tec', 'Acc', 'Str'],
    'STCL': ['Fin', 'Cmp', 'Tec', 'Acc', 'Str'],
    'STCR': ['Fin', 'Cmp', 'Tec', 'Acc', 'Str'],
    'WBR': ['Acc', 'Pac', 'Cro', 'Sta', 'Tck'],
    'WBL': ['Acc', 'Pac', 'Cro', 'Sta', 'Tck'],
}


FORMATIONS = {
    '4-3-3': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'DM', 'MCR', 'MCL', 'AMR', 'AML', 'STC'],
    '4-4-2': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MR', 'ML', 'MCR', 'MCL', 'STCR', 'STCL'],
    '3-5-2': ['GK', 'DCR', 'DC', 'DCL', 'MR', 'ML', 'DM', 'MCR', 'MCL', 'STCR', 'STCL'],
    '4-2-3-1': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MCR', 'MCL', 'AMR', 'AMC', 'AML', 'STC'],
    '4-3-1-2': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MCR', 'MC', 'MCL', 'AMC', 'STCR', 'STCL'],
    '4-5-1': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MR', 'ML', 'MCR', 'MC', 'MCL', 'STC'],
    '4-1-4-1': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'DM', 'MR', 'ML', 'MCR', 'MCL', 'STC'],
    '4-2-4': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MCR', 'MCL', 'AMR', 'AML', 'STCR', 'STCL'],
    '3-4-3': ['GK', 'DCR', 'DC', 'DCL', 'MR', 'ML', 'MCR', 'MCL', 'AMR', 'AML', 'STC'],
    '3-4-1-2': ['GK', 'DCR', 'DC', 'DCL', 'MR', 'ML', 'MCR', 'MCL', 'AMC', 'STCR', 'STCL'],
    '5-3-2': ['GK', 'WBR', 'DCR', 'DC', 'DCL', 'WBL', 'MCR', 'MC', 'MCL', 'STCR', 'STCL'],
    '5-4-1': ['GK', 'WBR', 'DCR', 'DC', 'DCL', 'WBL', 'MR', 'ML', 'MCR', 'MCL', 'STC'],
    '3-4-2-1': ['GK', 'DCR', 'DC', 'DCL', 'MR', 'ML', 'MCR', 'MCL', 'AMR', 'AML', 'STC'],
    '4-2-2-2': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MCR', 'MCL', 'AMR', 'AML', 'STCR', 'STCL'],
    '4-3-2-1': ['GK', 'DR', 'DCR', 'DCL', 'DL', 'MCR', 'MC', 'MCL', 'AMR', 'AML', 'STC'],
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
