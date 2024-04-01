

import os
import subprocess

from gui.server_thread import open_server_log_popup


def init_connectors(self):
    """Initializes the connectors of PyQt GUI"""
    self.comboBox_connection.currentIndexChanged.connect(
        lambda: connection_protocol_combobox(self))

    self.pushButton_LSL_lock.clicked.connect(
        lambda: lsl_lock_in_toggle(self))

    self.pushButton_start_backend.clicked.connect(lambda: toggle_server(self))
    self.pushButton_backend_logs.clicked.connect(
        lambda: open_server_log_popup(self))


def get_LSL_config(self):
    """Gets the LSL configuration from PyQt GUI

    Returns:
        dict: LSL configuration

    """
    # get LSL configuration
    lsl_config = {
        "stream_1": {"name": self.lineEdit_stream1name.text(),
                     "type": self.comboBox_stream1dt.currentText()},
        "stream_2": {"name": self.lineEdit_stream2name.text(),
                     "type": self.comboBox_stream2dt.currentText()},
        "stream_3": {"name": self.lineEdit_stream3name.text(),
                     "type": self.comboBox_stream3dt.currentText()},
    }
    return lsl_config


def init_layout(self):
    """Initializes the layout of PyQt GUI"""
    # hide groupSerial and groupLSL
    self.groupSerial.hide()
    self.groupLSL.hide()
    # RESIZE window vertically to fit the content
    self.resize(200, 200)


def connection_protocol_combobox(self):
    """Initializes the connection combobox of PyQt GUI"""
    # on connection combobox change
    if self.comboBox_connection.currentText() == "Serial":
        self.groupSerial.show()
        self.groupLSL.hide()
    elif self.comboBox_connection.currentText() == "LSL":
        self.groupSerial.hide()
        self.groupLSL.show()
    else:
        self.groupSerial.hide()
        self.groupLSL.hide()
    # RESIZE window vertically to fit the content
    width = self.width()
    self.resize(width, 100)


def lsl_lock_in_toggle(self):
    """Locks the LSL configuration in PyQt GUI"""
    self.groupLSL.setEnabled(not self.groupLSL.isEnabled())
    self.pushButton_LSL_lock.setText(
        "Lock-In" if self.groupLSL.isEnabled() else "Change Configuraiton")


def toggle_server(self):
    """Toggles the server on/off"""
    if self.server_process is None:
        start_server(self)
    else:
        stop_server(self)


def start_server(self):
    if self.server_process is None:
        # # Start the FastAPI server as a subprocess
        # # Change directory to the 'src' folder
        # os.chdir("src")
        # # Start the FastAPI server as a subprocess
        # self.server_process = subprocess.Popen(
        #     ["../.venv/bin/python", "-m", "uvicorn", "main:app"],
        # )
        from gui.server_thread import init_server_process
        self.server_process = init_server_process(self)
        self.server_thread.output_received.connect(self.append_output)
        self.server_thread.start()
        self.pushButton_start_backend.setText("Stop Server")

        # set status bar text
        self.statusbar.showMessage(
            "Server started, navigate to http://localhost:8000/docs to view API docs")


def stop_server(self):
    if self.server_process is not None:
        # Terminate the subprocess running the FastAPI server
        self.server_process.terminate()
        self.server_process = None
        self.pushButton_start_backend.setText("Start Server")
        # set status bar text
        self.statusbar.showMessage("Server stopped")
