import gzip
import json

# Third party imports
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QObject, QPoint
from PyQt5.QtGui import QValidator, QIntValidator, QDoubleValidator, QTextCursor
from si_prefix import si_parse
from pathvalidate import is_valid_filename

# Local imports
from . import get_class_from_string, get_object_class_name


def get_widget_value(widget):
    value = None

    # Call appropriate get function based on widget type
    if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QLabel)):
        value = widget.text()
    elif isinstance(widget, QtWidgets.QComboBox):
        value = widget.currentText()
    elif isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)):
        value = widget.isChecked()
    elif isinstance(widget, QtWidgets.QTableWidget):
        value = []
        for i in range(widget.rowCount()):
            row = []
            for j in range(widget.columnCount()):
                item = widget.item(i, j)
                item_value = None

                if item:
                    item_value = item.checkState() or item.text()

                row.append(item_value)

            value.append(row)

    return value


def set_widget_value(central_widget, widget_info):
    # Find widget object from class name
    class_name = get_class_from_string(widget_info['class'])
    widget = central_widget.findChild(class_name, widget_info['name'])

    value = widget_info['value']

    # Call appropriate set function based on widget type
    if isinstance(widget, QtWidgets.QLineEdit) and value:
        if widget.text() == value:
            widget.textChanged.emit(value)
        else:
            widget.setText(value)

        # Re-emit line edit signals
        widget.editingFinished.emit()
    elif isinstance(widget, QtWidgets.QLabel):
        widget.setText(value)
    elif isinstance(widget, QtWidgets.QComboBox):
        # Emit the currentTextChanged signal even if the state doesn't change
        if widget.currentText() == value:
            widget.currentTextChanged.emit(value)
        # (setCurrentText emits currentTextChanged when the state does change)
        else:
            widget.setCurrentText(value)
    elif isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)):
        # Emit the toggled signal even if the state doesn't change
        if widget.isChecked() == value:
            widget.toggled.emit(value)
        # (setChecked emits toggled when the state does change)
        else:
            widget.setChecked(value)
    elif isinstance(widget, QtWidgets.QTableWidget):
        for i in range(len(value)):                     # For each row
            for j, item_value in enumerate(value[i]):   # For each column
                item = widget.item(i, j)
                # If cell isn't None
                if item_value:
                    # Create a QTableWidgetItem if there isn't one already
                    if not item:
                        item = QtWidgets.QTableWidgetItem()
                        widget.setItem(i, j, item)

                    # If item_value is an int, it's a check state
                    if isinstance(item_value, int):
                        item.setCheckState(item_value)
                    # Text otherwise
                    elif isinstance(item_value, str):
                        item.setText(item_value)


def scan_column(table):
    values = np.array([])

    #####################
    # Get data from table
    #####################
    value = []
    for i in range(table.rowCount()):
        row = []
        item = table.item(i, 0)
        item_value = None

        if item:
            item_value = item.text()

        row.append(item_value)

        value.append(row)

    #########################
    # Filter out invalid data
    #########################
    valid_data_indices = []
    for i in range(len(value)):

        # Check to see if data is in all fields
        if not value[i][0]:
            continue

        # If it doesn't break before here add the current index as a good one
        valid_data_indices.append(i)

    #################################
    # Assemble data for next function
    #################################
    for i in valid_data_indices:
        values = np.append(values, float(value[i][0]))

    return values


def scan_bias_table(table):
    bias_values = []
    limit_values = []

    #####################
    # Get data from table
    #####################
    value = []
    for i in range(table.rowCount()):
        row = []
        for j in range(table.columnCount()):
            item = table.item(i, j)
            item_value = None

            if item:
                item_value = item.text()

            row.append(item_value)

        value.append(row)

    #########################
    # Filter out invalid data
    #########################
    valid_data_indices = []
    for i in range(len(value)):

        # Check to see if data is in all fields
        if not value[i][0] or not value[i][1]:
            continue

        # If it doesn't break before here add the current index as a good one
        valid_data_indices.append(i)

    #################################
    # Assemble data for next function
    #################################
    for i in valid_data_indices:
        bias_values.append(float(value[i][0]))
        limit_values.append(float(value[i][1]))

    return bias_values, limit_values


