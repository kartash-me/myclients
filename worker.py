import os
import pandas as pd

from data import DB
from PyQt6 import uic
from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt6.QtWidgets import QFileDialog, QHeaderView, QMainWindow


class WorkerMain(QMainWindow):

    def __init__(self, login):
        super().__init__(None)
        uic.loadUi("ui/worker_main.ui", self)

        worker, branch = DB.cur.execute("SELECT user_id, company FROM users WHERE login = ?", (login,)).fetchone()
        branch_name, company = DB.cur.execute("SELECT name, company FROM branches WHERE branch_id = ?",
                                              (branch,)).fetchone()
        company_name = DB.cur.execute("SELECT name FROM companies WHERE company_id = ?", (company,)).fetchone()[0]

        self.setWindowTitle(f"myclients - {company_name} - {branch_name} - {login}")
        self.get_records = DB.get_sql("sql/worker_records.sql") + f"WHERE records.worker = {worker}"
        self.r_filters = {"Клиент": self.r_user, "Статус": self.r_status, "Услуга": self.r_service}

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("db.sqlite")
        self.db.open()

        self.records_model = QSqlQueryModel()
        self.sf_records_model = QSortFilterProxyModel()

        self.initUI()

        with open("qss/admin_main.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def initUI(self):
        self.showMaximized()
        self.centralwidget.setLayout(self.records_layout)
        self.r_export_btn.clicked.connect(self.save)

        self.r_price.valueChanged.connect(self.filter_rows)
        self.r_date.dateChanged.connect(self.filter_rows)
        self.r_time.timeChanged.connect(self.filter_rows)

        self.sf_records_model.setSourceModel(self.records_model)
        self.records_table.setModel(self.sf_records_model)
        self.records_model.setQuery(self.get_records)
        self.records_table.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
        self.records_table.resizeColumnsToContents()

        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                        QHeaderView::section { border-top-right-radius: 15px; }""")

        if self.records_model.rowCount():
            self.records_table.setEnabled(True)
            self.statusBar().showMessage("")
            records_df = pd.read_sql(self.get_records, DB.con).to_dict("list")

            for column, values in records_df.items():
                if column in self.r_filters:
                    self.r_filters.get(column).clear()
                    self.r_filters.get(column).addItems(["Все"] + sorted(list(set(values))))

            for box in self.r_filters.values():
                box.activated.connect(self.filter_rows)
        else:
            self.records_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось ни одной записи")

    def filter_rows(self):
        index, value, sender = 0, "", self.sender()

        if sender in self.r_filters.values():
            index = list(self.r_filters.values()).index(sender)
            value = sender.currentText()
        elif sender == self.r_date:
            index = 3
            value = sender.text()
        elif sender == self.r_time:
            index = 4
            value = sender.text()
        elif sender == self.r_price:
            index = 5
            value = sender.text()

        for box in self.r_filters.values():
            if box != sender:
                box.setCurrentIndex(0)

        if value.strip() == "Все":
            value = ""

        self.sf_records_model.setFilterKeyColumn(index)
        self.sf_records_model.setFilterFixedString(value)
        self.records_table.setModel(self.sf_records_model)

    def save(self):
        dialog = QFileDialog(self)
        desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
        path = QFileDialog.getSaveFileName(dialog, "Экспорт", desktop, "CSV (*.csv);;Excel (*.xlsx)")[0]
        df = pd.read_sql(self.get_records, DB.con)

        if path[-4:] == ".csv":
            df.to_csv(path, index=False, encoding="utf-8")
        elif path[-5:] == ".xlsx":
            df.to_excel(path, index=False)
