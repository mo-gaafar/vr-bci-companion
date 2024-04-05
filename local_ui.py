
import datetime
import logging
import sys
from gui import interface


from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSlot


from gui.server_thread import init_server_process
from gui.sig_plot import PlotThread

"""local_ui.py - Main GUI for NeuroRehab Connect"""


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
        self.lsl_thread = None  # Initialize bci lsl thread
        self.plot_thread = PlotThread(self)
        self.plot_popup = None

        # initialize ui connectors
        interface.init_connectors(self)
        interface.init_layout(self)

    @pyqtSlot(str)
    def append_output(self, text):
        if self.server_log_popup is not None:
            self.server_log_popup.update_log(text)
        # self.text_edit.append(text)

    @pyqtSlot(str)
    def update_connection_status(self, status):
        self.label_connection_status.setText(status)

    @pyqtSlot(str, float, list)
    def handle_lsl_data(self, stream_id, timestamp, sample):
        # print(f"Received data for stream: {stream_id}")
        if self.plot_thread is None:
            self.plot_thread = PlotThread(self)
            self.plot_thread.start()
            print("Plot thread started")

        self.plot_thread.add_data(stream_id, timestamp, sample)

    @pyqtSlot()
    def create_plot_popup(self):
        from gui.sig_plot import create_stream_plot
        print("Creating plot popup")
        # print(f"Stream plots: {self.stream_plots}")
        # # get config from ui
        # # self.stream_plots = interface.get_LSL_config(self)
        # # use stream_config to create all plots
        print("Stream plots:")
        print(self.plot_thread.stream_plots)
        for stream_id in self.plot_thread.stream_plots:
            print(f"Creating plot for stream: {stream_id}")
            create_stream_plot(self, stream_id)

    @pyqtSlot(str, int, float, list)
    def update_plot_popup(self, stream_id, channel, timestamp, data):
        # Check if the plot for the given stream_id exists
        if stream_id in self.plot_thread.stream_plots:
            # Access the plot and its data buffers
            plot_info = self.plot_thread.stream_plots[stream_id]
            if channel < len(plot_info['items']):
                # Update the data buffer for the specific channel
                plot_info['buffer'][channel].append(data)
                plot_info['timestamps'][channel].append(timestamp)

                # If your data structure supports trimming old data, do it here
                # to avoid unlimited growth of the data buffer
                print(f"Data length: {len(plot_info['buffer'][channel])}")
                # Update the plot data
                plot_info['items'][channel].setData(
                    plot_info['timestamps'][channel], plot_info['buffer'][channel])
            else:
                print(
                    f"Channel {channel} does not exist in stream {stream_id}.")
        else:
            print(f"Plot for stream {stream_id} does not exist.")


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
