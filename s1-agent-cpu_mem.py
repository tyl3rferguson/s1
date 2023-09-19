import os
import json
import matplotlib.pyplot as plt
import pandas as pd

# Directory containing log files
log_dir = "s1_log"

# Initialize empty lists to store data
timestamps = []
cpu_usage = []
memory_rss = []

# Function to parse log files
def parse_log_file(file_path):
    with open(file_path, "r") as file:
        for line in file:
            if "Performance telemetry statistics on agent:" in line:
                try:
                    log_data = json.loads(line.split("Performance telemetry statistics on agent:")[1])
                    timestamps.append(log_data["timestamp"])
                    cpu_usage.append(log_data["average_cpu_usage"])
                    memory_rss.append(log_data["rss"])
                except json.JSONDecodeError:
                    continue

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
    "Memory RSS": memory_rss
}
df = pd.DataFrame(data)

# Convert the Timestamp column to a datetime type
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Sort the DataFrame by Timestamp
df = df.sort_values(by="Timestamp")

# Create separate plots for CPU and Memory
plt.figure(figsize=(12, 6))

# Plot CPU Usage
plt.subplot(2, 1, 1)
plt.plot(df["Timestamp"], df["CPU Usage"], label="Average CPU Usage")
plt.xlabel("Timestamp")
plt.ylabel("Average CPU Usage")
plt.title("CPU Usage Over Time")
plt.legend()

# Plot Memory (RSS) Usage
plt.subplot(2, 1, 2)
plt.plot(df["Timestamp"], df["Memory RSS"], label="Memory RSS")
plt.xlabel("Timestamp")
plt.ylabel("Memory RSS")
plt.title("Memory (RSS) Usage Over Time")
plt.legend()

# Automatically adjust the layout
plt.tight_layout()

# Show the plots
plt.show()

