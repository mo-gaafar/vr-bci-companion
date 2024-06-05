import time
import csv
import logging


def timed(func):
    """Decorator to measure execution time and log/save results."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Log to console (optional)
        logging.info(f"{func.__name__} took {elapsed_time:.6f} seconds")

        # Save to CSV
        with open("function_timing.csv", "a", newline='') as csvfile:  # Append mode
            fieldnames = ["Function_Name", "Elapsed_Time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:  # Write header only if the file is empty
                writer.writeheader()
            writer.writerow({"Function_Name": func.__name__,
                            "Elapsed_Time": elapsed_time})

        return result
    return wrapper

# Example Usage


@timed
def my_function(a, b):
    """Example function to be timed."""
    # ... your function code ...
    return a + b


# Set up logging
logging.basicConfig(filename='execution_times.log', level=logging.INFO)

# Call the function multiple times to test
for i in range(5):
    my_function(i, i*2)