def scan_sweep_table(table, column_offset=0):
    starting_values = []
    ending_values = []
    num_steps_values = []
    step_size_values = []

    #####################
    # Get data from table
    #####################
    value = []
    for i in range(table.rowCount()):
        row = []
        for j in range(table.columnCount()):
            item = table.item(i, j+column_offset)
            item_value = None

            if item:
                item_value = item.text()

            row.append(item_value)

        value.append(row)

    #########################
    # Filter out invalid data
    #########################
    valid_data_indices = []
    for i in range(len(value)):

        # Check to see if data is in all fields
        if not value[i][0] or not value[i][1]:
            continue

        if not value[i][2] and not value[i][3]:
            continue

        # If it doesn't break before here add the current index as a good one
        valid_data_indices.append(i)

    #################################
    # Assemble data for next function
    #################################
    for i in valid_data_indices:
        starting_values.append(float(value[i][0]))
        ending_values.append(float(value[i][1]))
        try:
            step_size_values.append(float(value[i][2]))
        except (ValueError, TypeError):
            step_size_values.append(None)
        try:
            num_steps_values.append(int(value[i][3]))
        except (ValueError, TypeError):
            num_steps_values.append(None)

    return starting_values, ending_values, step_size_values, num_steps_values


def scan_sweep_table_checkbox(table):
    starting_values = []
    ending_values = []
    num_steps_values = []
    step_size_values = []

    #####################
    # Get data from table
    #####################
    value = []
    for i in range(table.rowCount()):
        row = []
        for j in range(table.columnCount()):
            item = table.item(i, j)
            item_value = None

            if item:
                item_value = item.checkState() or item.text()

            row.append(item_value)

        value.append(row)

    #########################
    # Filter out invalid data
    #########################
    valid_data_indices = []
    for i in range(len(value)):
        # Check to see if the box was checked
        if value[i][0] != Qt.Checked:
            continue

        # Check to see if data is in all fields
        if not value[i][1] or not value[i][2]:
            continue

        if not value[i][3] and not value[i][4]:
            continue

        # If it doesn't break before here add the current index as a good one
        valid_data_indices.append(i)

    #################################
    # Assemble data for next function
    #################################
    for i in valid_data_indices:
        starting_values.append(float(value[i][1]))
        ending_values.append(float(value[i][2]))
        try:
            step_size_values.append(float(value[i][3]))
        except (ValueError, TypeError):
            step_size_values.append(None)
        try:
            num_steps_values.append(int(value[i][4]))
        except (ValueError, TypeError):
            num_steps_values.append(None)

    return starting_values, ending_values, step_size_values, num_steps_values


def get_widget_info(widget):
    return {
        'class': get_object_class_name(widget),
        'name': widget.objectName(),
        'value': get_widget_value(widget)
    }


def save_to_json_gz(data, path, file_name=''):
    if not file_name:
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', str(path), 'GZ files (*.gz)')

    # If user didn't cancel out of the dialog
    if file_name:
        with gzip.open(path / file_name, 'wt', encoding='utf-8') as f:
            json.dump(data, f)


def load_from_json_gz(path, file_name=''):
    if not file_name:
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open File', str(path), 'GZ files (*.gz)')

    file_path = path / file_name

    # If user didn't cancel out of the dialog and the path exists
    if file_name and file_path.exists():
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return json.load(f)


# Icon options: QMessageBox.Critical, QMessageBox.Information, QMessageBox.Question, QMessageBox.Warning
def display_message(icon, title, text):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.exec()


def toggle_combo_box_item(combo_box, index, enabled):
    combo_box.model().item(index).setEnabled(enabled)


