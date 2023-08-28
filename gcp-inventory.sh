#!/bin/bash
#
# GCP Machine Inventory -tylerf@sentinelone.com
#

# Check if a project value is provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 PROJECT_ID"
    exit 1
fi

# Set the provided project ID
gcloud config set project "$1"

echo "Region Name and VM Count"
gcloud compute instances list --format="csv[no-heading](zone.basename(),name)" | awk -F"," '
{
    zn = $1
    name = $2
    for (i = 1; i <= NF - 1; i++) {
        zn = zn $i
        if (i < NF - 1) {
            zn = zn "-"
        }
    }
    zns[zn] += 1
    names[zn] = names[zn] "\n" name
}
END {
    for (key in zns) {
        print key ": " zns[key] names[key]
    }
}
' | sort | awk 'BEGIN {print "Region Name, VM Count, and VM Names"} {print $0; vt += $2} END {print "Total VMs: " vt}'

echo ""

echo "Region Name, VM Count, and VM Names (Running)"
gcloud compute instances list --filter="status=RUNNING" --format="csv[no-heading](zone.basename(),name)" | awk -F"," '
{
    zn = $1
    name = $2
    for (i = 1; i <= NF - 1; i++) {
        zn = zn $i
        if (i < NF - 1) {
            zn = zn "-"
        }
    }
    zns[zn] += 1
    names[zn] = names[zn] "\n" name
}
END {
    for (key in zns) {
        print key ": " zns[key] names[key]
    }
}
' | sort | awk 'BEGIN {print "Region Name, VM Count, and VM Names"} {print $0; vt += $2} END {print "Total Running VMs: " vt}'
