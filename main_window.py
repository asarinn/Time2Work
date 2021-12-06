from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
import datetime

from main_window_init import Ui_TimeToWork


class MainWindow(QMainWindow):
    MINUTES_REQUIRED = 2520

    def __init__(self):

        super().__init__()

        # Basic PyQt init for window
        self.ui = Ui_TimeToWork()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.ui.time_entry_table.itemChanged.connect(self.update_time)

    def update_time(self):
        worked_minutes = 0
        unfinished_days = 0
        for i in range(self.ui.time_entry_table.rowCount()):
            try:
                unfinished = True

                for j in range(self.ui.time_entry_table.columnCount()):
                    # print(j, self.ui.time_entry_table.item(i, j).text())
                    if j%2 == 0:  # Even numbers
                        temp_worked_minutes = self.get_minutes(self.ui.time_entry_table.item(i, j+1).text()) - self.get_minutes(self.ui.time_entry_table.item(i, j).text())
                        if temp_worked_minutes > 0:
                            worked_minutes += temp_worked_minutes
                            unfinished = False

            except:
                print(f' i={i} ')
                if unfinished and i < 5:
                    unfinished_days += 1
                print(f' unfinished_days={unfinished_days}')

        remaining_minutes = self.MINUTES_REQUIRED - worked_minutes
        hours = int(abs(remaining_minutes)/60)
        minutes = int(abs(remaining_minutes) - 60 * hours)

        # FLip sign only once if negative
        if remaining_minutes < 0:
            sign = '-'
        else:
            sign = ''

        if minutes < 10:
            minutes = f'0{minutes}'

        try:
            remaining_minutes_per_day = remaining_minutes/unfinished_days
            hours_per_day = int(abs(remaining_minutes_per_day)/60)
            minutes_per_day = int(abs(remaining_minutes_per_day) - 60 * hours_per_day)
        except ZeroDivisionError:
            remaining_minutes_per_day = 0
            hours_per_day = 0
            minutes_per_day = 0

        if remaining_minutes_per_day < 0:
            day_sign = '-'
        else:
            day_sign = ''

        if minutes_per_day < 10:
            minutes_per_day = f'0{minutes_per_day}'

        self.ui.time_left_label.setText(f'Time left this week: {sign}{hours}:{minutes}')
        self.ui.time_left_per_day_label.setText(f'Time left per remaining weekday: {day_sign}{hours_per_day}:{minutes_per_day}')

    def get_minutes(self, time):
        t1 = datetime.datetime.strptime(time, '%H:%M')
        t2 = datetime.datetime(1900, 1, 1)

        return (t1 - t2).total_seconds() / 60.0
