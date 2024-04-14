import random
import time
import pylsl

# --- Configuration ---
stream_name = 'obci_eeg1'
stream_type = 'EEG'  # Adjust if needed
channel_count = 8
nominal_srate = 5  # Samples per second
data_type = 'float32'  # Common for EEG

# --- Create an outlet ---
info = pylsl.StreamInfo(stream_name, stream_type,
                        channel_count, nominal_srate, data_type, 'myuid12345')
outlet = pylsl.StreamOutlet(info)

# --- Generate a continuous stream of random data ---
print("Sending test data...")
start_time = time.time()
while True:
    # Create a sample with random values
    sample = [random.random() for _ in range(channel_count)]

    # Push the sample to the outlet
    outlet.push_sample(sample, time.time())

    print(sample)
    print(time.time())
    # Control the rate (adjust if needed)
    time.sleep(0.1)
