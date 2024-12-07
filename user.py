from data import DB, Schedule
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QMessageBox, QPushButton, QWidget, QMainWindow


class UserMain(QMainWindow):

    def __init__(self, login):
        super().__init__(None)
        uic.loadUi("ui/user_main.ui", self)
        self.setWindowTitle(f"myclients - {login}")

        self.user = DB.cur.execute("SELECT user_id FROM users WHERE login = ?", (login,)).fetchone()[0]
        self.get_records = DB.get_sql("sql/user_records.sql") + f"WHERE records.user = {self.user}"
        self.buttons, self.widget = {}, None

        self.showMaximized()
        self.setCentralWidget(self.tabWidget)
        self.records_tab.setLayout(self.records_layout)
        self.future_widget.setLayout(self.future_layout)
        self.past_widget.setLayout(self.past_layout)
        self.new_btn.clicked.connect(self.new_record)
        self.add_records()

        with open("qss/user_main.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def new_record(self):
        self.widget = UserNewRecord(self)
        self.widget.show()

    def add_records(self):
        def create_record(items, icon, action):
            row, column = 0, 1
            box = QGroupBox()
            box.setMaximumWidth(350)
            grid = QGridLayout(box)

            for i in items[:-1]:
                if row == 0 and column == 2:
                    btn = QPushButton(icon)
                    btn.clicked.connect(action)
                    btn.setFixedSize(50, 50)
                    grid.addWidget(btn, row, column, Qt.AlignmentFlag.AlignRight)
                    row, column = 1, 1
                    self.buttons[btn] = items[-1]

                grid.addWidget(QLabel(str(i)), row, column)
                column += 1

                if column == 3:
                    column = 1
                    row += 1

            return box

        future = DB.cur.execute(self.get_records + " AND records.status = 'new'").fetchall()
        past = DB.cur.execute(self.get_records + " AND records.status = 'completed'").fetchall()

        if future:
            for record in future:
                self.future_layout.addWidget(create_record(record, "×", self.delete))

        if past:
            for record in past:
                self.past_layout.addWidget(create_record(record, "⭯", self.repeat))

    def clear(self):
        for layout in (self.future_layout, self.past_layout):
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i).widget()
                layout.removeWidget(item)
                item.setParent(None)

    def delete(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Отмена записи")
        dlg.setText("Отменить запись?")
        dlg.setIcon(QMessageBox.Icon.Question)
        yes_btn = QPushButton("Да")
        yes_btn.setFixedSize(50, 50)
        no_btn = QPushButton("Нет")
        no_btn.setFixedSize(50, 50)
        dlg.addButton(yes_btn, QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton(no_btn, QMessageBox.ButtonRole.RejectRole)
        answer = dlg.exec()

        if answer == 2:
            record_id = self.buttons[self.sender()]
            schedule_id = DB.cur.execute("SELECT schedule FROM records WHERE record_id = ?", (record_id,)).fetchone()[0]
            DB.cur.execute("UPDATE records SET status = 'cancelled' WHERE record_id = ?", (record_id,))
            DB.cur.execute("UPDATE schedules SET status = 'available' WHERE schedule_id = ?", (schedule_id,))
            DB.con.commit()
            self.clear()
            self.add_records()

    def repeat(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Повтор записи")
        dlg.setText("Повтор записи временно недоступен")
        dlg.setIcon(QMessageBox.Icon.Critical)
        btn = QPushButton("ОК")
        btn.setFixedSize(50, 50)
        dlg.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
        dlg.exec()


class UserNewRecord(QWidget):

    def __init__(self, parent):
        super().__init__(None)
        uic.loadUi("ui/user_new_record.ui", self)

        self.parent, self.schedule_widget, self.schedule_id = parent, None, None
        self.data, self.first_step, self.branches, self.worker, self.service = [], None, None, None, None
        self.companies_buttons, self.branches_buttons, self.workers_buttons, self.services_buttons = {}, {}, {}, {}
        self.companies = DB.cur.execute("SELECT company_id, name FROM companies").fetchall()
        self.initUI()

        with open("qss/user_new_record.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def initUI(self):
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("Запись")
        self.setFixedSize(400, 400)

        self.company_widget.setLayout(self.company_layout)
        self.branch_widget.setLayout(self.branch_layout)
        self.worker_widget.setLayout(self.worker_layout)
        self.service_widget.setLayout(self.service_layout)
        self.company_edit.textChanged.connect(self.set_companies)
        self.set_companies()

        self.branch_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.branch_edit.textChanged.connect(self.set_branches)
        self.worker_btn.clicked.connect(self.main_next)
        self.service_btn.clicked.connect(self.main_next)
        self.worker_back_btn.clicked.connect(self.back)
        self.service_back_btn.clicked.connect(self.back)
        self.schedule_back_btn.clicked.connect(self.schedule_back)
        self.save_btn.clicked.connect(self.save)
        self.info_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))

    def set_companies(self):
        for i in reversed(range(self.company_layout.count())):
            item = self.company_layout.itemAt(i).widget()
            self.company_layout.removeWidget(item)
            item.setParent(None)

        for company, name in self.companies:
            if name.lower().startswith(self.company_edit.text().lower()):
                btn = QPushButton(name)
                btn.setMinimumHeight(40)
                btn.clicked.connect(self.company_next)
                self.companies_buttons[btn] = company
                self.company_layout.addWidget(btn)

    def company_next(self):
        self.data.append(self.companies_buttons.get(self.sender()))
        self.stack.setCurrentIndex(1)
        self.branches = DB.cur.execute("SELECT branch_id, name, address FROM branches WHERE company = ?",
                                       (self.data[0],)).fetchall()
        self.set_branches()

    def set_branches(self):
        for i in reversed(range(self.branch_layout.count())):
            item = self.branch_layout.itemAt(i).widget()
            self.branch_layout.removeWidget(item)
            item.setParent(None)

        for branch, name, address in self.branches:
            if name.lower().strip().startswith(self.branch_edit.text().strip().lower()):
                btn = QPushButton(name + " - " + address)
                btn.setMinimumHeight(40)
                btn.clicked.connect(self.branch_next)
                self.branches_buttons[btn] = branch
                self.branch_layout.addWidget(btn)

    def branch_next(self):
        self.data.append(self.branches_buttons.get(self.sender()))
        self.stack.setCurrentIndex(2)

    def main_next(self):
        btn = {self.worker_btn: (3, "worker"), self.service_btn: (4, "service")}
        self.first_step = btn.get(self.sender())[1]
        self.stack.setCurrentIndex(btn.get(self.sender())[0])
        self.set_workers()
        self.set_services()

    def back(self):
        if self.sender() == self.worker_back_btn:
            if self.first_step == "worker":
                self.stack.setCurrentIndex(1)
            else:
                self.stack.setCurrentIndex(4)
        else:
            if self.first_step == "worker":
                self.stack.setCurrentIndex(3)
            else:
                self.stack.setCurrentIndex(1)

    def set_workers(self):
        workers = DB.cur.execute("SELECT user_id, name FROM users WHERE company = ? AND role = 'worker'",
                                 (self.data[1],)).fetchall()

        for i in reversed(range(self.worker_layout.count())):
            item = self.worker_layout.itemAt(i).widget()
            self.worker_layout.removeWidget(item)
            item.setParent(None)

        for worker, name in workers:
            if name.lower().strip().startswith(self.worker_edit.text().strip().lower()):
                btn = QPushButton(name)
                btn.setMinimumHeight(40)
                btn.clicked.connect(self.worker_next)
                self.workers_buttons[btn] = worker
                self.worker_layout.addWidget(btn)

    def worker_next(self):
        self.worker = self.workers_buttons.get(self.sender())

        if self.first_step == "worker":
            self.stack.setCurrentIndex(4)
            self.set_services()
        else:
            self.stack.setCurrentIndex(5)
            self.set_schedule()

    def set_services(self):
        services = DB.cur.execute("SELECT service_id, title, price FROM services").fetchall()

        for i in reversed(range(self.service_layout.count())):
            item = self.service.itemAt(i).widget()
            self.service_layout.removeWidget(item)
            item.setParent(None)

        for service, name, price in services:
            if name.lower().strip().startswith(self.service_edit.text().strip().lower()):
                btn = QPushButton(name + " - " + str(price))
                btn.setMinimumHeight(40)
                btn.clicked.connect(self.service_next)
                self.services_buttons[btn] = service
                self.service_layout.addWidget(btn)

    def service_next(self):
        self.service = self.services_buttons.get(self.sender())

        if self.first_step == "worker":
            self.stack.setCurrentIndex(5)
            self.set_schedule()
        else:
            self.stack.setCurrentIndex(3)
            self.set_workers()

    def set_schedule(self):
        schedule = DB.cur.execute("""SELECT schedule_id, date, time FROM schedules WHERE worker = ?
                                  AND status = 'available'""", (self.worker,)).fetchall()
        try:
            if schedule:
                self.schedule_widget = Schedule(schedule, self.schedule_next)
                self.schedule_layout.addWidget(self.schedule_widget)
            else:
                raise ValueError
        except ValueError:
            self.schedule_error.setText("Не нашлось ни одного свободного\nвремени для записи")

    def schedule_back(self):
        if self.first_step == "worker":
            self.stack.setCurrentIndex(4)
            self.set_services()
        else:
            self.stack.setCurrentIndex(3)
            self.set_workers()

    def schedule_next(self):
        self.schedule_id = self.schedule_widget.records.get(self.sender())
        self.stack.setCurrentIndex(6)

    def save(self):
        comment = self.comment_edit.toPlainText()
        data = (None, self.parent.user, self.data[0], self.data[1], self.worker,
                self.service, self.schedule_id, (None if comment.strip() == "" else comment), "new")
        DB.cur.execute("UPDATE schedules SET status = 'booked' WHERE schedule_id = ?", (self.schedule_id,))
        DB.cur.execute("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        DB.con.commit()
        self.parent.clear()
        self.parent.add_records()
        self.close()