class TableItemDelegate(QtWidgets.QItemDelegate):
    def setBottom(self, bottom):
        self.validator.setBottom(bottom)

    def setTop(self, top):
        self.validator.setTop(top)

    def createEditor(self, parent, option, index):
        line_edit = QtWidgets.QLineEdit(parent)
        line_edit.setValidator(self.validator)

        return line_edit


class IntTableItemDelegate(TableItemDelegate):
    def __init__(self, default_value='', si=False, parent=None):
        super().__init__(parent)
        self.validator = IntValidator(default_value, si)


class FloatTableItemDelegate(TableItemDelegate):
    def __init__(self, default_value='', si=False, parent=None):
        super().__init__(parent)
        self.validator = FloatValidator(default_value, si)


# Subclass double and int validators to add a default value for invalid input and call editingFinished regardless
class FloatValidator(QDoubleValidator):
    def __init__(self, default_value='', si=False, parent=None):
        super().__init__(parent)
        self.default_value = str(default_value)
        # If accepting SI prefixes, use si_parse. Otherwise, parse as float
        self.parse = si_parse if si else float

        # Flag is necessary so that intermediate input is not immediately passed back to validate to be fixed up again
        self.fixed_up = False

    def fixup(self, input):
        self.fixed_up = True
        return self.default_value

    def validate(self, input, pos):
        # Immediately invalidate input that starts negative when only positive is accepted
        if input == '-' and self.bottom() >= 0:
            return QValidator.Invalid, input, pos

        # Fixup empty string and partial decimals/negatives (if we haven't fixed up already)
        if not self.fixed_up and (not input or input in ('.', '-', '-.')):
            return QValidator.Intermediate, input, pos
        else:
            # Check that input is:
            # a) fixed up
            # or
            # b) can be cast to a float and is within the range specified
            if self.fixed_up:
                self.fixed_up = False
                return QValidator.Acceptable, input, pos

            try:
                # Users can't easily type 'µ', so replace 'u' in the input
                input = input.replace('u', 'µ')

                # Strip trailing decimal point in intermediate floating point values, as si_parse will fail to parse
                # valid floats otherwise
                parsed_input = self.parse(input[:-1] if input.count('.') == 1 and input.endswith('.') else input)
                if self.bottom() <= parsed_input <= self.top():
                    return QValidator.Acceptable, input, pos
            except (AttributeError, ValueError, AssertionError):
                pass

            return QValidator.Invalid, input, pos


class IntValidator(QIntValidator):
    def __init__(self, default_value='', si=False, parent=None):
        super().__init__(parent)
        self.default_value = str(default_value)
        # If accepting SI prefixes, use si_parse. Otherwise, parse as int
        self.parse = si_parse if si else int

        # Flag is necessary so that intermediate input is not immediately passed back to validate to be fixed up again
        self.fixed_up = False

    def fixup(self, input):
        self.fixed_up = True
        return self.default_value

    def validate(self, input, pos):
        # Immediately invalidate input that starts negative when only positive is accepted
        if input == '-' and self.bottom() >= 0:
            return QValidator.Invalid, input, pos

        # Fixup empty string and partial negatives (if we haven't fixed up already)
        if not self.fixed_up and (not input or input == '-'):
            return QValidator.Intermediate, input, pos
        else:
            # Accept input if already fixed up
            if self.fixed_up:
                self.fixed_up = False
                return QValidator.Acceptable, input, pos

            # Try to parse input using selected method and validate range
            try:
                # Users can't easily type 'µ', so replace 'u' in the input
                input = input.replace('u', 'µ')
                if self.bottom() <= self.parse(input) <= self.top():
                    return QValidator.Acceptable, input, pos
            except (AttributeError, ValueError, AssertionError):
                pass

            # Reject input if all else fails
            return QValidator.Invalid, input, pos


