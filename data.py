import sqlite3
import datetime as dt

from PyQt6 import uic
from PyQt6.QtWidgets import QButtonGroup, QPushButton, QWidget


class DB:
    con = sqlite3.connect("db.sqlite")
    cur = con.cursor()

    @staticmethod
    def get_sql(path):
        with open(path, "r", encoding="utf-8") as sql:
            return sql.read()


class Schedule(QWidget):

    def __init__(self, data, action):
        super().__init__(None)
        self.action = action
        self.data = data
        self.data.sort(key=lambda x: (dt.datetime.strptime(x[1], "%d.%m.%Y"), dt.datetime.strptime(x[2], "%H:%M")))
        uic.loadUi("ui/schedule.ui", self)

        with open("qss/schedule.qss", "r") as qss:
            self.setStyleSheet(qss.read())

        for i in reversed(range(self.dates_layout.count())):
            item = self.dates_layout.itemAt(i).widget()
            self.dates_layout.removeWidget(item)
            item.setParent(None)

        self.setLayout(self.main_layout)
        self.setMaximumHeight(400)
        self.main_layout.addWidget(self.scroll_dates)
        self.main_layout.addWidget(self.scroll_times)
        self.dates_widget.setLayout(self.dates_layout)
        self.times_widget.setLayout(self.times_layout)
        self.scroll_times.hide()
        self.dates, self.records, first = {}, {}, None
        bg = QButtonGroup(self)

        for row in self.data:
            if (row[1] not in self.dates.values() and
                    dt.datetime.strptime(f"{row[1]} {row[2]}", "%d.%m.%Y %H:%M") >= dt.datetime.today()):

                btn = QPushButton(row[1][:-5], self)
                btn.setFixedSize(80, 40)
                btn.setCheckable(True)
                btn.clicked.connect(self.set_times)

                bg.addButton(btn)
                self.dates_layout.addWidget(btn)
                self.dates[btn] = row[1]

                if first is None:
                    first = btn

        if bg.buttons():
            self.dates_layout.addStretch()
            first.setChecked(True)
            first.clicked.emit()
        else:
            raise ValueError

    def set_times(self):
        times, row, column = [], 0, 0

        for i in reversed(range(self.times_grid.count())):
            item = self.times_grid.itemAt(i).widget()
            self.times_grid.removeWidget(item)
            item.setParent(None)

        for record, date, time in self.data:
            if self.dates.get(self.sender()) == date and time not in times:
                btn = QPushButton(time, self)
                btn.setFixedSize(60, 40)
                btn.clicked.connect(self.action)

                self.times_grid.addWidget(btn, row, column)
                self.records[btn] = record
                times.append(time)
                column += 1

                if column == 5:
                    column = 0
                    row += 1

        self.scroll_times.show()