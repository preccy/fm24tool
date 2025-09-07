import sys
import pandas as pd
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QDialog,
    QTextEdit,
    QInputDialog,
    QLineEdit,
)
from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"

class FM24Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FM24 Squad Viewer")
        self.resize(1200, 600)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.drag_position = None
        self.api_key = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            #TitleBar {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #2979ff;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1c54b2;
            }
            QPushButton#WindowControl {
                padding: 4px;
                border-radius: 4px;
                width: 24px;
                height: 24px;
            }
            QTableWidget {
                background-color: #262626;
                alternate-background-color: #2e2e2e;
                border: 1px solid #2979ff;
                border-radius: 4px;
                gridline-color: #2e2e2e;
                color: #e0e0e0;
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
                background-color: #2b2b2b;
                color: #e0e0e0;
                padding: 8px 12px;
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)
        title_label = QLabel("FM24 Squad Viewer")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("WindowControl")
        self.settings_button.clicked.connect(self.open_settings)
        self.full_button = QPushButton("⛶")
        self.full_button.setObjectName("WindowControl")
        self.full_button.clicked.connect(self.toggle_fullscreen)
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("WindowControl")
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.settings_button)
        title_layout.addWidget(self.full_button)
        title_layout.addWidget(self.close_button)
        self.title_bar.installEventFilter(self)
        layout.addWidget(self.title_bar)

        button_bar = QHBoxLayout()
        self.open_button = QPushButton("Open Squad HTML")
        self.open_button.clicked.connect(self.open_file)
        button_bar.addWidget(self.open_button)

        self.assess_button = QPushButton("Assess My Squad")
        self.assess_button.clicked.connect(self.assess_squad)
        button_bar.addWidget(self.assess_button)

        layout.addLayout(button_bar)

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

        layout.addWidget(self.tabs)

    def _prep_table(self, table):
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def eventFilter(self, obj, event):
        if obj == self.title_bar:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                return True
            elif event.type() == QEvent.MouseMove and event.buttons() == Qt.LeftButton and self.drag_position is not None:
                self.move(event.globalPos() - self.drag_position)
                return True
        return super().eventFilter(obj, event)

    def open_settings(self):
        key, ok = QInputDialog.getText(
            self,
            "OpenAI API Key",
            "Enter your OpenAI API key:",
            QLineEdit.Password,
            self.api_key or "",
        )
        if ok:
            self.api_key = key


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
                if 'Position' in df.columns:
                    df['PosSet'] = df['Position'].apply(parse_positions)
                else:
                    df['PosSet'] = [set() for _ in range(len(df))]
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

    def assess_squad(self):
        df = getattr(self, 'df', None)
        if df is None:
            return
        try:
            summary = df[['Name', 'Age', 'CA', 'PA'] + self.attribute_cols].to_dict(orient='records')
        except Exception:
            summary = df.to_dict(orient='records')
        prompt = (
            "You are a football squad analyst. Using the squad data with fields like Name, Age, CA, "
            "PA and attributes, provide a concise assessment outlining strengths, areas needing "
            "upgrades or depth, and players who could be offloaded due to age or low potential."
        )
        try:
            client = OpenAI(api_key=self.api_key) if self.api_key else OpenAI()
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": str(summary)},
                ],
            )
            assessment = response.choices[0].message.content
        except Exception as e:
            assessment = f"Error generating assessment: {e}"
        dialog = QDialog(self)
        dialog.setWindowTitle("Squad Assessment")
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(assessment)
        layout.addWidget(text)
        dialog.resize(600, 400)
        dialog.show()
        if not hasattr(self, '_assessment_dialogs'):
            self._assessment_dialogs = []
        self._assessment_dialogs.append(dialog)

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

