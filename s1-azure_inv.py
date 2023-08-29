import os
import requests
import subprocess

# Fetch Azure VM information using subprocess
def get_azure_vm_info(subscription_id):
    subprocess.run(["az", "account", "set", "--subscription", subscription_id])

    cmd = "az vm list --query '[].{name:name, location:location, powerState:powerState}' --output tsv"
    vm_info = subprocess.check_output(cmd, shell=True, text=True)

    vm_statuses = {}
    vm_names = {}
    total_vms = 0

    for line in vm_info.strip().split("\n"):
        values = line.split("\t")
        if len(values) >= 3:
            name, location, power_state = values
            vm_statuses[location] = vm_statuses.get(location, {})
            vm_statuses[location][name] = power_state
            vm_names[location] = vm_names.get(location, "") + "\n" + name
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
            machine_name = agent.get("computerName")
            sentinelone_info[machine_name] = {
                "OS": agent.get("osType"),
                "Location": agent.get("cloudProviders", {}).get("Azure", {}).get("cloudLocation", "Unknown")
            }

        return sentinelone_info

    else:
        print("SentinelOne API request failed with status code:", response.status_code)
        return {}

# Compare Azure VM counts with SentinelOne agent counts
def compare_vm_counts(azure_vms, sentinelone_vms):
    comparison_table = []
    total_azure_vms = 0
    total_sentinelone_agents = 0

    for location, vm_names in azure_vms.items():
        azure_count = len(vm_names)
        sentinelone_count = sum(1 for agent in sentinelone_vms.values() if agent["Location"].startswith(location))
        comparison_table.append((location, azure_count, sentinelone_count, azure_count - sentinelone_count))
        total_azure_vms += azure_count
        total_sentinelone_agents += sentinelone_count

    comparison_table.append(("Total", total_azure_vms, total_sentinelone_agents, total_azure_vms - total_sentinelone_agents))

    return comparison_table

if __name__ == "__main__":
    print("This script will get the count of VMs installed in Azure for a specific subscription and then query the SentinelOne API for agents matching that environment in a specific SentinelOne account.")
    print("=" * 80)

    azure_subscription_id = input("Enter your Azure Subscription ID: ")
    api_token = input("Enter your SentinelOne API Token: ")
    account_id = input("Enter your SentinelOne Account ID: ")
    s1_api_url = input("Enter your SentinelOne API URL (without the scheme, e.g., usea1-purple.sentinelone.net): ")

    if not s1_api_url.startswith("http://") and not s1_api_url.startswith("https://"):
        s1_api_url = "https://" + s1_api_url

    azure_vm_statuses, azure_vm_names, total_azure_vms = get_azure_vm_info(azure_subscription_id)
    sentinelone_vm_info = get_sentinelone_vm_info(api_token, account_id, s1_api_url)

    if total_azure_vms == 0:
        print("Heads up.. there aren't any VMs in the subscription.")
        exit(0)

    comparison_table = compare_vm_counts(azure_vm_statuses, sentinelone_vm_info)

    print("Comparison Table:")
    print("-" * 80)
    print("{:<30} | {:<12} | {:<21} | {:<10}".format("Azure Location", "Azure VM Count", "S1 Linux Agents Count", "Difference"))
    print("-" * 80)
    for row in comparison_table:
        print("{:<30} | {:<12} | {:<21} | {:<10}".format(*row))

