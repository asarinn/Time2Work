import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from common import get_config_path
from common.qt import display_message, set_widget_value, load_from_json_gz, save_to_json_gz, get_widget_info
from main_window import MainWindow

APP_PUBLISHER = 'Mike Projects'
APP_NAME = 'TimeToWork'

CONFIG_DIRECTORY = get_config_path(APP_PUBLISHER, APP_NAME)
GUI_SETTINGS_AUTOSAVE_FILE_NAME = 'gui_settings_autosave.gz'


class WeeklyTimeTracker:
    def __init__(self):

        # Initialize Qt sys
        self.app = QApplication(sys.argv)
        self.app.setStyle("fusion")

        self.main_window = MainWindow()

        self.main_window.destroyed.connect(self.save_settings)
        self.load_settings()

    def get_settings(self):
        ui = self.main_window.ui
        main_window_widgets = {
            ui.time_entry_table
        }

        return {
            'main_window': [get_widget_info(w) for w in main_window_widgets],
        }

    def save_settings(self):
        file_name = 'time_tracker_auto_save.gz'
        save_to_json_gz(self.get_settings(), CONFIG_DIRECTORY, file_name)

    def load_settings(self):
        file_name = 'time_tracker_auto_save.gz'
        try:
            # Get settings from file
            settings = load_from_json_gz(CONFIG_DIRECTORY, file_name)

            if settings:
                # Return if attempting to load from autosave and user has disabled autosave
                if file_name == GUI_SETTINGS_AUTOSAVE_FILE_NAME:
                    return
            # Return if user canceled out of load dialog
            else:
                return

            # Set widget values for each window
            central_widget = self.main_window.ui.centralwidget
            for widget_info in settings['main_window']:
                set_widget_value(central_widget, widget_info)

        except Exception as e:
            display_message(QMessageBox.Critical, 'Error', f'Invalid settings file: {e}')


# Create instance of main control class
instance = WeeklyTimeTracker()

# Start by showing the main window
instance.main_window.show()

# Execute and close on end on program exit
sys.exit(instance.app.exec())
