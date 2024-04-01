import sys
from gui import interface


from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import QtGui, uic


class ServerControlGUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ServerControlGUI, self).__init__(*args, **kwargs)
        uic.loadUi('./gui/MainWindow.ui', self)

        # set the title and icon
        self.setWindowIcon(QtGui.QIcon('./gui/icons/icon.png'))
        self.setWindowTitle("NeuroRehab Connect")

        # initialize global variables
        self.server_process = None

        # initialize ui connectors
        interface.init_connectors(self)

        interface.init_layout(self)


# sys.path.append('/src/')


def main():
    app = QApplication(sys.argv)
    gui = ServerControlGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
