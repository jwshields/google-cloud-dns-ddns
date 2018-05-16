# google-cloud-dns-ddns
###### Simple Python script to update Google Cloud DNS record in an automated fashion from the command line or in a scheduler

This script was created to help automate updating Google Cloud DNS records via the command line or through a scheduler such as cron.

Currently this script is aimed toward updating `A` and `AAAA` records only.

## Python Requirements
### Environment:
- Python 3.6+
### Imports
- google.oauth2
- google.cloud.dns
- os
- requests
- time
- argparse
- collections

### Documentation/Usage
This script accepts multiple arguments
- `--record`, `-r`
    - This arument can be used in any position of the command, and can be used an unlimited number of times
    - It accepts two inputs per argument
    - The first argument should be a FQDN
    - The second should be a record type
    - As of this writing, supported record types are `A` and `AAAA`
    - Either argument can be enclosed in quotes or not, but must be separated by a space
- `--credentials`, `-c`
    - This argument can only be used once
    - It expects a quoted path to a json file
    - This JSON file should be the private key for your Service Account of a Google Cloud Project
    - Service Account Dashboard - [Link](https://console.cloud.google.com/iam-admin/serviceaccounts/project)
    - Service Account Documentation - [Link](https://cloud.google.com/compute/docs/access/service-accounts)
    - Required scope for the Service Account - "Cloud DNS Read/Write" - [Link](https://cloud.google.com/dns/api/authorization)
    - Specific Permissioning - [Link](https://cloud.google.com/dns/access-control#permissions_and_roles)
- `-noipv4`
    - This switch, if present, will tell the script to not perform updates/changes on `A` type records
    - Default - get/update IPv4 records
- `-noipv6`
    - This switch, if present, will tell the script to not perform updates/changes on `AAAA` type records
    - Default - get/update IPv6 records
- `-auto`
    - This switch, if present, will bypass user prompts to proceed/continue
    - Default - False, script *will* prompt user
- `--help`, `-h`
    - This will print the help text for the script, detailing available options/switches

### Examples
1. `python /path/to/script/googleclouddns.py -r "example.com" A -r "example.com" AAAA -r "subdomain.example.com" A -r "subdomain.example.com" AAAA -c "/path/to/my/creds.json" -auto`
    - This example will create A and AAAA records for `example.com` and `subdomain.example.com` with the machine's external IPv4 and IPv6 addresses, and will perform these updates automatically
2. `python /path/to/script/googleclouddns.py -r "mydomain.com" A -c "/path/to/my/credentials.json"`
    - This example will create a single A record for `mydomain.com` and will prompt the user to proceed to create/update the records

#### EOF
