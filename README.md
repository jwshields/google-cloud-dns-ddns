# google-cloud-dns-ddns
###### Simple Python script to update Google Cloud DNS record in an automated fashion from the command line or in a scheduler

This script was created to help automate updating Google Cloud DNS records via the command line or through a scheduler such as cron.

Currently this script is aimed toward updating `A` and `AAAA` records, but I do not see why it wouldn't work with other types, though some edits to the script would be required for other records.

## Python Requirements
### Environment:
~ This script has been tested with Python 3.6 & 3.7, but should be compatible with 2.7, 3.4, 3.5, barring the needed libraries being backported to those releases of Python. ~
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
    - Either argument can be enclosed in quotes or not, but must be separated by a space
    - As of this writing, supported record types are `A` and `AAAA`

- `--credentials`, `-c`
    - This argument can only be used once
    - It expects a quoted path to a json file
    - This JSON file should be the private key for your Service Account of a GCP Project
    - Service Account Dashboard - [Link](https://console.cloud.google.com/iam-admin/serviceaccounts/project)
    - Service Account Documentation - [Link](https://cloud.google.com/compute/docs/access/service-accounts)
    - Required scope for the Service Account - "Cloud DNS Read/Write" - [Link](https://cloud.google.com/dns/api/authorization)
    - Specific Permissioning - [Link](https://cloud.google.com/dns/access-control#permissions_and_roles)
- `-ttl`
    - This argument can only be specified once
    - It expects a number, unquoted
    - The entered number will be used as the TTL value for all records being processed
    - Defaults to 300 seeconds if this switch is not specified
- `-noipv4`
    - This switch, if present, will tell the script to not perform updates/changes on `A` type records
    - Default - get/update IPv4 records
- `-noipv6`
    - This switch, if present, will tell the script to not perform updates/changes on `AAAA` type records
    - Default - get/update IPv6 records
- `-auto`
    - This switch, if present, will bypass user prompts to proceed/continue
    - Default - False, script *will* prompt to proceed
- `--help`, `-h`
    - This will print the help text for the script, detailing available options/switches

### Examples
1. `python /path/to/script/googleclouddns.py -r "example.com" A -r "example.com" AAAA -r "subdomain.example.com" A -r "subdomain.example.com" AAAA -c "/path/to/my/creds.json" -ttl 60 -auto`
    - This example will create A and AAAA records for `example.com` and `subdomain.example.com` with the machine's external IPv4 and IPv6 addresses, the new records will have a ttl of 60 seconds, and will perform these updates automatically
2. `python /path/to/script/googleclouddns.py -r "mydomain.com" A -c "D:\path\to\my\credentials.json"`
    - This example will create a single A record for `mydomain.com` and will prompt the user to proceed to create/update the records


#### EOF
