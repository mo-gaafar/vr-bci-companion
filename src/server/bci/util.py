# EEG data to mne raw object

# Path: src/server/machine_learning/preprocessors.py


from .models import CalibrationAction, CalibrationSet, CalibrationProtocol
from .models import CalibrationProtocol
from mne import create_info, concatenate_raws, concatenate_epochs
from server.machine_learning.models import ClassEnum
from server.bci.models import EEGData
from typing import List
import numpy as np


def eeg_data_to_mne_raw(eeg_data: EEGData):
    # Create info object
    ch_names = eeg_data.ch_names
    ch_types = ['eeg'] * len(ch_names)
    info = create_info(ch_names=ch_names,
                       sfreq=eeg_data.sfreq, ch_types=ch_types)

    # Create raw object
    raw = eeg_data.data
    return raw


def calc_protocol_time(calibration_protocol: CalibrationProtocol):
    '''Calculate the total time of a calibration protocol in seconds.'''
    # Calculate time from protocol
    # add up all seconds x repetitions
    time = 0
    for event in calibration_protocol.prepare.actions:
        time_prep = 0
        time_prep += event.baseline
        time_prep += event.time
        time_prep += event.cooldown
        time += time_prep * calibration_protocol.prepare.repeat
    for event in calibration_protocol.main_trial.actions:
        time_trial = 0
        time_trial += event.baseline
        time_trial += event.time
        time_trial += event.cooldown
        time += time_trial * calibration_protocol.main_trial.repeat
    for event in calibration_protocol.end.actions:
        time_end = 0
        time_end += event.baseline
        time_end += event.time
        time_end += event.cooldown
        time += time_end * calibration_protocol.end.repeat
    return time

def generate_mne_event_labels(protocol: CalibrationProtocol, start_epoch):
    '''Generate MNE event labels from a calibration protocol, 
    starting from a given epoch number. and return the event labels and event ids.'''

    # Generate event labels
    event_labels = []
    event_ids = {}
    epoch_num = start_epoch
    for event in protocol.prepare.actions:
        event_labels.append(event.action)
        event_ids[event.action] = epoch_num
        epoch_num += 1
    for event in protocol.main_trial.actions:
        event_labels.append(event.action)
        event_ids[event.action] = epoch_num
        epoch_num += 1
    for event in protocol.end.actions:
        event_labels.append(event.action)
        event_ids[event.action] = epoch_num
        epoch_num += 1

    return event_labels, event_ids

