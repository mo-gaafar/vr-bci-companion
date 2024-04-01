import logging
import sys
from gui import interface


from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSlot


from gui.server_thread import init_server_process


class ServerControlGUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ServerControlGUI, self).__init__(*args, **kwargs)
        uic.loadUi('./gui/MainWindow.ui', self)

        # set the title and icon
        self.setWindowIcon(QtGui.QIcon('./gui/icons/icon.png'))
        self.setWindowTitle("NeuroRehab Connect")

        # initialize global variables
        self.server_process = None
        self.server_log_popup = None

        # initialize ui connectors
        interface.init_connectors(self)

        interface.init_layout(self)

    @pyqtSlot(str)
    def append_output(self, text):
        if self.server_log_popup is not None:
            self.server_log_popup.update_log(text)
        # self.text_edit.append(text)


# sys.path.append('/src/')


def main():
    try:
        app = QApplication(sys.argv)
        gui = ServerControlGUI()
        gui.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.basicConfig(filename='app_errors.log', level=logging.ERROR)
        logging.error("An error occurred:", exc_info=e)


if __name__ == '__main__':
    main()
