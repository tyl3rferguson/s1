"""
GCP and S1 Agent Count Comparison

This script retrieves the count of virtual machines (VMs) installed in a specific
Google Cloud Platform (GCP) project. It then queries the SentinelOne API to gather
information about agents matching the environment in a specific SentinelOne account.

Usage:
1. Provide your GCP Project ID, SentinelOne API Token, SentinelOne Account ID, and API URL.
2. The script will retrieve GCP VM and SentinelOne agent information.
3. It will display a comparison table indicating the number of GCP VMs, the number of
   SentinelOne Linux agents, and the difference between the counts.

contact: tylerf@sentinelone.com
"""


import os
import requests
import subprocess

# Fetch GCP VM information using subprocess
def get_gcp_vm_info(project_id):
    subprocess.run(["gcloud", "config", "set", "project", project_id])

    cmd = "gcloud compute instances list --format='csv[no-heading](zone.basename(),name,STATUS)'"
    vm_info = subprocess.check_output(cmd, shell=True, text=True)

    vm_statuses = {}
    vm_names = {}
    total_vms = 0

    for line in vm_info.strip().split("\n"):
        zone, name, status = line.split(",")
        vm_statuses[zone] = vm_statuses.get(zone, {})
        vm_statuses[zone][name] = status
        vm_names[zone] = vm_names.get(zone, "") + "\n" + name
        total_vms += 1

    return vm_statuses, vm_names, total_vms

# Fetch SentinelOne VM information using API
def get_sentinelone_vm_info(api_token, account_id, s1_api_url):
    api_url = f"{s1_api_url}/web/api/v2.1/agents?accountIds={account_id}"
    headers = {
        "Authorization": f"ApiToken {api_token}"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        agents = response.json()["data"]

        sentinelone_info = {}
        for agent in agents:
            cloudProviders = agent.get("cloudProviders")
            if cloudProviders and "GCP" in cloudProviders:
                machine_name = agent.get("computerName")
                sentinelone_info[machine_name] = {
                    "OS": agent.get("osType"),
                    "Location": agent.get("cloudProviders")["GCP"].get("cloudLocation", "Unknown")
                }

        return sentinelone_info

    else:
        print("SentinelOne API request failed with status code:", response.status_code)
        return {}

# Compare GCP VM counts with SentinelOne agent counts
def compare_vm_counts(gcp_vms, sentinelone_vms):
    comparison_table = []
    total_gcp_vms = 0
    total_sentinelone_agents = 0

    for zone, vm_names in gcp_vms.items():
        gcp_count = len(vm_names)
        sentinelone_count = sum(1 for agent in sentinelone_vms.values() if agent["Location"].startswith(zone))
        comparison_table.append((zone, gcp_count, sentinelone_count, gcp_count - sentinelone_count))
        total_gcp_vms += gcp_count
        total_sentinelone_agents += sentinelone_count

    comparison_table.append(("Total", total_gcp_vms, total_sentinelone_agents, total_gcp_vms - total_sentinelone_agents))

    return comparison_table

if __name__ == "__main__":
    gcp_project_id = input("Enter your GCP Project ID: ")
    api_token = input("Enter your SentinelOne API Token: ")
    account_id = input("Enter your SentinelOne Account ID: ")
    s1_api_url = input("Enter your SentinelOne API URL (without the scheme, e.g., usea1-purple.sentinelone.net): ")

    if not s1_api_url.startswith("http://") and not s1_api_url.startswith("https://"):
        s1_api_url = "https://" + s1_api_url

    gcp_vm_statuses, gcp_vm_names, total_gcp_vms = get_gcp_vm_info(gcp_project_id)
    sentinelone_vm_info = get_sentinelone_vm_info(api_token, account_id, s1_api_url)

    comparison_table = compare_vm_counts(gcp_vm_statuses, sentinelone_vm_info)

    print("Comparison Table:")
    print("------------------")
    print("{:<30} | {:<12} | {:<21} | {:<10}".format("GCP Region Name", "GCP VM Count", "S1 Agents Count (on GCP)", "Difference"))
    print("-" * 75)
    for row in comparison_table:
        print("{:<30} | {:<12} | {:<21} | {:<10}".format(*row))

