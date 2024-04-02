import time
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout

import random

from PyQt5 import QtCore, QtWidgets

""" sig_plot.py - Signal plotting functions for NeuroRehab Connect"""


class PlotThread(QtCore.QThread):
    create_plot_popup = QtCore.pyqtSignal(str)  # Signal for popup creation
    update_plot_popup = QtCore.pyqtSignal(
        str, int, float, list)  # Signal for updating plot

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_queue = []  # Queue to store data received from LSL thread
        self.stream_plots = {}  # Store plot widgets for each stream

    def run(self):
        while True:
            if self.data_queue:  # Process data when available
                stream_id, timestamp, sample = self.data_queue.pop(0)
                # Check if stream plot exists
                if stream_id not in self.stream_plots:
                    print(f"Stream plot for {stream_id} does not exist.")
                    self.create_stream_plot(stream_id)

                self.update_stream_plot(stream_id, timestamp, sample)
            else:
                time.sleep(0.01)  # Small delay to not overload CPU

    def add_data(self, stream_id, timestamp, sample):
        self.data_queue.append((stream_id, timestamp, sample))

    def create_stream_plot(self, stream_id):
        """Creates a plot in a popup window."""
        # initialize stream plot dictionary
        self.stream_plots[stream_id] = {
            # To store plot items for each channel
            'items': [[] for _ in range(8)],
            # Separate buffer for each channel
            'buffer': [[] for _ in range(8)],
            # Separate timestamps for each channel
            'timestamps': [[] for _ in range(8)]
        }
        # signal to create plot popup in main thread
        self.create_plot_popup.emit(stream_id)

    def update_stream_plot(self, stream_id, timestamp, sample):

        # get the plot dictionary for this stream from parent
        # plotDict = self.parent().stream_plots[stream_id]
        print(self.stream_plots)
        # plotDict = self.stream_plots[stream_id]
        # print("plot dict" + str(plotDict))

        # Assume each lsl frame is 8 channels and update each channel by one sample at a time then send
        for i, data in enumerate(sample):

            # Update the plot item with the new data
            # window width is 10 seconds
            if len(self.stream_plots[stream_id]['buffer'][i]) > 1000:
                self.stream_plots[stream_id]['buffer'][i] = self.stream_plots[stream_id]['buffer'][i][1:]
                self.stream_plots[stream_id]['timestamps'][i] = self.stream_plots[stream_id]['timestamps'][i][1:]
            else:
                # Update the data buffer for the specific channel
                self.stream_plots[stream_id]['buffer'][i].append(data)
                self.stream_plots[stream_id]['timestamps'][i].append(timestamp)
            # emit signal to update plot popup in main thread with the new buffer
            # every 1 second send signal to update plot
            if len(self.stream_plots[stream_id]['buffer'][i]) % 100 == 0:
                print("updating plot")
                print(self.stream_plots[stream_id]['buffer'][i])
                data_out = self.stream_plots[stream_id]['buffer'][i]
                self.update_plot_popup.emit(stream_id, i, timestamp, data_out)

# def create_stream_plot(self, stream_id):
#     # Create a new plot for this stream
#     plotWidget = pg.PlotWidget(title=f"Stream: {stream_id}")
#     self.plotLayout.addWidget(plotWidget)


def create_stream_plot(self, stream_id):
    """Creates a plot in a popup window."""
    self.plot_popup = QtWidgets.QDialog(self.parent())
    self.popup_layout = QVBoxLayout(self.plot_popup)
    plotWidget = pg.PlotWidget(title=f"Stream: {stream_id}")
    self.popup_layout.addWidget(plotWidget)

    # Store the plot widget and an empty list for plot items
    self.plot_thread.stream_plots[stream_id] = {
        'widget': plotWidget,  # Your plot widget initialization
        'items': [],  # To store plot items for each channel
        # Separate buffer for each channel
        'buffer': [[] for _ in range(8)],
        # Separate timestamps for each channel
        'timestamps': [[] for _ in range(8)]
    }

    # Create plot items for each channel upfront
    for channel_index in range(8):
        # random rgb color for each channel
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))

        plotItem = self.plot_thread.stream_plots[stream_id]['widget'].plot(
            pen=pg.mkPen(color=color,
                         width=2))
        self.plot_thread.stream_plots[stream_id]['items'].append(plotItem)
    self.plot_popup.show()


def open_plot_popup(self):
    """Opens the plot popup window."""
    if self.plot_popup is not None:
        close_plot_popup(self)
    else:
        self.plot_popup = QtWidgets.QDialog(self)
        self.popup_layout = QVBoxLayout(self.plot_popup)
        plotWidget = pg.PlotWidget(title="Stream Plot")
        self.popup_layout.addWidget(plotWidget)
        # start plot thread
        self.plot_thread.start()
        print("connecting create_plot_popup")
        self.plot_popup.show()


def close_plot_popup(self):
    """Closes the plot popup window."""
    self.plot_popup.close()
    self.plot_popup = None
    self.popup_layout = None
    self.stream_plots = {}
