from PyQt6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import subprocess
import threading
import sys
import numpy as np
from pylsl import StreamInlet, resolve_streams

from bci.openbci_interface import BCIStreamer


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, bci_streamer):
        super().__init__()
        self.setWindowTitle("BCI Control Panel")
        self.bci_streamer = bci_streamer

        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QGridLayout(self.central_widget)

        self._create_connection_area()
        self._create_status_area()
        self._create_eeg_plot()
        self._create_lsl_config_window()

        self.update_connection_type('Serial')  # Initial state
        self.bci_streamer.connection_status.connection_status_changed.connect(
            self.update_connection_status)
        self.port_label = None
        self.port_combobox = None
        self.refresh_ports_button = None

    def _create_connection_area(self):
        connection_area = QtWidgets.QGroupBox("Connection")
        connection_layout = QtWidgets.QFormLayout(connection_area)

        self.connection_method_dropdown = QtWidgets.QComboBox()
        self.connection_method_dropdown.addItems(['Serial', 'PyLSL'])
        connection_layout.addRow("Connection Method:",
                                 self.connection_method_dropdown)

        self.port_label = QtWidgets.QLabel("Port:")
        connection_layout.addRow(self.port_label)
        self.port_combobox = QtWidgets.QComboBox()
        connection_layout.addRow(self.port_combobox)
        self.refresh_ports_button = QtWidgets.QPushButton("Refresh Ports")
        connection_layout.addRow(self.refresh_ports_button)

        self.connect_button = QtWidgets.QPushButton("Connect")
        connection_layout.addRow(self.connect_button)

        self.port_selection_widget = self.port_combobox

        self.connection_method_dropdown.currentTextChanged.connect(
            self.update_connection_type)
        self.refresh_ports_button.clicked.connect(self.update_port_list)
        self.connect_button.clicked.connect(self.toggle_bci_connection)

        # PyLSL Configuration (initially hidden)
        self.lsl_config_groupbox = QtWidgets.QGroupBox(
            "LSL Stream Configuration")
        self.lsl_config_layout = QtWidgets.QFormLayout(
            self.lsl_config_groupbox)
        connection_layout.addWidget(self.lsl_config_groupbox)
        self.lsl_config_groupbox.setVisible(False)  # Initially hidden

        # Add LSL Configuration Elements Here
        self.stream_name_inputs = []
        self.stream_type_dropdowns = []
        self.stream_enable_checkboxes = []

        for i in range(3):
            label = QtWidgets.QLabel(f"Stream {i + 1} Name:")
            self.lsl_config_layout.addRow(label)
            name_input = QtWidgets.QLineEdit(f"obci_eeg{i + 1}")
            self.stream_name_inputs.append(name_input)
            self.lsl_config_layout.addRow(name_input)

            label = QtWidgets.QLabel("Type:")
            self.lsl_config_layout.addRow(label)
            dropdown = QtWidgets.QComboBox()
            dropdown.addItems(['EEG', 'Markers', 'None'])
            self.stream_type_dropdowns.append(dropdown)
            self.lsl_config_layout.addRow(dropdown)

            checkbox = QtWidgets.QCheckBox("Enable")
            checkbox.setChecked(True)
            self.stream_enable_checkboxes.append(checkbox)
            self.lsl_config_layout.addRow(checkbox)

        # Adjust row/col as needed
        self.main_layout.addWidget(connection_area, 0, 0)

    def _create_status_area(self):
        # ... Similar Structure for status display ...
        pass

    def _create_eeg_plot(self):
        # ... EEG Plot setup ...
        pass

    def _create_lsl_config_window(self):
        self.stream_config_widget = QtWidgets.QDialog()  # Use QDialog
        self.stream_config_widget.setWindowTitle(
            "LSL Stream Configuration")
        self.stream_config_layout = QtWidgets.QFormLayout(
            self.stream_config_widget)

        self.stream_name_inputs = []
        self.stream_type_dropdowns = []
        self.stream_enable_checkboxes = []

        for i in range(3):
            label = QtWidgets.QLabel(f"Stream {i + 1} Name:")
            self.stream_config_layout.addRow(label)
            name_input = QtWidgets.QLineEdit(f"obci_eeg{i + 1}")
            self.stream_name_inputs.append(name_input)
            self.stream_config_layout.addRow(name_input)

            label = QtWidgets.QLabel("Type:")
            self.stream_config_layout.addRow(label)
            dropdown = QtWidgets.QComboBox()
            dropdown.addItems(['EEG', 'Markers', 'None'])
            self.stream_type_dropdowns.append(dropdown)
            self.stream_config_layout.addRow(dropdown)

            checkbox = QtWidgets.QCheckBox("Enable")
            checkbox.setChecked(True)
            self.stream_enable_checkboxes.append(checkbox)
            self.stream_config_layout.addRow(checkbox)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.configure_lsl_streams)
        self.stream_config_layout.addWidget(ok_button)

        self.stream_config_widget.show()

    def configure_lsl_streams(self):
        inlets = []
        for i in range(3):
            stream_name = self.stream_name_inputs[i].text().strip()
            stream_type = self.stream_type_dropdowns[i].currentText()
            is_enabled = self.stream_enable_checkboxes[i].isChecked()

            if is_enabled:
                matching_streams = [stream for stream in resolve_streams(
                ) if stream.name() == stream_name and stream.type() == stream_type]
                if matching_streams:
                    inlet = StreamInlet(matching_streams[0])
                    inlets.append(inlet)
                else:
                    print(
                        f"Warning: Could not find LSL stream '{stream_name}' (type: {stream_type})")

        if inlets:
            self.inlets = inlets  # Store for later
            self.bci_streamer.start_streaming(self.process_data)
        else:
            self.show_error_message("No valid LSL streams configured.")

        self.stream_config_widget.close()

    def toggle_bci_connection(self):
        if self.bci_streamer.is_connected:
            self.bci_streamer.stop_streaming()
            self.connect_button.setText("Connect BCI")
            self.inlets = []  # Clear inlets on disconnect
        else:
            if self.bci_streamer.connection_type == 'PyLSL':
                if not self.stream_config_widget:
                    self.create_lsl_stream_config_window()
                    return  # Wait for user to configure LSL streams

                self.inlets = self.configure_lsl_streams()
                if not self.inlets:
                    self.show_error_message(
                        "Error: Could not find configured LSL streams.")
                    return

                self.bci_streamer.start_streaming(self.process_data)
            else:
                # Handle serial connection logic (if applicable)
                pass
            self.connect_button.setText("Disconnect BCI")

    def toggle_bci_connection(self):
        if self.bci_streamer.is_connected:
            self.bci_streamer.stop_streaming()
            self.connect_button.setText("Connect BCI")
        else:
            self.bci_streamer.port = self.port_combobox.currentText()
            self.bci_streamer.start_streaming(self.process_data)
            self.connect_button.setText("Disconnect BCI")

    def update_status_label(self, status):
        self.status_label.setText(f"Status: {status}")

    def update_signal_quality(self, quality):
        self.signal_quality_label.setText(f"Signal Quality: {quality}")

    def start_fastapi_server(self):
        self.server_thread = threading.Thread(target=self.run_fastapi)
        self.server_thread.start()
        self.start_server_button.setEnabled(False)

    def run_fastapi(self):
        subprocess.run(["uvicorn", "main:app", "--reload"])
        self.start_server_button.setEnabled(True)

    def process_data(self, data_packet):
        self.data_buffer.append(data_packet.channels_data)
        self.update_eeg_plot()
        # ... other data processing ...

    def update_eeg_plot(self):
        data_array = np.array(self.data_buffer)
        for i, curve in enumerate(self.eeg_curves):
            curve.setData(data_array[:, i])

    def show_error_message(self, message):
        error_dialog = QtWidgets.QMessageBox()
        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.setText(message)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec()

    def update_port_list(self):
        # get port endpoints available from os
        import serial.tools.list_ports

        def get_available_serial_ports():
            ports = serial.tools.list_ports.comports()
            available_ports = []
            for port, desc, hwid in sorted(ports):
                available_ports.append(port)
            return available_ports

        ports = get_available_serial_ports()
        print("Available serial ports:", ports)

        # Update the combobox #but try to maintain the current selection if its still available
        current_port = self.port_combobox.currentText()
        self.port_combobox.clear()

        if current_port in ports:
            self.port_combobox.addItem(current_port)
            ports.remove(current_port)

        self.port_combobox.addItems(ports)
        if not self.port_combobox.currentText():
            self.port_combobox.addItem("No ports available")
            self.port_combobox.setDisabled(True)
        else:
            self.port_combobox.setDisabled(False)

        return ports

    def update_connection_type(self, connection_type):
        self.bci_streamer.connection_type = connection_type
        self.port_selection_widget.setEnabled(connection_type == 'Serial')
        self.port_label.setVisible(connection_type == 'Serial')
        self.refresh_ports_button.setVisible(connection_type == 'Serial')

        if connection_type == 'PyLSL':
            if not self.stream_config_widget:
                self.create_lsl_stream_config_window()
                self.stream_config_widget.show()  # Show after creation

    def start_streaming(self):
        self.bci_streamer.connect()
        self.bci_streamer.start_streaming(self.process_data)
        self.connect_button.setText("Disconnect")

    def update_connection_status(self, status_message):
        self.status_label.setText(status_message)
        self.connect_button.setEnabled(
            status_message != "Connected (LSL)" and status_message != "Connected (Serial)")

    def create_lsl_stream_config_window(self):
        self.stream_config_widget = QtWidgets.QWidget()
        self.stream_config_layout = QtWidgets.QFormLayout(
            self.stream_config_widget)

        # Dynamically generate input fields based on available LSL streams
        self.stream_name_inputs = []
        self.stream_type_dropdowns = []

    def process_data(self, data, stream_index):
        # ... Process data and update UI elements ...
        pass


# Example usage
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    streamer = BCIStreamer()
    window = MainWindow(streamer)
    window.show()
    app.exec()
