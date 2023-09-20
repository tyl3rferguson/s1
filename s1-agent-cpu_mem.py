import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import re

# Directory containing log files
log_dir = "s1_log"

# Initialize empty lists to store data
timestamps = []
cpu_usage = []
cpu_time = []  # List to store CPU time
memory_rss = []
crash_timestamps = []  # List to store crash timestamps
crash_descriptions = []  # List to store crash descriptions

# Function to parse log files
def parse_log_file(file_path):
    with open(file_path, "r") as file:
        for line in file:
            if "Performance telemetry statistics on agent:" in line:
                try:
                    log_data = json.loads(line.split("Performance telemetry statistics on agent:")[1])
                    timestamps.append(log_data["timestamp"])
                    cpu_usage.append(log_data["average_cpu_usage"])
                    cpu_time.append(log_data["cpu_time"])  # Collect CPU time data
                    memory_rss.append(log_data["rss"])
                except json.JSONDecodeError:
                    continue
            elif "Child process agent crashed" in line:
                # Extract crash timestamp and description using regular expressions
                match = re.search(r'\[(.*?)\].*Child process agent crashed with signal (\d+)', line)
                if match:
                    crash_timestamp = match.group(1)
                    crash_signal = match.group(2)
                    crash_timestamps.append(crash_timestamp)
                    crash_descriptions.append(f"Agent crashed with signal {crash_signal}")

# Iterate through log files in the directory
for filename in os.listdir(log_dir):
    if filename.startswith("orchestrator") and filename.endswith(".log"):
        file_path = os.path.join(log_dir, filename)
        print(f"Parsing file: {file_path}")
        parse_log_file(file_path)

# Create Pandas DataFrame from the parsed data
data = {
    "Timestamp": timestamps,
    "CPU Usage": cpu_usage,
    "CPU Time": cpu_time,  # Add CPU time to the data
    "Memory RSS": memory_rss
}
df = pd.DataFrame(data)

# Convert the Timestamp column to a datetime type
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Sort the DataFrame by Timestamp
df = df.sort_values(by="Timestamp")

# Create separate plots for CPU Usage, CPU Time, and Memory with a heatmap for crashes
plt.figure(figsize=(12, 10))

# Create the subplot for CPU Usage
plt.subplot(3, 1, 1)
plt.plot(df["Timestamp"], df["CPU Usage"], label="Average CPU Usage", color='b')
plt.xlabel("Timestamp")
plt.ylabel("Average CPU Usage")
plt.title("CPU Usage Over Time")
plt.legend()

# Create the subplot for CPU Time
plt.subplot(3, 1, 2)
plt.plot(df["Timestamp"], df["CPU Time"], label="CPU Time", color='g')
plt.xlabel("Timestamp")
plt.ylabel("CPU Time")
plt.title("CPU Time Over Time")
plt.legend()

# Create the subplot for Memory with a heatmap for crashes
plt.subplot(3, 1, 3)
plt.plot(df["Timestamp"], df["Memory RSS"], label="Memory RSS", color='r')
plt.scatter(crash_timestamps, [0] * len(crash_timestamps), c='r', marker='x', label='Crashes', zorder=5)
plt.xlabel("Timestamp")
plt.ylabel("Memory RSS")
plt.title("Memory (RSS) Usage Over Time")
plt.ylim(0)  # Set the y-axis lower limit to 0 for Memory RSS
plt.legend()

# Automatically adjust the layout
plt.tight_layout()

# Show the plot
plt.show()

