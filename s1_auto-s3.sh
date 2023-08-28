#!/bin/bash
#
# This script is designed to download S1 agents via API from the S1 Console and upload to S3.
# Version: 1.0 tylerf@sentinelone.com
#
# run ./script --help for usage

# Usage help message
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 S1_CONSOLE_PREFIX S1_API_TOKEN S1_RELEASE_STATUS S1_FILE_EXTENSION S1_ARCHITECTURE S3_BUCKET_NAME S3_PATH"
    echo "S1_CONSOLE_PREFIX: The SentinelOne console prefix"
    echo "S1_API_TOKEN: API token for authentication"
    echo "S1_RELEASE_STATUS: Release status (ea and ga supported)"
    echo "S1_FILE_EXTENSION: File type (deb or rpm)"
    echo "S1_ARCHITECTURE: Architecture (x86_64 and aarch64 supported)"
    echo "S3_BUCKET_NAME: S3 bucket name"
    echo "S3_PATH: Path within S3 bucket"
    exit 0
fi

S1_CONSOLE_PREFIX=$1
S1_API_TOKEN=$2
S1_RELEASE_STATUS=$3
S1_FILE_EXTENSION=$4
S1_ARCHITECTURE=$5
S3_BUCKET_NAME=$6
S3_PATH=$7

# Determine OS types based on architecture
if [ "$S1_ARCHITECTURE" = "aarch64" ] || [ "$S1_ARCHITECTURE" = "x86_64" ]; then
    S1_OS_TYPES="linux"
else
    echo "Invalid architecture: $S1_ARCHITECTURE"
    exit 1
fi

# Color codes for messages
Color_Off='\033[0m'
Green='\033[0;32m'
Purple='\033[0;35m'

# Find the latest GA package
printf "${Green}Fetching info on the latest ${S1_RELEASE_STATUS} K8s Agent for ${S1_FILE_EXTENSION} packages...${Color_Off}\n"
response=$(curl -H "Authorization: ApiToken ${S1_API_TOKEN}" \
    -H "Content-Type: application/json" \
    "https://${S1_CONSOLE_PREFIX}.sentinelone.net/web/api/v2.1/update/agent/packages?osTypes=${S1_OS_TYPES}&fileExtension=.${S1_FILE_EXTENSION}&status=${S1_RELEASE_STATUS}&sortOrder=desc")

# Capture details in variables
download_link=$(echo "$response" | jq -r ".data[] | select(.fileName | contains(\"${S1_ARCHITECTURE}\")) | .link" | head -n 1 | sed -e 's/^"//' -e 's/"$//')
filename=$(echo "$response" | jq -r ".data[] | select(.fileName | contains(\"${S1_ARCHITECTURE}\")) | .fileName" | head -n 1)

# Output details to the screen
printf "${Purple}Found the following ${S1_RELEASE_STATUS} Linux ${S1_FILE_EXTENSION} Agent for ${S1_ARCHITECTURE}...\n"
printf "${Purple}Filename:  ${filename}\n"

# Download the package
printf "${Green}Downloading ${filename} package:      ${filename}${Color_Off}\n"
curl -# -H "Authorization: ApiToken ${S1_API_TOKEN}" -o "$filename" "$download_link"

# Upload the package to S3
if [ -n "$S3_BUCKET_NAME" ]; then
    printf "${Green}Uploading ${filename} package to S3...${Color_Off}\n"
    aws s3 cp "$filename" "s3://${S3_BUCKET_NAME}/${S3_PATH}/${filename}"
    printf "${Green}Package uploaded to S3.${Color_Off}\n"
    printf "${Green}Confirmation: ${filename} has been successfully uploaded to S3.${Color_Off}\n"
fi

printf "${Green}Script completed successfully!${Color_Off}\n"