class FilenameValidator(QValidator):
    def __init__(self, default_value='', parent=None):
        super().__init__(parent)
        self.default_value = default_value

        self.fixed_up = False

    def fixup(self, input):
        self.fixed_up = True
        return self.default_value

    def validate(self, input, pos):
        # Fixup empty string
        if not self.fixed_up and not input:
            return QValidator.Intermediate, input, pos
        else:
            # Accept input if already fixed up
            if self.fixed_up:
                self.fixed_up = False
                return QValidator.Acceptable, input, pos

            # Attempt to validate input
            if is_valid_filename(input):
                return QValidator.Acceptable, input, pos
            else:
                position = self.parent().mapToGlobal(QPoint(0, 0))
                QtWidgets.QToolTip.showText(position, 'Must be a valid Windows filename.')
                return QValidator.Invalid, input, pos


class PopupComboBox(QtWidgets.QComboBox):
    popup = pyqtSignal()

    def showPopup(self):
        self.popup.emit()
        super().showPopup()


class ClickMenu(QtWidgets.QMenu):
    clicked = pyqtSignal(object)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit(e)


class TimeoutMessageBox(QtWidgets.QMessageBox):
    def __init__(self, *args, timeout=15, default_result=QtWidgets.QMessageBox.Ok, default_text='Continue', **kwargs):
        super().__init__(*args, **kwargs)

        self.timeout = timeout                  # Time before message box times out
        self.default_result = default_result    # Default result that is returned after timeout
        self.default_text = default_text        # Text of the default button

        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        self.setDefaultButton(default_result)

        # Initialize timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timeout)

        # Initialize default button text
        self.update_default_button_text()

    def exec(self):
        self.timer.start(1000)
        return super().exec()

    def update_default_button_text(self):
        self.button(self.default_result).setText(f'{self.default_text} ({self.timeout})')

    def update_timeout(self):
        self.timeout -= 1
        if self.timeout == 0:
            self.done(self.default_result)

        self.update_default_button_text()


class SplitTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cells = []
        self.cellActivated.connect(self.highlight_cell)

    def highlight_cell(self, row, column):
        left, right = self.cells[row][column]
        left.setStyleSheet('background-color: #0f0')
        right.setStyleSheet('background-color: #0f0')

    def split_cells(self, left, right):
        for i in range(self.rowCount()):
            row = []

            for j in range(self.columnCount()):
                cell_widget = QtWidgets.QWidget()
                cell_layout = QtWidgets.QHBoxLayout(cell_widget)

                # Construct label label
                left_label = QtWidgets.QLabel(left)
                left_label.setAlignment(Qt.AlignCenter)

                # Construct separator
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.VLine)
                line.setStyleSheet('color: #c8c8c8')
                line.setMaximumWidth(1)

                # Construct right label
                right_label = QtWidgets.QLabel(right)
                right_label.setAlignment(Qt.AlignCenter)

                row.append((left_label, right_label))

                # Add widgets to layout
                cell_layout.addWidget(left_label)
                cell_layout.addWidget(line)
                cell_layout.addWidget(right_label)

                # Remove margins/spacing from layout
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.setSpacing(0)

                self.setCellWidget(i, j, cell_widget)

            self.cells.append(row)


class OutputLog(QObject):
    text_ready = pyqtSignal(str)

    def __init__(self, text_widget, stream=None, color=''):
        super().__init__()

        self.text_widget = text_widget
        self.stream = stream
        self.color = color

        self.text_ready.connect(self.insertHtml)

    def insertHtml(self, html):
        self.text_widget.moveCursor(QTextCursor.End)
        self.text_widget.textCursor().insertHtml(html)
        self.text_widget.moveCursor(QTextCursor.End)

    def write(self, s):
        # Write to alternative stream (if defined)
        if self.stream:
            self.stream.write(s)

        # Format string as HTML
        html = f'<pre><font color="{self.color}">{s}</font></pre>'

        self.text_ready.emit(html)
