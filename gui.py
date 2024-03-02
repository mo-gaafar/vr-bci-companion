import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

sys.path.append('/src/')


class ServerControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('FastAPI Server Control')
        self.setGeometry(100, 100, 200, 100)

        layout = QVBoxLayout()

        self.start_button = QPushButton('Start Server', self)
        self.start_button.clicked.connect(self.start_server)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Server', self)
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)  # Disabled until server starts
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_server(self):
        if self.server_process is None:
            # Start the FastAPI server as a subprocess
            self.server_process = subprocess.Popen(
                ['uvicorn', 'src.main:app', '--reload'])
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def stop_server(self):
        if self.server_process is not None:
            # Terminate the subprocess running the FastAPI server
            self.server_process.terminate()
            self.server_process = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    gui = ServerControlGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
