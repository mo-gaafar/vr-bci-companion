

from qasync import QEventLoop
import asyncio
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


def init_signal_connections(self):
    """Initializes the signal connections of PyQt GUI"""
    # self.worker.connected.connect(
    #     lambda: self.wsConnectionStatus.emit("Connected to WebSocket"))
    # self.worker.disconnected.connect(
    #     lambda: self.wsConnectionStatus.emit("Disconnected from WebSocket"))

    # establishes a connection between the connectionStatus signal (emitted by LSLStreamingThread)
    # and the update_connection_status slot (a method in your ServerControlGUI class)
    self.connectionStatus.connect(self.update_connection_status)
    self.wsConnectionStatus.connect(self.update_connection_status)


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
                     "type": self.comboBox_stream1dt.currentText(),
                     "channels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
                     },
        "stream_2": {"name": self.lineEdit_stream2name.text(),
                     "type": self.comboBox_stream2dt.currentText(),
                     "channels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']},
        # "stream_3": {"name": self.lineEdit_stream3name.text(),
        #              "type": self.comboBox_stream3dt.currentText()},
    }
    return lsl_config


def get_websocket_config(self):
    """Gets the websocket configuration from PyQt GUI

    Returns:
        dict: Websocket configuration

    """
    # get websocket configuration
    # convert to lowercase
    ws_config = {
        "server_select": str(self.comboBox_server_select.currentText()).lower(),
    }
    return ws_config


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
    """Initializes the LSL thread and starts the streaming task."""
    if self.lsl_thread is None:
        from gui.obci_lsl import lsl_stream_to_websocket

        stream_config = get_LSL_config(self)
        server_type = get_websocket_config(self)["server_select"]

        # # Get the Qt event loop
        # loop = QEventLoop(self)
        # asyncio.set_event_loop(loop)  # Set it as the default asyncio loop

        loop = asyncio.get_event_loop()

        async def run_lsl_stream():
            await lsl_stream_to_websocket(self, stream_config, server_type)

        # Schedule the coroutine to run within the Qt event loop
        self.lsl_thread = loop.create_task(run_lsl_stream())

        self.pushButton_LSL_lock.hide()
        self.connectButton.show()
        self.pushButton_show_plot.show()


def stop_lsl_connection(self):
    """Stops the LSL thread and cancels the streaming task."""
    if self.lsl_thread is not None:
        self.lsl_thread.cancel()  # Cancel the asyncio task
        try:
            asyncio.get_event_loop().run_until_complete(
                self.lsl_thread)  # Wait for the task to finish gracefully
        except asyncio.CancelledError:
            pass  # Task cancellation is expected
