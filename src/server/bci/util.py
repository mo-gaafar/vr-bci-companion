# EEG data to mne raw object

# Path: src/server/machine_learning/preprocessors.py


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
