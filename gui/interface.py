

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from gui.server_thread import open_server_log_popup
from gui.sig_plot import open_plot_popup
""" interface.py - Interface functions for NeuroRehab Connect"""


def init_connectors(self):
    """Initializes the connectors of PyQt GUI"""
    self.comboBox_connection.currentIndexChanged.connect(
        lambda: connection_protocol_combobox(self))

    self.tabWidget.currentChanged.connect(lambda: change_tabs(self))

    self.pushButton_LSL_lock.clicked.connect(
        lambda: lsl_lock_in_toggle(self))

    self.pushButton_start_backend.clicked.connect(lambda: toggle_server(self))
    self.pushButton_backend_logs.clicked.connect(
        lambda: open_server_log_popup(self))

    self.connectButton.clicked.connect(lambda: init_bci_connection(
        self, self.comboBox_connection.currentText()))

    self.pushButton_show_plot.clicked.connect(lambda: open_plot_popup(self))

    # signal connections
    self.plot_thread.create_plot_popup.connect(self.create_plot_popup)
    self.plot_thread.update_plot_popup.connect(self.update_plot_popup)


def init_bci_connection(self, connection):
    """Initializes the connection of PyQt GUI"""
    if connection == "Serial":
        pass
    elif connection == "LSL":
        init_lsl_thread(self)
    else:
        pass


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
        # "stream_3": {"name": self.lineEdit_stream3name.text(),
        #              "type": self.comboBox_stream3dt.currentText()},
    }
    return lsl_config


def init_stream_plot(self):
    # if show plot button is clicked
    # check if plot thread is initialized
    if self.plot_thread is None:
        # initialize the plot thread
        from gui.sig_plot import PlotThread
        self.plot_thread = PlotThread(self)
        self.plot_thread.start()
    else:
        # stop the plot thread
        self.plot_thread.stop()
        self.plot_thread.wait()
        self.plot_thread = None


def init_layout(self):
    """Initializes the layout of PyQt GUI"""
    self.plotLayout = QVBoxLayout()
    self.mainPlotWidget.setLayout(self.plotLayout)
    # hide groupSerial and groupLSL
    self.groupSerial.hide()
    self.groupLSL.hide()
    # hide connect button and signal plot button by default
    self.connectButton.hide()
    self.pushButton_show_plot.hide()
    # RESIZE window vertically to fit the content
    # self.resize(300, 600)


def change_tabs(self):
    """Initializes the tabs of PyQt GUI"""
    if self.tabWidget.currentIndex() == 0:
        self.resize(300, 100)
    elif self.tabWidget.currentIndex() == 1:
        connection_protocol_combobox(self)
        # self.resize(300, 600)


def connection_protocol_combobox(self):
    """Initializes the connection combobox of PyQt GUI"""
    width = self.width()
    # on connection combobox change
    if self.comboBox_connection.currentText() == "Serial":
        self.groupSerial.show()
        self.groupLSL.hide()
        self.resize(width, 500)
    elif self.comboBox_connection.currentText() == "LSL":
        self.groupSerial.hide()
        self.pushButton_LSL_lock.show()
        self.groupLSL.show()
        self.resize(width, 600)
    else:
        self.pushButton_LSL_lock.hide()
        self.groupSerial.hide()
        self.groupLSL.hide()
        self.resize(width, 380)
    # RESIZE window vertically to fit the content


def lsl_lock_in_toggle(self):
    """Locks the LSL configuration in PyQt GUI"""
    self.groupLSL.setEnabled(not self.groupLSL.isEnabled())
    self.pushButton_LSL_lock.setText(
        "Lock-In" if self.groupLSL.isEnabled() else "Change Configuration")

    # toggles hide the connect to bci button and signal plot button
    if self.groupLSL.isEnabled():
        self.connectButton.hide()
        self.pushButton_show_plot.hide()
    else:
        self.connectButton.show()
        self.pushButton_show_plot.show()


def lsl_toggle(self):
    """Toggles the LSL connection on/off"""
    if self.lsl_thread is None:
        init_lsl_thread(self)
    else:
        from gui.obci_lsl import stop_lsl_connection
        stop_lsl_connection(self)


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


def init_lsl_thread(self):
    """Initializes the LSL thread"""
    from gui.obci_lsl import start_lsl_connection
    lsl_config = get_LSL_config(self)
    start_lsl_connection(self, lsl_config)
