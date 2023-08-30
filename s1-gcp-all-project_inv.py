import subprocess
import requests

def get_all_gcp_projects():
    cmd = ["gcloud", "projects", "list", "--format=value(projectId)"]
    try:
        projects = subprocess.check_output(cmd, text=True).strip().split("\n")
        return projects
    except subprocess.CalledProcessError as e:
        print("Error fetching GCP project list:", e)
        return []

def get_gcp_vm_info(project_id):
    cmd = f"gcloud compute instances list --project {project_id} --format='csv[no-heading](zone.basename(),name)'"
    vm_info = subprocess.check_output(cmd, shell=True, text=True)

    vm_count = 0
    vm_list = []

    for line in vm_info.strip().split("\n"):
        values = line.split(",")
        if len(values) >= 2:
            zone, name = values
            vm_list.append((zone, name))
            vm_count += 1

    return vm_count, vm_list

def get_sentinelone_vm_count(api_token, account_id, s1_api_url, zone):
    api_url = f"{s1_api_url}/web/api/v2.1/agents?accountIds={account_id}"
    headers = {
        "Authorization": f"ApiToken {api_token}"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        agents = response.json()["data"]
        sentinelone_count = sum(1 for agent in agents if agent.get("cloudProviders", {}).get("GCP", {}).get("cloudLocation") == zone)
        return sentinelone_count
    else:
        print(f"SentinelOne API request for zone {zone} failed with status code:", response.status_code)
        return 0

if __name__ == "__main__":
    print("Fetching GCP project list...")
    project_ids = get_all_gcp_projects()

    api_token = input("Enter your SentinelOne API Token: ")
    account_id = input("Enter your SentinelOne Account ID: ")
    s1_api_url = input("Enter your SentinelOne API URL (without the scheme, e.g., usea1-purple.sentinelone.net): ")

    if not s1_api_url.startswith("http://") and not s1_api_url.startswith("https://"):
        s1_api_url = "https://" + s1_api_url

    print("=" * 80)

    for project_id in project_ids:
        print(f"Fetching VMs and SentinelOne counts for project: {project_id}")
        vm_count, vm_list = get_gcp_vm_info(project_id)

        if vm_count == 0:
            print("No VMs found in this project.")
        else:
            print(f"VMs in project {project_id}:")
            print("-" * 80)
            print("{:<30} | {:<20} | {:<20} | {:<10}".format("GCP Region Name", "GCP Linux VM Count", "S1 Linux Agents Count", "Difference"))
            print("-" * 80)
            
            total_gcp_vms = 0
            total_sentinelone_agents = 0
            
            for zone, name in vm_list:
                sentinelone_count = get_sentinelone_vm_count(api_token, account_id, s1_api_url, zone)
                difference = vm_count - sentinelone_count
                total_gcp_vms += vm_count
                total_sentinelone_agents += sentinelone_count
                print("{:<30} | {:<20} | {:<20} | {:<10}".format(zone, vm_count, sentinelone_count, difference))
            
            print("-" * 80)
            print("{:<30} | {:<20} | {:<20} | {:<10}".format("Total", total_gcp_vms, total_sentinelone_agents, total_gcp_vms - total_sentinelone_agents))
            print("=" * 80)