def parse_positions(pos_str):
    pos_str = str(pos_str)
    segments = [seg.strip() for seg in pos_str.split(',')]
    codes = set()
    for seg in segments:
        if not seg:
            continue
        if '(' in seg:
            roles_part, sides_part = seg.split('(')
            sides = list(sides_part.strip(')'))
        else:
            roles_part = seg
            sides = ['']
        roles = [r.strip() for r in roles_part.split('/')]
        for role in roles:
            for side in sides:
                code = (role + side).replace(' ', '')
                codes.add(code)
    expanded = set()
    for code in codes:
        expanded.add(code)
        if code == 'DC':
            expanded.update({'DCL', 'DCR'})
        elif code == 'MC':
            expanded.update({'MCL', 'MCR'})
        elif code == 'AM':
            expanded.update({'AML', 'AMR', 'AMC'})
        elif code == 'ST':
            expanded.add('STC')
        elif code == 'WB':
            expanded.update({'WBL', 'WBR'})
    return expanded

def player_position_score(player, pos):
    attrs = POSITION_ATTRS.get(pos, [])
    total = 0
    weight_sum = 0
    for a in attrs:
        if a in player.index and pd.notna(player[a]):
            w = ATTRIBUTE_WEIGHTS.get(a, 1)
            total += player[a] * w
            weight_sum += w
    attr_score = total / weight_sum if weight_sum else 0
    return player.get('CA', 0) * 0.7 + attr_score * 3


def best_xi_for_formation(df, positions):
    used = set()
    rows = []
    total = 0
    for pos in positions:
        remaining = df[~df['Name'].isin(used)]
        if remaining.empty:
            break
        candidates = remaining[remaining['PosSet'].apply(lambda s: pos in s)]
        if candidates.empty:
            rows.append({'Position': pos, 'Name': 'None', 'Score': 0})
            continue
        candidates = candidates.copy()
        candidates['Score'] = candidates.apply(lambda r: player_position_score(r, pos), axis=1)
        best = candidates.sort_values('Score', ascending=False).iloc[0]
        rows.append({'Position': pos, 'Name': best['Name'], 'Score': round(best['Score'], 2)})
        used.add(best['Name'])
        total += best['Score']
    avg = total / len(positions) if positions else 0
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

# Attribute weights derived from FM-Arena testing
ATTRIBUTE_WEIGHTS = {
    'Pac': 2.0,
    'Acc': 1.77,
    'Jum': 1.46,
    'Dri': 1.38,
    'Bal': 1.19,
    'Con': 1.15,
    'Ant': 1.15,
    'Det': 1.12,
    'Agi': 1.12,
    'Sta': 1.08,
    'Str': 1.08,
    'Fir': 1.04,
    'Cmp': 1.04,
    'Wor': 1.04,
    'Fin': 1.04,
    'Fla': 1.04,
    'LSh': 1.04,
    'Agg': 1.04,
    'Hea': 1.04,
    'OTB': 1.0,
    'Dec': 1.0,
    'Cro': 1.0,
    'Vis': 1.0,
    'Tck': 1.04,
    'Pos': 1.04,
    'Tec': 1.04,
    'Mar': 1.04,
    'Pas': 1.08,
    'Bra': 1.04,
    'Tea': 1.08,
}
 
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
    'Gegenpress': ['Wor', 'Sta', 'Agg'],
    'Tiki-Taka': ['Pas', 'Tec', 'Cmp'],
    'Vertical Tiki-Taka': ['Pas', 'Tec', 'Dec'],
    'Control Possession': ['Pas', 'Dec', 'Vis'],
    'Wing Play': ['Acc', 'Pac', 'Cro'],
    'Route One': ['Jum', 'Hea', 'Str'],
    'Fluid Counter-Attack': ['Acc', 'Pac', 'Dec'],
    'Direct Counter-Attack': ['Acc', 'Pac', 'Fin'],
    'Park the Bus': ['Tck', 'Mar', 'Pos'],
    'Catenaccio': ['Tck', 'Pos', 'Ant'],
}



def main():
    app = QApplication(sys.argv)
    window = FM24Tool()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
