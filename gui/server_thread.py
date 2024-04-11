from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMainWindow, QTextEdit
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import os


class ServerProcess(QThread):
    output_received = pyqtSignal(str)

    def run(self):
        # run this once only
        # os.chdir("src")
        process = subprocess.Popen(
            ["../.venv/bin/python", "-m", "uvicorn", "server.main:app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd="src"
        )
        while True:
            output = process.stdout.readline().decode().strip()
            if output:
                self.output_received.emit(output)
            else:
                break


def open_server_log_popup(self):
    if self.server_log_popup is not None:
        close_server_log_popup(self)
    else:
        self.server_log_popup = ServerLogPopup(
            self)  # Create instance, pass 'self'
        self.server_log_popup.show()  # Use .show() instead of .exec()

    # if called while the logs are already being displayed close them


def close_server_log_popup(self):
    self.server_log_popup.close()
    self.server_log_popup = None


class ServerLogPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Server Log")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()  # Create a layout
        self.text_edit = QTextEdit(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)  # Set the layout

    def update_log(self, new_text):
        self.text_edit.append(new_text)  # Or use setText() to replace content


def init_server_process(self) -> ServerProcess:

    self.server_thread = ServerProcess()

    return self.server_thread
