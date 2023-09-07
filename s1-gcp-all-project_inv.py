import subprocess
import requests
import csv

def is_compute_engine_api_enabled(project_id):
    # Check if the Compute Engine API is enabled for the project
    cmd = f"gcloud services list --project {project_id} --format='value(NAME)'"
    try:
        services = subprocess.check_output(cmd, shell=True, text=True).strip().split("\n")
        return "compute.googleapis.com" in services
    except subprocess.CalledProcessError:
        return False

def get_all_gcp_projects():
    try:
        projects = subprocess.check_output(["gcloud", "projects", "list", "--format=value(projectId)"], text=True).strip().split("\n")
        return projects
    except subprocess.CalledProcessError as e:
        print("Error fetching GCP project list:", e)
        return []

def get_gcp_vm_info(project_id):
    cmd = f"gcloud compute instances list --project {project_id} --format='csv[no-heading](zone.basename(),name, status)'"
    vm_info = subprocess.check_output(cmd, shell=True, text=True)

    vm_list = []

    for line in vm_info.strip().split("\n"):
        values = line.split(",")
        if len(values) >= 3:
            zone, name, status = values
            vm_list.append((zone, name, status))

    return vm_list

def get_sentinelone_vm_info(api_token, account_id, s1_api_url, zone):
    api_url = f"{s1_api_url}/web/api/v2.1/agents?accountIds={account_id}"
    headers = {
        "Authorization": f"ApiToken {api_token}"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        agents = response.json()["data"]
        sentinelone_info = []

        for agent in agents:
            cloud_location = agent.get("cloudProviders", {}).get("GCP", {}).get("cloudLocation")
            if cloud_location == zone:
                sentinelone_info.append(agent)

        return sentinelone_info
    else:
        print(f"SentinelOne API request for zone {zone} failed with status code:", response.status_code)
        return []

def calculate_coverage(gcp_vm_count, sentinelone_count):
    if gcp_vm_count == 0:
        return 0
    return (sentinelone_count / gcp_vm_count) * 100

if __name__ == "__main__":
    print("Fetching GCP project list...")
    project_ids = get_all_gcp_projects()

    api_token = input("Enter your SentinelOne API Token: ")
    account_id = input("Enter your SentinelOne Account ID: ")
    s1_api_url = input("Enter your SentinelOne API URL (without the scheme, e.g., usea1-purple.sentinelone.net): ")

    if not s1_api_url.startswith("http://") and not s1_api_url.startswith("https://"):
        s1_api_url = "https://" + s1_api_url

    output_file_name = input("Enter the CSV file name (e.g., output.csv): ")

    data_for_csv = []

    print("=" * 100)
    print("{:<30} | {:<20} | {:<20} | {:<20} | {:<20}".format(
        "GCP Region Name", "GCP Linux VM Count", "S1 Linux Agents Count", "Difference", "Coverage Percentage"))
    print("-" * 100)

    for project_id in project_ids:
        if not is_compute_engine_api_enabled(project_id):
            print(f"Compute Engine API not enabled for the project: {project_id}")
            continue  # Skip this project

        vm_list = get_gcp_vm_info(project_id)

        if vm_list:
            for zone, name, status in vm_list:
                sentinelone_info = get_sentinelone_vm_info(api_token, account_id, s1_api_url, zone)
                sentinelone_count = len(sentinelone_info)

                if sentinelone_count == 0:
                    data_for_csv.append({
                        "GCP Project": project_id,
                        "GCP Region": zone,
                        "Machine Name": name,
                        "Running Status": status,
                    })

                coverage = calculate_coverage(1, sentinelone_count)

                print("{:<30} | {:<20} | {:<20} | {:<20} | {:<20}".format(
                    zone, 1, sentinelone_count, 1 - sentinelone_count, f"{coverage:.2f}%"))

    with open(output_file_name, mode='w', newline='') as csv_file:
        fieldnames = ["GCP Project", "GCP Region", "Machine Name", "Running Status"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for data_row in data_for_csv:
            writer.writerow(data_row)

    print("=" * 100)
    print(f"Data has been saved to {output_file_name}")

