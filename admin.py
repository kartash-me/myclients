import os
import random
import string
import pandas as pd
import datetime as dt

from PyQt6 import uic
from data import DB, Schedule
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt6.QtWidgets import (QApplication, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget, QMainWindow)


class AdminMain(QMainWindow):

    def __init__(self, login):
        super().__init__(None)
        uic.loadUi("ui/admin_main.ui", self)

        self.widget, self.widgets = None, None
        self.company = DB.cur.execute("SELECT company FROM users WHERE login = ?", (login,)).fetchone()[0]
        company_name = DB.cur.execute("SELECT name FROM companies WHERE company_id = ?", (self.company,)).fetchone()[0]
        self.setWindowTitle(f"myclients - {company_name} - {login}")
        self.get_records = DB.get_sql("sql/get_records.sql") + f"WHERE records.company = {self.company}"
        self.get_branches = "SELECT name AS Название, address AS Адрес FROM branches WHERE company = ?" \
            .replace("?", str(self.company))
        self.get_workers = DB.get_sql("sql/get_workers.sql").replace("?", str(self.company))
        self.get_services = """SELECT title AS Название, description AS Описание, price AS Цена FROM services
                               WHERE company = ?""".replace("?", str(self.company))
        self.get_clients = DB.get_sql("sql/get_clients.sql").replace("?", str(self.company))
        self.r_filters = {"Филиал": self.r_branch, "Сотрудник": self.r_worker, "Клиент": self.r_user,
                          "Статус": self.r_status, "Услуга": self.r_service}
        self.b_filters = {"Название": self.b_name, "Адрес": self.b_address}
        self.w_filters = {"Имя": self.w_name, "Фамилия": self.w_surname, "Пол": self.w_gender, "Филиал": self.w_branch}
        self.s_filters = {"Название": self.s_name}
        self.c_filters = {"Имя": self.c_name, "Фамилия": self.c_surname, "Пол": self.c_gender}

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("db.sqlite")
        self.db.open()

        self.records_model = QSqlQueryModel()
        self.sf_records_model = QSortFilterProxyModel()
        self.branches_model = QSqlQueryModel()
        self.sf_branches_model = QSortFilterProxyModel()
        self.workers_model = QSqlQueryModel()
        self.sf_workers_model = QSortFilterProxyModel()
        self.services_model = QSqlQueryModel()
        self.sf_services_model = QSortFilterProxyModel()
        self.clients_model = QSqlQueryModel()
        self.sf_clients_model = QSortFilterProxyModel()

        self.initUI()

        with open("qss/admin_main.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def initUI(self):
        self.showMaximized()
        self.tabWidget.setCurrentIndex(0)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.currentChanged.connect(self.update)

        self.schedules_tab.setLayout(self.schedule_layout)
        self.schedule_scroll_widget.setLayout(self.scroll_schedules_layout)
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        self.schedule_edit.textChanged.connect(self.set_schedule)
        self.schedule_update_btn.clicked.connect(self.set_schedule)
        self.set_schedule()

        self.records_tab.setLayout(self.records_layout)
        self.new_record_btn.clicked.connect(self.new_record)
        self.r_export_btn.clicked.connect(self.save)

        self.r_price.valueChanged.connect(self.filter_rows)
        self.r_date.dateChanged.connect(self.filter_rows)
        self.r_time.timeChanged.connect(self.filter_rows)

        self.sf_records_model.setSourceModel(self.records_model)
        self.records_table.setModel(self.sf_records_model)
        self.records_model.setQuery(self.get_records)

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
        elif self.tabWidget.currentIndex() == 0:
            self.records_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось записей в вашу организацию")

        self.branches_tab.setLayout(self.branches_layout)
        self.new_branch_btn.clicked.connect(self.new_branch)
        self.b_export_btn.clicked.connect(self.save)

        self.sf_branches_model.setSourceModel(self.branches_model)
        self.branches_table.setModel(self.sf_branches_model)
        self.branches_model.setQuery(self.get_branches)

        if self.branches_model.rowCount():
            self.branches_table.setEnabled(True)
            self.statusBar().showMessage("")
            branches_df = pd.read_sql(self.get_branches, DB.con).to_dict("list")

            for column, values in branches_df.items():
                if column in self.b_filters:
                    self.b_filters.get(column).clear()
                    self.b_filters.get(column).addItems(["Все"] + sorted(list(set(values))))

            for box in self.b_filters.values():
                box.activated.connect(self.filter_rows)
        elif self.tabWidget.currentIndex() == 1:
            self.branches_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось ни одного филиала")

        self.workers_tab.setLayout(self.workers_layout)
        self.new_worker_btn.clicked.connect(self.new_worker)
        self.w_export_btn.clicked.connect(self.save)

        self.w_date.dateChanged.connect(self.filter_rows)
        self.w_phone.valueChanged.connect(self.filter_rows)
        self.sf_workers_model.setSourceModel(self.workers_model)
        self.workers_table.setModel(self.sf_workers_model)
        self.workers_model.setQuery(self.get_workers)

        if self.workers_model.rowCount():
            self.workers_table.setEnabled(True)
            self.statusBar().showMessage("")
            workers_df = pd.read_sql(self.get_workers, DB.con).to_dict("list")

            for column, values in workers_df.items():
                if column in self.w_filters:
                    self.w_filters.get(column).clear()
                    self.w_filters.get(column).addItems(["Все"] + sorted(list(set(values))))

            for box in self.w_filters.values():
                box.activated.connect(self.filter_rows)
        elif self.tabWidget.currentIndex() == 2:
            self.workers_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось сотрудников в вашей организации")

        self.services_tab.setLayout(self.services_layout)
        self.new_service_btn.clicked.connect(self.new_service)
        self.s_export_btn.clicked.connect(self.save)

        self.s_price.valueChanged.connect(self.filter_rows)
        self.sf_services_model.setSourceModel(self.services_model)
        self.services_table.setModel(self.sf_services_model)
        self.services_model.setQuery(self.get_services)

        if self.services_model.rowCount():
            self.services_table.setEnabled(True)
            self.statusBar().showMessage("")
            services_df = pd.read_sql(self.get_services, DB.con).to_dict("list")

            for column, values in services_df.items():
                if column in self.s_filters:
                    self.s_filters.get(column).clear()
                    self.s_filters.get(column).addItems(["Все"] + sorted(list(set(values))))

            for box in self.s_filters.values():
                box.activated.connect(self.filter_rows)
        elif self.tabWidget.currentIndex() == 3:
            self.services_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось ни одной услуги")

        self.clients_tab.setLayout(self.clients_layout)
        self.c_export_btn.clicked.connect(self.save)

        self.c_date.dateChanged.connect(self.filter_rows)
        self.c_phone.valueChanged.connect(self.filter_rows)
        self.sf_clients_model.setSourceModel(self.clients_model)
        self.clients_table.setModel(self.sf_clients_model)
        self.clients_model.setQuery(self.get_clients)

        if self.clients_model.rowCount():
            self.clients_table.setEnabled(True)
            self.statusBar().showMessage("")
            clients_df = pd.read_sql(self.get_clients, DB.con).to_dict("list")

            for column, values in clients_df.items():
                if column in self.c_filters:
                    self.c_filters.get(column).clear()
                    self.c_filters.get(column).addItems(["Все"] + sorted(list(set(values))))

            for box in self.c_filters.values():
                box.activated.connect(self.filter_rows)
        elif self.tabWidget.currentIndex() == 5:
            self.clients_table.setEnabled(False)
            self.statusBar().showMessage("Не нашлось клиентов в вашей организации")

        for table in \
                (self.records_table, self.branches_table, self.workers_table, self.services_table, self.clients_table):
            table.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
            table.resizeColumnsToContents()
            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                    QHeaderView::section { border-top-right-radius: 15px; }""")

        for btn in (self.r_update_btn, self.b_update_btn, self.w_update_btn, self.s_update_btn, self.c_update_btn):
            btn.clicked.connect(self.update)

    def update(self):
        self.records_table.setModel(self.sf_records_model)
        self.branches_table.setModel(self.sf_branches_model)
        self.workers_table.setModel(self.sf_workers_model)
        self.services_table.setModel(self.sf_services_model)
        self.clients_table.setModel(self.sf_clients_model)

        data = {0: (self.records_table, self.records_model, "Не нашлось записей в вашу организацию"),
                1: (self.branches_table, self.branches_model, "Не нашлось ни одного филиала"),
                2: (self.workers_table, self.workers_model, "Не нашлось сотрудников в вашей организации"),
                3: (self.services_table, self.services_model, "Не нашлось ни одной услуги"),
                5: (self.clients_table, self.clients_model, "Не нашлось клиентов в вашей организации")}

        if self.tabWidget.currentIndex() in data:
            table, model, message = data.get(self.tabWidget.currentIndex())

            if not model.rowCount():
                table.setEnabled(False)
                self.statusBar().showMessage(message)
        elif self.tabWidget.currentIndex() == 4:
            self.set_schedule()

    def filter_rows(self):
        index, value, sender = 0, "", self.sender()

        if sender in self.c_filters.values() or sender in (self.c_phone, self.c_date):
            table, model, filters = self.clients_table, self.sf_clients_model, self.c_filters
        elif sender in self.b_filters.values():
            table, model, filters = self.branches_table, self.sf_branches_model, self.b_filters
        elif sender in self.w_filters.values() or sender in (self.w_phone, self.w_date):
            table, model, filters = self.workers_table, self.sf_workers_model, self.w_filters
        elif sender in (self.s_name, self.s_price):
            table, model, filters = self.services_table, self.sf_services_model, self.s_filters
        else:
            table, model, filters = self.records_table, self.sf_records_model, self.r_filters

        if sender in filters.values():
            index = list(filters.values()).index(sender)
            value = sender.currentText()
        elif sender == self.s_price:
            index = 2
            value = sender.text()
        elif sender == self.c_phone:
            index = 4
            value = sender.text()
        elif sender.__class__.__name__ == "QDateEdit":
            index = 5
            value = sender.text()
        elif sender.__class__.__name__ == "QTimeEdit" or sender == self.w_phone:
            index = 6
            value = sender.text()
        elif sender == self.r_price:
            index = 7
            value = sender.text()

        for box in filters.values():
            if box != sender:
                box.setCurrentIndex(0)

        if value.strip() == "Все":
            value = ""

        model.setFilterKeyColumn(index)
        model.setFilterFixedString(value)
        table.setModel(model)

    def set_schedule(self):
        for i in reversed(range(self.scroll_schedules_layout.count())):
            item = self.scroll_schedules_layout.itemAt(i).widget()
            self.scroll_schedules_layout.removeWidget(item)
            item.setParent(None)

        company = str(self.company) if self.company is not None else "NULL"
        df = pd.read_sql(DB.get_sql("sql/get_schedule.sql").replace("?", company), DB.con)
        column, row = 0, 0

        if len(df):
            schedules = df.groupby("main").apply(lambda x: x.iloc[:, :].values.tolist(), include_groups=False).to_dict()

            for worker, schedule in schedules.items():
                if worker.strip().lower().startswith(self.schedule_edit.text().strip().lower()):
                    try:
                        box = QGroupBox("", self)
                        box.setFixedSize(370, 370)
                        layout = QVBoxLayout()
                        label = QLabel(worker)
                        layout.addWidget(label)
                        schedule_widget = Schedule(schedule, self.delete_schedule)
                        schedule_widget.setMaximumSize(350, 350)
                        layout.addWidget(schedule_widget)
                        box.setLayout(layout)
                        self.scroll_schedules_layout.addWidget(box, row, column)
                        column += 1

                        if column == 3:
                            column = 0
                            row += 1
                    except ValueError:
                        pass
        else:
            self.statusBar().showMessage("Не нашлось свободных окошек для записи")

    def add_schedule(self):
        self.widget = NewSchedule(self.company, self)
        self.widget.show()
        self.update()

    def delete_schedule(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Удаление окошка")
        dlg.setText("Удалить запись?")
        dlg.setIcon(QMessageBox.Icon.Question)
        yes_btn = QPushButton("Да")
        yes_btn.setFixedSize(40, 40)
        no_btn = QPushButton("Нет")
        no_btn.setFixedSize(40, 40)
        dlg.addButton(yes_btn, QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton(no_btn, QMessageBox.ButtonRole.RejectRole)
        answer = dlg.exec()

        if answer == 2:
            record = self.sender().parent().parent().parent().parent().records.get(self.sender())
            DB.cur.execute("DELETE FROM schedules WHERE schedule_id = ?", (record,))
            DB.con.commit()
            self.update()

    def new_record(self):
        self.widget = AdminNewRecord(self.company, self)
        self.widget.show()

    def new_branch(self):
        self.widget = QWidget(None)
        self.widget.setWindowTitle("Новый филиал")
        self.widget.setFixedSize(400, 400)

        layout = QVBoxLayout()
        label = QLabel("Новый филиал")
        label.setMaximumHeight(100)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font: 24pt")
        layout.addWidget(label)

        self.widgets = [QLineEdit(), QLineEdit(), QLabel(""), QPushButton("Сохранить")]
        self.widgets[0].setPlaceholderText("Название филиала")
        self.widgets[1].setPlaceholderText("Адрес филиала")
        self.widgets[2].setObjectName("error")
        self.widgets[3].clicked.connect(self.save_branch)

        for w in self.widgets:
            w.setFixedHeight(40)
            layout.addWidget(w)

        with open("qss/add.qss", "r") as qss:
            self.widget.setStyleSheet(qss.read())

        self.widget.setLayout(layout)
        self.widget.show()

    def save_branch(self):
        branches = [i[0] for i in DB.cur.execute(self.get_branches).fetchall()]

        if self.widgets[0].text().strip() == "" or self.widgets[1].text().strip() == "":
            self.widgets[2].setText("Заполните все поля")
        elif self.widgets[0].text() in branches:
            self.widgets[2].setText("Филиал с таким названием уже есть")
        else:
            data = (None, self.company, self.widgets[0].text(), self.widgets[1].text())
            DB.cur.execute("INSERT INTO branches VALUES (?, ?, ?, ?)", data)
            DB.con.commit()
            self.update()

            dlg = QMessageBox(self.widget)
            dlg.setWindowTitle("Новый филиал")
            dlg.setText("Филиал успешно добавлен")
            dlg.setIcon(QMessageBox.Icon.Information)
            btn = QPushButton("ОК")
            btn.setFixedSize(40, 40)
            dlg.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
            ans = dlg.exec()

            if ans:
                self.widget.close()

    def new_worker(self):
        self.widget = QWidget(None)
        self.widget.setWindowTitle("Новый сотрудник")
        self.widget.setFixedSize(450, 140)

        invite = DB.cur.execute("SELECT invite FROM companies WHERE company_id = ?", (self.company,)).fetchone()

        if invite is None:
            invite = ("".join(random.choices(string.ascii_uppercase + string.digits, k=8)),)
            DB.cur.execute("UPDATE companies SET invite = ? WHERE company_id = ?", (invite[0], self.company))
            DB.con.commit()

        label = QLabel("Передайте код ниже сотрудникам, которых\nхотите пригласить в свою организацию")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font: 16pt")
        invite_label = QLabel(invite[0])
        invite_label.setStyleSheet("font: 24pt bold")

        copy_btn = QPushButton("Копировать")
        copy_btn.setFixedHeight(40)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(invite[0]))
        update_btn = QPushButton("Обновить")
        update_btn.setFixedHeight(40)
        update_btn.clicked.connect(self.update_invite)

        h_layout = QHBoxLayout()
        h_layout.addWidget(invite_label)
        h_layout.addWidget(copy_btn)
        h_layout.addWidget(update_btn)
        v_layout = QVBoxLayout()
        v_layout.addWidget(label)
        v_layout.addLayout(h_layout)

        with open("qss/add.qss", "r") as qss:
            self.widget.setStyleSheet(qss.read())

        self.widgets = invite_label
        self.widget.setLayout(v_layout)
        self.widget.show()

    def update_invite(self):
        dlg = QMessageBox(self.widget)
        dlg.setWindowTitle("Обновить код?")
        dlg.setText("Все прошлые коды станут неактивными")
        dlg.setIcon(QMessageBox.Icon.Warning)
        yes_btn = QPushButton("Да")
        yes_btn.setFixedSize(40, 40)
        no_btn = QPushButton("Нет")
        no_btn.setFixedSize(40, 40)
        dlg.addButton(yes_btn, QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton(no_btn, QMessageBox.ButtonRole.RejectRole)
        answer = dlg.exec()

        if answer == 2:
            invite = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            DB.cur.execute("UPDATE companies SET invite = ? WHERE company_id = ?", (invite, self.company))
            DB.con.commit()
            self.widgets.setText(invite)

    def new_service(self):
        self.widget = QWidget(None)
        self.widget.setWindowTitle("Новая услуга")
        self.widget.setFixedSize(400, 400)

        layout = QVBoxLayout()
        label = QLabel("Новая услуга")
        label.setMaximumHeight(100)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font: 24pt")
        layout.addWidget(label)

        self.widgets = [QLineEdit(), QSpinBox(self.widget), QPlainTextEdit(), QLabel(""), QPushButton("Сохранить")]
        self.widgets[0].setPlaceholderText("Название услуги")
        self.widgets[1].setMaximum(2147483646)
        self.widgets[2].setPlaceholderText("Описание услуги (необязательно)")
        self.widgets[3].setObjectName("error")
        self.widgets[4].clicked.connect(self.save_service)

        for w in self.widgets:
            w.setMinimumHeight(40)
            layout.addWidget(w)

        with open("qss/add.qss", "r") as qss:
            self.widget.setStyleSheet(qss.read())

        self.widget.setLayout(layout)
        self.widget.show()

    def save_service(self):
        services = [i[0] for i in DB.cur.execute(self.get_services).fetchall()]

        if self.widgets[0].text().strip() == "" or self.widgets[1].text().strip() == "" or self.widgets[1].value() == 0:
            self.widgets[3].setText("Заполните все обязательные поля")
        elif self.widgets[0].text() in services:
            self.widgets[3].setText("Услуга с таким названием уже есть")
        else:
            comment = None if self.widgets[2].toPlainText().strip() == "" else self.widgets[2].toPlainText()
            data = (None, self.widgets[0].text(), comment, self.widgets[1].value(), self.company)
            DB.cur.execute("INSERT INTO services VALUES (?, ?, ?, ?, ?)", data)
            DB.con.commit()
            self.widgets[3].setText("")
            self.update()

            dlg = QMessageBox(self.widget)
            dlg.setWindowTitle("Новая услуга")
            dlg.setText("Услуга успешно добавлена")
            dlg.setIcon(QMessageBox.Icon.Information)
            btn = QPushButton("ОК")
            btn.setFixedSize(40, 40)
            dlg.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
            ans = dlg.exec()

            if ans:
                self.widget.close()

    def save(self):
        dialog = QFileDialog(self)
        desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
        path = QFileDialog.getSaveFileName(dialog, "Экспорт", desktop, "CSV (*.csv);;Excel (*.xlsx)")[0]
        sql = {self.r_export_btn: self.get_records, self.b_export_btn: self.get_branches,
               self.w_export_btn: self.get_workers, self.c_export_btn: self.get_clients,
               self.s_export_btn: self.get_services}
        df = pd.read_sql(sql.get(self.sender()), DB.con)

        if path[-4:] == ".csv":
            df.to_csv(path, index=False, encoding="utf-8")
        elif path[-5:] == ".xlsx":
            df.to_excel(path, index=False)


class NewSchedule(QWidget):
    def __init__(self, company, parent):
        super().__init__(None)
        uic.loadUi("ui/new_schedule.ui", self)

        self.company, self.parent = company, parent
        self.setWindowTitle("Новое расписание")
        self.setFixedSize(400, 500)
        self.button.clicked.connect(self.save)

        with open("qss/new_schedule.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def save(self):
        self.label.setStyleSheet("color: red;")
        phone = self.edit.text()
        is_phone_correct = False

        if phone == "":
            self.label.setText("Введите номер телефона")
        elif phone.startswith("8") or phone.startswith("+7"):
            phone = phone.replace("+7", "8", 1)

            if phone.isdigit():
                if len(phone) == 11:
                    result = DB.cur.execute(
                        """SELECT phone FROM users INNER JOIN branches ON users.company = branches.branch_id
                           WHERE branches.company = ? AND role = 'worker'""", (self.company,)).fetchall()
                    phones = [str(tuple_[0]) for tuple_ in result]

                    if phone in phones:
                        is_phone_correct = True
                        self.label.setText("")
                    else:
                        self.label.setText("Такого сотрудника нет")
                else:
                    self.label.setText("Неверный номер")
            else:
                self.label.setText("Неверный номер")
        else:
            self.label.setText("Неверный номер")

        if is_phone_correct:
            start_dt = dt.datetime.strptime(f"{self.start_date.text()} {self.start_time.text()}", "%d.%m.%Y %H:%M")
            end_dt = dt.datetime.strptime(f"{self.end_date.text()} {self.end_time.text()}", "%d.%m.%Y %H:%M")

            if start_dt.date() <= dt.date.today() or end_dt.date() <= dt.date.today() or end_dt.date() <= start_dt.date():
                self.label.setText("Введите корректные даты")
            elif self.weekdays.value() < 1:
                self.label.setText("Укажите кол-во рабочих дней")
            elif end_dt.time() <= start_dt.time():
                self.label.setText("Введите корректное время")
            elif self.duration.value() < 1:
                self.label.setText("Укажите интервал записи")
            else:
                self.label.setText("")
                worker = DB.cur.execute("SELECT user_id FROM users WHERE phone = ?", (int(self.edit.text()),)).fetchone()[0]
                schedules = DB.cur.execute("SELECT date, time FROM schedules WHERE worker = ?", (worker,)).fetchall()

                for d, t in schedules:
                    cur_dt = dt.datetime.strptime(f"{d} {t}", "%d.%m.%Y %H:%M")

                    if start_dt <= cur_dt <= end_dt:
                        self.label.setText("На это время уже есть записи")
                        break
                else:
                    schedule, weekday = [], 0
                    cur_date = start_dt.date()

                    while cur_date <= end_dt.date():
                        weekday += 1
                        cur_time = dt.datetime.combine(cur_date, start_dt.time())
                        end_time = dt.datetime.combine(cur_date, end_dt.time())

                        while cur_time < end_time:
                            schedule.append(str(("NULL", worker, cur_date.strftime("%d.%m.%Y"),
                                                 cur_time.strftime("%H:%M"), "available")).replace("'", "", 2))
                            cur_time += dt.timedelta(minutes=self.duration.value())

                        if weekday == self.weekdays.value():
                            weekday = 0

                            for _ in range(self.weekends.value()):
                                cur_date += dt.timedelta(days=1)

                        cur_date += dt.timedelta(days=1)

                    DB.cur.execute("INSERT INTO schedules VALUES " + ", ".join(schedule))
                    DB.con.commit()

                    self.label.setText("Успешно сохранено")
                    self.label.setStyleSheet("color: green;")


class AdminNewRecord(QWidget):
    NORMAL = "QLineEdit { border: 1px solid darkgrey; } QLineEdit:focus { border: 2px solid white; }"

    def __init__(self, company, parent=None):
        super().__init__(None)
        uic.loadUi("ui/admin_new_record.ui", self)

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("db.sqlite")
        self.db.open()
        self.company, self.parent, self.schedule_widget = company, parent, None
        self.branch, self.worker, self.workers, self.services, self.service, self.schedule_id = (None for _ in range(6))
        self.users = dict(DB.cur.execute("""SELECT users.phone, user FROM records
                                         INNER JOIN users ON records.user = users.user_id
                                         WHERE records.company = ?""", (self.company,)).fetchall())
        self.branches = dict(DB.cur.execute("SELECT name, branch_id FROM branches WHERE company = ?",
                                            (self.company,)).fetchall())

        self.user_model = QSqlQueryModel()
        self.sf_user_model = QSortFilterProxyModel()
        items = tuple(self.users.values())
        items = str(items).replace(",", "") if len(items) == 1 else str(items)
        self.user_model.setQuery("""SELECT phone AS Телефон, name AS Имя, surname AS Фамилия
                                 FROM users WHERE user_id IN """ + items)

        self.branch_model = QSqlQueryModel()
        self.sf_branch_model = QSortFilterProxyModel()
        self.branch_model.setQuery("SELECT name AS Название, address AS Адрес FROM branches WHERE company = %s" %
                                   self.company)

        self.worker_model = QSqlQueryModel()
        self.sf_worker_model = QSortFilterProxyModel()
        self.service_model = QSqlQueryModel()
        self.sf_service_model = QSortFilterProxyModel()

        self.initUI()

        with open("qss/admin_new_record.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def initUI(self):
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("Новая запись")
        self.setFixedSize(400, 400)

        u_header = self.user_view.horizontalHeader()
        u_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        u_header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                  QHeaderView::section { border-top-right-radius: 15px; }""")

        self.sf_user_model.setSourceModel(self.user_model)
        self.user_next_btn.clicked.connect(self.user_next)
        self.user_edit.returnPressed.connect(self.user_next)
        self.user_edit.textChanged.connect(self.user_filter)
        self.user_view.setModel(self.sf_user_model)
        self.user_view.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
        self.user_view.selectionModel().selectionChanged.connect(self.user_select)
        self.user_view.resizeColumnsToContents()

        if not self.user_model.rowCount():
            self.user_view.hide()
            self.user_edit.setEnabled(False)
            self.user_next_btn.setEnabled(False)
            self.user_error.setText("Не нашлось ни одного клиента")

        b_header = self.branch_view.horizontalHeader()
        b_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        b_header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                  QHeaderView::section { border-top-right-radius: 15px; }""")

        self.sf_branch_model.setSourceModel(self.branch_model)
        self.branch_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.branch_next_btn.clicked.connect(self.branch_next)
        self.branch_edit.returnPressed.connect(self.branch_next)
        self.branch_edit.textChanged.connect(self.branch_filter)
        self.branch_view.setModel(self.sf_branch_model)
        self.branch_view.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
        self.branch_view.selectionModel().selectionChanged.connect(self.branch_select)
        self.branch_view.resizeColumnsToContents()

        if not self.branch_model.rowCount():
            self.branch_view.hide()
            self.branch_edit.setEnabled(False)
            self.branch_next_btn.setEnabled(False)
            self.branch_error.setText("Не нашлось ни одного филиала")

        w_header = self.worker_view.horizontalHeader()
        w_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        w_header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                  QHeaderView::section { border-top-right-radius: 15px; }""")

        self.sf_worker_model.setSourceModel(self.worker_model)
        self.worker_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.worker_next_btn.clicked.connect(self.worker_next)
        self.worker_edit.returnPressed.connect(self.worker_next)
        self.worker_edit.textChanged.connect(self.worker_filter)
        self.worker_view.setModel(self.sf_worker_model)
        self.worker_view.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
        self.worker_view.selectionModel().selectionChanged.connect(self.worker_select)
        self.worker_view.resizeColumnsToContents()

        s_header = self.service_view.horizontalHeader()
        s_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        s_header.setStyleSheet("""QHeaderView { border-top-right-radius: 15px; }
                                  QHeaderView::section { border-top-right-radius: 15px; }""")

        self.sf_service_model.setSourceModel(self.service_model)
        self.service_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.service_next_btn.clicked.connect(self.service_next)
        self.service_edit.returnPressed.connect(self.service_next)
        self.service_edit.textChanged.connect(self.service_filter)
        self.service_view.setModel(self.sf_service_model)
        self.service_view.verticalHeader().setStyleSheet("border-bottom-left-radius: 15px;")
        self.service_view.selectionModel().selectionChanged.connect(self.service_select)
        self.service_view.resizeColumnsToContents()

        self.schedule_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.info_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.save_btn.clicked.connect(self.save)

    def user_filter(self):
        self.user_edit.setStyleSheet(self.NORMAL)
        self.sf_user_model.setFilterKeyColumn(0)
        self.sf_user_model.setFilterFixedString(self.user_edit.text())
        self.user_view.setModel(self.sf_user_model)

    def user_select(self, new, _):
        row = None

        for i in new.indexes():
            row = i.row()
            break

        self.user_edit.setText(str(self.sf_user_model.index(row, 0).data()))

    def user_next(self):
        if self.user_edit.text().strip() == "":
            self.user_error.setText("Введите номер телефона")
            self.user_edit.setStyleSheet("border: 2px solid red")
        elif self.user_edit.text() in list(map(str, self.users.keys())):
            self.user_error.setText("")
            self.stack.setCurrentIndex(1)
        else:
            self.user_error.setText("Неверный номер телефона")
            self.user_edit.setStyleSheet("border: 2px solid red")

    def branch_filter(self):
        self.branch_edit.setStyleSheet(self.NORMAL)
        self.sf_branch_model.setFilterKeyColumn(0)
        self.sf_branch_model.setFilterFixedString(self.branch_edit.text())
        self.branch_view.setModel(self.sf_branch_model)

    def branch_select(self, new, _):
        row = None

        for i in new.indexes():
            row = i.row()
            break

        self.branch_edit.setText(self.sf_branch_model.index(row, 0).data())

    def branch_next(self):
        if self.branch_edit.text().strip() == "":
            self.branch_error.setText("Введите название филиала")
            self.branch_edit.setStyleSheet("border: 2px solid red")
        elif self.branch_edit.text() in self.branches:
            self.branch_error.setText("")
            self.stack.setCurrentIndex(2)
            self.branch = self.branches[self.branch_edit.text()]
            self.worker_model.setQuery(f"""SELECT phone AS Телефон, name AS Имя, surname AS Фамилия FROM users
                                           WHERE role = 'worker' AND company = {self.branch}""")
            self.workers = dict(DB.cur.execute("SELECT phone, user_id FROM users WHERE role = 'worker' AND company = ?",
                                               (self.branch,)).fetchall())
            if not self.worker_model.rowCount():
                self.worker_view.hide()
                self.worker_edit.setEnabled(False)
                self.worker_next_btn.setEnabled(False)
                self.worker_error.setText("Не нашлось ни одного сотрудника")
        else:
            self.branch_error.setText("Неверный филиал")
            self.branch_edit.setStyleSheet("border: 2px solid red")

    def worker_filter(self):
        self.worker_edit.setStyleSheet(self.NORMAL)
        self.sf_worker_model.setFilterKeyColumn(0)
        self.sf_worker_model.setFilterFixedString(self.worker_edit.text())
        self.worker_view.setModel(self.sf_worker_model)

    def worker_select(self, new, _):
        row = None

        for i in new.indexes():
            row = i.row()
            break

        self.worker_edit.setText(str(self.sf_worker_model.index(row, 0).data()))

    def worker_next(self):
        if self.worker_edit.text().strip() == "":
            self.worker_error.setText("Введите телефон сотрудника")
            self.worker_edit.setStyleSheet("border: 2px solid red")
        elif self.worker_edit.text() in list(map(str, self.workers.keys())):
            self.worker_error.setText("")
            self.stack.setCurrentIndex(3)
            self.worker = self.workers[int(self.worker_edit.text())]
            self.services = DB.cur.execute("SELECT title, service_id FROM services WHERE company = ?",
                                           (self.company,)).fetchall()

            if not self.services:
                self.service_view.hide()
                self.service_edit.setEnabled(False)
                self.service_next_btn.setEnabled(False)
                self.service_error.setText("Не нашлось ни одной услуги")
            else:
                self.service_model.setQuery(f"""SELECT title AS Название, price AS Цена FROM services
                                                WHERE company = {self.company}""")
        else:
            self.worker_error.setText("Неверный номер телефона")
            self.worker_edit.setStyleSheet("border: 2px solid red")

    def service_filter(self):
        self.service_edit.setStyleSheet(self.NORMAL)
        self.sf_service_model.setFilterKeyColumn(0)
        self.sf_service_model.setFilterFixedString(self.service_edit.text())
        self.service_view.setModel(self.sf_service_model)

    def service_select(self, new, _):
        row = None

        for i in new.indexes():
            row = i.row()
            break

        self.service_edit.setText(self.sf_service_model.index(row, 0).data())

    def service_next(self):
        services = dict(self.services)

        if self.service_edit.text().strip() == "":
            self.service_error.setText("Введите название услуги")
            self.service_edit.setStyleSheet("border: 2px solid red")
        elif self.service_edit.text() in services.keys():
            self.service_error.setText("")
            self.service = services[self.service_edit.text()]
            self.stack.setCurrentIndex(4)

            schedule = DB.cur.execute("""SELECT schedule_id, date, time FROM schedules
                                      WHERE worker = ? AND status = 'available'""", (self.worker,)).fetchall()

            try:
                if schedule:
                    for i in reversed(range(self.schedule_layout.count())):
                        item = self.schedule_layout.itemAt(i).widget()
                        self.schedule_layout.removeWidget(item)
                        item.setParent(None)

                    self.schedule_widget = Schedule(schedule, self.schedule_next)
                    self.schedule_layout.addWidget(self.schedule_widget)
                else:
                    raise ValueError
            except ValueError:
                self.schedule_error.setText("Не нашлось ни одного свободного\nвремени для записи")
        else:
            self.service_error.setText("Неверная услуга")
            self.service_edit.setStyleSheet("border: 2px solid red")

    def schedule_next(self):
        self.schedule_id = self.schedule_widget.records.get(self.sender())
        self.stack.setCurrentIndex(5)

    def save(self):
        comment = self.comment_edit.toPlainText()
        data = (None, self.users.get(int(self.user_edit.text())), self.company, self.branch, self.worker, self.service,
                self.schedule_id, (None if comment.strip() == "" else comment), "new")
        DB.cur.execute("UPDATE schedules SET status = 'booked' WHERE schedule_id = ?", (self.schedule_id,))
        DB.cur.execute("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        DB.con.commit()
        self.parent.update()
        self.close()