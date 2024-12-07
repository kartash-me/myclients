import os
import sys
import string
import hashlib
import datetime as dt

from data import DB
from admin import AdminMain
from worker import WorkerMain
from user import UserMain

from PyQt6 import uic
from PyQt6.QtGui import QIcon, QImage, QIntValidator, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


class Authorization(QWidget):
    MONTHS = ["Месяц", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
              "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    GENDERS = ["Пол", "Не указан", "Мужской", "Женский", "Другой"]
    NORMAL = "QLineEdit { border: 1px solid darkgrey; } QLineEdit:focus { border: 2px solid white; }"

    def __init__(self):
        super().__init__(None)
        uic.loadUi("ui/authorization.ui", self)
        self.date_of_birth, self.phone, self.role, self.widget, self.company, self.key = (None for _ in range(6))
        self.branches = {}
        self.initUI()

        with open("qss/authorization.qss", "r") as qss:
            self.setStyleSheet(qss.read())

    def initUI(self):
        self.stack.setCurrentIndex(0)
        self.setFixedSize(400, 400)
        self.non_registration_btn.hide()

        image = QImage("logo.png").scaled(370, 90)
        self.main_label.setPixmap(QPixmap.fromImage(image))

        self.sign_in_btn.clicked.connect(self.sign_in)
        self.create_account_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.login_edit.textChanged.connect(lambda: self.login_edit.setStyleSheet(self.NORMAL))
        self.pass_edit.textChanged.connect(lambda: self.pass_edit.setStyleSheet(self.NORMAL))
        self.pass_edit.returnPressed.connect(self.sign_in)

        self.name_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.name_next_btn.clicked.connect(self.name_next)
        self.name_edit.textChanged.connect(lambda: self.name_edit.setStyleSheet(self.NORMAL))
        self.surname_edit.textChanged.connect(lambda: self.surname_edit.setStyleSheet(self.NORMAL))
        self.surname_edit.returnPressed.connect(self.name_next)

        self.data_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.data_next_btn.clicked.connect(self.data_next)
        self.month.addItems(self.MONTHS)
        self.gender.addItems(self.GENDERS)
        self.date.setValidator(QIntValidator(0, 99, self.date))
        self.year.setValidator(QIntValidator(0, 9999, self.year))
        self.month.currentTextChanged.connect(lambda: self.month.setStyleSheet("border: 1px solid darkgrey"))
        self.gender.currentTextChanged.connect(lambda: self.gender.setStyleSheet("border: 1px solid darkgrey"))
        self.date.textChanged.connect(lambda: self.date.setStyleSheet(self.NORMAL))
        self.year.textChanged.connect(lambda: self.year.setStyleSheet(self.NORMAL))

        self.login_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.login_next_btn.clicked.connect(self.login_next)
        self.new_login_edit.textChanged.connect(lambda: self.new_login_edit.setStyleSheet(self.NORMAL))
        self.new_login_edit.returnPressed.connect(self.login_next)

        self.pass_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.pass_next_btn.clicked.connect(self.pass_next)
        self.first_pass_edit.textChanged.connect(self.pass_edited)
        self.second_pass_edit.returnPressed.connect(self.pass_next)

        self.phone_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.phone_next_btn.clicked.connect(self.phone_next)
        self.phone_edit.textChanged.connect(lambda: self.phone_edit.setStyleSheet(self.NORMAL))
        self.phone_edit.returnPressed.connect(self.phone_next)

        self.role_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.role_next_btn.clicked.connect(self.role_next)

        self.code_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.code_next_btn.clicked.connect(self.code_next)

        self.branch_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))
        self.branch_next_btn.clicked.connect(self.branch_next)

        self.key_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.key_next_btn.clicked.connect(self.key_next)

        self.company_back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(9))
        self.company_next_btn.clicked.connect(self.company_next)

        self.main_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.log_in_btn.clicked.connect(self.log_in)

    def sign_in(self):
        if self.login_edit.text().strip() == "":
            self.error_label.setText("Логин не указан")
            self.login_edit.setStyleSheet("border: 2px solid red")
        elif self.pass_edit.text().strip() == "":
            self.error_label.setText("Пароль не указан")
            self.pass_edit.setStyleSheet("border: 2px solid red")
        else:
            login = self.login_edit.text()
            password = self.pass_edit.text()
            result = DB.cur.execute("SELECT role, password, salt FROM users WHERE login == ?",
                                    (login,)).fetchall()

            if result:
                role, true_password, salt = result.pop()

                if check_elem(true_password, salt, password):
                    if self.remember.isChecked():
                        sn = serial_number()
                        DB.cur.execute("UPDATE users SET sn = ? WHERE login = ?", (sn, login))

                        with open("cookie.txt", "w", encoding="utf-8") as file:
                            file.write(login)

                    DB.con.commit()
                    self.close()

                    if role == "admin":
                        self.widget = AdminMain(login)
                        self.widget.show()
                    elif role == "worker":
                        self.widget = WorkerMain(login)
                        self.widget.show()
                    elif role == "user":
                        self.widget = UserMain(login)
                        self.widget.show()
                else:
                    self.error_label.setText("Неверный пароль")
                    self.pass_edit.setStyleSheet("border: 2px solid red")
            else:
                self.error_label.setText("Неверный логин")
                self.pass_edit.setStyleSheet(self.NORMAL)
                self.login_edit.setStyleSheet("border: 2px solid red")

    def name_next(self):
        if self.name_edit.text() == "":
            self.name_error_label.setText("Имя не указано")
            self.name_edit.setStyleSheet("border: 2px solid red")
        elif self.surname_edit.text() == "":
            self.name_error_label.setText("Фамилия не указана")
            self.surname_edit.setStyleSheet("border: 2px solid red")
        else:
            self.name_error_label.setText("")
            self.stack.setCurrentIndex(2)

    def data_next(self):
        try:
            date_tmp = dt.date(int(self.year.text()), self.month.currentIndex(), int(self.date.text()))

            if int(self.year.text()) < 1900 or date_tmp > dt.date.today():
                raise ValueError("year is out of range")
            elif self.gender.currentText() == "Пол":
                self.data_error_label.setText(" Укажите пол")
                self.gender.setStyleSheet("border: 2px solid red")
                self.date.setStyleSheet(self.NORMAL)
                self.month.setStyleSheet("border: 1px solid darkgrey")
                self.year.setStyleSheet(self.NORMAL)
            else:
                self.date_of_birth = date_tmp.strftime("%d.%m.%Y")
                self.data_error_label.setText("")
                self.date.setStyleSheet(self.NORMAL)
                self.month.setStyleSheet("border: 1px solid darkgrey")
                self.year.setStyleSheet(self.NORMAL)
                self.gender.setStyleSheet("border: 1px solid darkgrey")
                self.stack.setCurrentIndex(3)

        except ValueError:
            self.data_error_label.setText(" Укажите правильную дату")
            self.date.setStyleSheet("border: 2px solid red")
            self.month.setStyleSheet("border: 2px solid red")
            self.year.setStyleSheet("border: 2px solid red")

    def login_next(self):
        login = self.new_login_edit.text()

        if len(login) == 0:
            self.login_error_label.setText(" Придумайте логин")
            self.new_login_edit.setStyleSheet("border: 2px solid red")
        elif len(login) < 6:
            self.login_error_label.setText(" Логин не может быть короче 6 символов")
            self.new_login_edit.setStyleSheet("border: 2px solid red")
        elif login[0].isdigit():
            self.login_error_label.setText(" Логин не может начинаться с цифры")
            self.new_login_edit.setStyleSheet("border: 2px solid red")
        elif not all(i in string.ascii_letters + string.digits + "._" for i in login) or " " in login:
            self.login_error_label.setText(" Логин может содержать только\n латинские буквы, точку и подчёркивание")
            self.new_login_edit.setStyleSheet("border: 2px solid red")
        else:
            result = DB.cur.execute("SELECT login FROM users WHERE login = ?", (login,)).fetchone()

            if result:
                self.login_error_label.setText(" Такой логин уже занят")
                self.new_login_edit.setStyleSheet("border: 2px solid red")
            else:
                self.login_error_label.setText("")
                self.stack.setCurrentIndex(4)

    def pass_edited(self):
        self.pass_error_label.setStyleSheet("color: white")

        password = self.first_pass_edit.text()
        progress = 0
        progress_color = {0: "transparent", 25: "red", 50: "orange", 75: "yellow", 100: "green"}

        if len(password) >= 8:
            self.symbols_label.setText(f" ✓ {self.symbols_label.text()[3:]}")
            self.symbols_label.setStyleSheet("color: green")
            progress += 25
        else:
            self.symbols_label.setText(f" • {self.symbols_label.text()[3:]}")
            self.symbols_label.setStyleSheet("color: white")

        if any(i in string.ascii_lowercase for i in password):
            self.lower_label.setText(f" ✓ {self.lower_label.text()[3:]}")
            self.lower_label.setStyleSheet("color: green")
            progress += 25
        else:
            self.lower_label.setText(f" • {self.lower_label.text()[3:]}")
            self.lower_label.setStyleSheet("color: white")

        if any(i in string.ascii_uppercase for i in password):
            self.upper_label.setText(f" ✓ {self.upper_label.text()[3:]}")
            self.upper_label.setStyleSheet("color: green")
            progress += 25
        else:
            self.upper_label.setText(f" • {self.upper_label.text()[3:]}")
            self.upper_label.setStyleSheet("color: white")

        if any(i in string.digits for i in password):
            self.num_label.setText(f" ✓ {self.num_label.text()[3:]}")
            self.num_label.setStyleSheet("color: green")
            progress += 25
        else:
            self.num_label.setText(f" • {self.num_label.text()[3:]}")
            self.num_label.setStyleSheet("color: white")

        self.progress_bar.setValue(progress)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: %s; }" % progress_color[progress])

    def pass_next(self):
        self.params.hide()
        self.progress_bar.hide()
        self.pass_error_label.setText("")

        if self.progress_bar.value() == 100:
            if self.first_pass_edit.text() == self.second_pass_edit.text():
                self.pass_error_label.setText("")
                self.pass_error_label.setStyleSheet("color: white")
                self.stack.setCurrentIndex(5)
            else:
                self.pass_error_label.setText(" Пароли не совпадают")
                self.pass_error_label.setStyleSheet("color: red")
        else:
            self.pass_error_label.setText(" Пароль не соответствует требованиям")
            self.pass_error_label.setStyleSheet("color: red")

    def phone_next(self):
        phone = self.phone_edit.text().strip()

        if phone == "":
            self.phone_error_label.setText(" Введите номер телефона")
            self.phone_edit.setStyleSheet("border: 2px solid red")
        elif phone.startswith("8") or phone.startswith("+7"):
            phone = phone.replace("+7", "8", 1)

            if phone.isdigit():
                if len(phone) == 11:
                    result = DB.cur.execute("SELECT phone FROM users WHERE phone = ?", (phone,)).fetchone()

                    if result:
                        self.phone_error_label.setText(" Этот номер уже зарегистрирован")
                        self.phone_edit.setStyleSheet("border: 2px solid red")
                    else:
                        self.phone_error_label.setText("")
                        self.phone = phone
                        self.stack.setCurrentIndex(6)
                else:
                    self.phone_error_label.setText(" Неверный номер")
                    self.phone_edit.setStyleSheet("border: 2px solid red")
            else:
                self.phone_error_label.setText(" Номер может состоять только из цифр")
                self.phone_edit.setStyleSheet("border: 2px solid red")
        else:
            self.phone_error_label.setText(" Номер должен начинаться с +7 или 8")
            self.phone_edit.setStyleSheet("border: 2px solid red")

    def role_next(self):
        role = self.roles.checkedButton().text()

        if role == "Сотрудник":
            self.stack.setCurrentIndex(7)
        elif role == "Администратор":
            self.stack.setCurrentIndex(9)
        else:
            self.role = "user"
            data = (None, self.new_login_edit.text(), self.role, None, *hash_elem(self.first_pass_edit.text()),
                    self.name_edit.text(), self.surname_edit.text(), self.phone, self.date_of_birth,
                    self.gender.currentText(), None, None)

            DB.cur.execute("""INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            DB.con.commit()

            self.stack.setCurrentIndex(9)

    def code_next(self):
        code = self.code_input.toPlainText().strip()

        if code == "":
            self.code_error_label.setText("Введите код сотрудника")
        else:
            self.company = DB.cur.execute("SELECT company_id FROM companies WHERE invite = ?", (code,)).fetchone()

            if self.company:
                branches = DB.cur.execute("SELECT branch_id, name, address FROM branches WHERE company = ?",
                                          (self.company[0],)).fetchall()

                if branches:
                    self.stack.setCurrentIndex(8)
                    self.branch_box.addItem("Филиал")
                    self.code_error_label.setText("")

                    for branch_id, name, address in branches:
                        self.branch_box.addItem(f"{name} - {address}")
                        self.branches[f"{name} - {address}"] = branch_id
                else:
                    self.code_error_label.setText("У компании нет ни одного филиала")
            else:
                self.code_error_label.setText("Неверный код сотрудника")

    def branch_next(self):
        if self.branch_box.currentText() == "Филиал":
            self.branch_error_label.setText(" Укажите филиал")
        else:
            branch = self.branches.get(self.branch_box.currentText())
            self.role = "worker"
            data = (None, self.new_login_edit.text(), self.role, None, *hash_elem(self.first_pass_edit.text()),
                    self.name_edit.text(), self.surname_edit.text(), self.phone, self.date_of_birth,
                    self.gender.currentText(), branch, None)

            DB.cur.execute("""INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            DB.con.commit()

            self.stack.setCurrentIndex(11)

    def key_next(self):
        key = self.key_input.toPlainText().strip()

        if key == "":
            self.key_error_label.setText("Введите лицензионный ключ")
        else:
            result = DB.cur.execute("SELECT key_id, status FROM keys WHERE key = ?",
                                    (hash_elem_without_salt(key),)).fetchone()
            key_id, status = result if result else (None, None)

            if status == "available":
                self.key_error_label.setText("")
                self.key = key_id
                self.stack.setCurrentIndex(10)
            elif status == "active":
                self.key_error_label.setText("Этот лицензионный ключ используется")
            elif status == "blocked":
                self.key_error_label.setText("Этот лицензионный ключ заблокирован")
            else:
                self.key_error_label.setText("Неверный лицензионный ключ")

    def company_next(self):
        company = self.company_edit.text()

        if company.strip() == "":
            self.company_error_label.setText("Введите название компании")
        else:
            result = DB.cur.execute("SELECT name FROM companies WHERE name = ?", (company,)).fetchone()

            if result:
                self.company_error_label.setText("Такая компания уже зарегистрирована")
            else:
                self.role = "admin"
                DB.cur.execute("UPDATE keys SET status = 'active' WHERE key_id = ?", (self.key,))
                data = (None, self.new_login_edit.text(), self.role, None, *hash_elem(self.first_pass_edit.text()),
                        self.name_edit.text(), self.surname_edit.text(), self.phone, self.date_of_birth,
                        self.gender.currentText(), None, self.key)
                DB.cur.execute("""INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
                DB.con.commit()
                user = DB.cur.execute("SELECT user_id FROM users WHERE login = ?",
                                      (self.new_login_edit.text(),)).fetchone()[0]
                DB.cur.execute("INSERT INTO companies VALUES (?, ?, ?, ?, ?)", (None, self.key, user, company, None))
                DB.con.commit()
                company_id = DB.cur.execute("SELECT company_id FROM companies WHERE admin = ?", (user,)).fetchone()[0]
                DB.cur.execute("UPDATE users SET company = ? WHERE user_id = ?", (company_id, user,))
                DB.con.commit()
                self.stack.setCurrentIndex(11)

    def log_in(self):
        login = self.new_login_edit.text()

        if self.confirm_remember.isChecked():
            sn = serial_number()
            DB.cur.execute("UPDATE users SET sn = ? WHERE login = ?", (sn, login))

            with open("cookie.txt", "w", encoding="utf-8") as file:
                file.write(login)

        DB.con.commit()
        self.close()

        if self.role == "admin":
            self.widget = AdminMain(login)
            self.widget.show()
        elif self.role == "worker":
            self.widget = WorkerMain(login)
            self.widget.show()
        elif self.role == "user":
            self.widget = UserMain(login)
            self.widget.show()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def serial_number():
    os_type = sys.platform.lower()

    if "win" in os_type:
        command = "wmic bios get serialnumber"
    elif "linux" in os_type:
        command = "hal-get-property --udi /org/freedesktop/Hal/devices/computer --key system.hardware.uuid"
    elif "darwin" in os_type:
        command = "ioreg -l | grep IOPlatformSerialNumber"
    else:
        command = ""

    return os.popen(command).read().replace("\n", "").replace(" ", "")[12:]


def hash_elem_without_salt(elem):
    return hashlib.sha256(elem.encode()).hexdigest()


def hash_elem(elem):
    salt = os.urandom(16).hex()
    return hashlib.sha256((salt + elem).encode()).hexdigest(), salt


def check_elem(true_elem, salt, input_elem):
    return true_elem == hashlib.sha256((salt + input_elem).encode()).hexdigest()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))

    try:
        with open("cookie.txt", "r", encoding="utf-8") as text:
            cookie = text.read().strip()
            ser_num = serial_number()
            res = DB.cur.execute("SELECT login, role FROM users WHERE login == ? AND sn == ?",
                                 (cookie, ser_num)).fetchall()

            if res:
                if res[0][1] == "admin":
                    widget = AdminMain(res[0][0])
                    widget.show()
                elif res[0][1] == "worker":
                    widget = WorkerMain(res[0][0])
                    widget.show()
                elif res[0][1] == "user":
                    widget = UserMain(res[0][0])
                    widget.show()
            else:
                widget = Authorization()
                widget.show()

    except FileNotFoundError:
        widget = Authorization()
        widget.show()

    sys.excepthook = except_hook
    sys.exit(app.exec())
