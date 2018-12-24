import os
import requests
import time
import argparse
import collections
from google.oauth2 import service_account
from google.cloud import dns as gdns


def argparser():
    # argparse to gather command line args
    # also to show help text
    usagestr = ("""googleclouddns.py --credentials "/path/to/service/creds.json" --record "subdomain.example.com" "A"
                --record [FQDN] [record type] -r [FQDN] [record type]\n""")
    parser = argparse.ArgumentParser(prog='googleclouddns', usage=usagestr)
    rhelpstr = ("A required argument that can be listed an unlimited number of times\nThis argument expects, in order,"
                "a FQDN hostname, and a record type.")
    chelpstr = "A required argument which points to the location on disk of the service account credentials.json file"
    ip4helpstr = ('An optional argument which is a boolean option, which chooses whether to update IPv4 DNS (defaults '
                  'to ipv4=True)')
    ip6helpstr = ('An optional argument which is a boolean option, which chooses whether to update IPv6 DNS (defaults '
                  'to ipv6=True)')
    ttlhelpstr = ('An optional argument which allows specifying the TTL of records to be processed. (Defaults to 300 '
                  'seconds)')
    autostr = 'An option that performs updates automatically without prompting.'
    parser.add_argument('--record', '-r', nargs=2, metavar=('"FQDN"', '{record type}'), action="append",
                        help=rhelpstr, required=True)
    parser.add_argument('--credentials', '-c', nargs=1, help=chelpstr, required=True)
    parser.add_argument('-noipv4', action="store_false", help=ip4helpstr, required=False, default=True)
    parser.add_argument('-noipv6', action='store_false', help=ip6helpstr, required=False, default=True)
    parser.add_argument('-auto', action='store_true', help=autostr, required=False, default=False)
    parser.add_argument('-ttl', action='store', help=ttlhelpstr, required=False, default=300, type=int)
    arg_ns_1 = parser.parse_args()
    # sort the records because why not
    arg_ns_1.record = sorted(arg_ns_1.record)
    # Print info about records received
    print("Got {0} records to process:".format(len(arg_ns_1.record)))
    temp_records = []
    for record in arg_ns_1.record:
        if (record[1]).upper() in ["A", "AAAA", "TXT", "MX", "CAA", "CNAME", "NS"]:
            print("""- "{0}" with an "{1}" record""".format(record[0], record[1]))
            temp_records.append(record)
    if arg_ns_1.ttl == 300:
        ttlprintstr = ("\nA TTL value was either not specified or the flag was set to 300, using default value of 300 "
                       "seconds.")
    else:
        ttlprintstr = "\nSpecifying a TTL value of {0} for all records being processed.".format(arg_ns_1.ttl)
    print(ttlprintstr)
    arg_ns_1.record = temp_records
    return arg_ns_1


def auto_proceed(arg_ns_2):
    # check for the `-auto` switch
    # if not auto, prompt to proceed
    proceed = arg_ns_2.auto
    if not proceed:
        print("\nI will be reaching out to two external hosts to retrieve IP information. These hosts are:\n"
              "- `4.icanhazip.com`\n- `6.icanhazip.com`")
        proceed = input("\nDo you want to proceed?\ny/n: ")
        if proceed.lower() != "y":
            print("\nNo changes have been made...\nExiting script")
            time.sleep(0.25)
            exit(0)
        return
    else:
        return


def load_creds():
    # check if creds path is real
    # exit if not
    # load credentials and open up a session with Google Cloud and scoped for DNS.
    # grabs the project-id from the service account json
    jsonpath = os.path.exists(arg_ns.credentials[0])
    if jsonpath:
        gcredentials = service_account.Credentials.from_service_account_file(arg_ns.credentials[0])
        gscoped_credentials = gcredentials.with_scopes(['https://www.googleapis.com/auth/ndev.clouddns.readwrite'])
        return gscoped_credentials
    else:
        print("\nThe location given for the service account credentials json file was not found.")
        exit(1)


def retrieve_addresses(arg_ns_internal):
    # Starting retrieval of external addresses
    print("\nRetrieving external addresses now...")
    if arg_ns_internal.noipv4:
        ipv4ip_internal = (requests.get('http://4.icanhazip.com')).text.strip('\n') or None
        print("Received '{0}' as IPv4 address.".format(ipv4ip_internal))
    else:
        ipv4ip_internal = None
    if arg_ns_internal.noipv6:
        ipv6ip_internal = (requests.get('http://6.icanhazip.com')).text.strip('\n') or None
        print("Received '{0}' as IPv6 address.".format(ipv6ip_internal))
    else:
        ipv6ip_internal = None
    print("")
    return ipv4ip_internal, ipv6ip_internal


def zone_search(values, searchfor):
    for k, v in values.items():
        if v.dns_name in '{0}.'.format(searchfor):
            return k
    return None


def all_zones(gdnsclient_func):
    # start zone enumeration to figure out what we have to work with
    # load up the zones into a dict
    zones = gdnsclient_func.list_zones()
    zone_list1 = {}
    for zone in zones:
        zone_list1[str(zone.name)] = zone
    return zone_list1


def zones_to_edit_func(all_zones_func, records):
    # create an empty dict of lists from the collections package
    zones_to_edit1 = collections.defaultdict(list)
    passed_records_with_no_zone1 = {}
    # iterate through records to match if it's a zone that we have access to via the passed credentials
    for record_inside in records:
        zonekey = zone_search(all_zones_func, record_inside[0])
        if zonekey is not None:
            zones_to_edit1[str(zonekey)].append(record_inside)
        else:
            passed_records_with_no_zone1[str(record_inside[0])] = record_inside
    # Print something if we get records in a zone we don't have
    if passed_records_with_no_zone1:
        print("You have passed in arguments that I was unable to find a zone for.\nThese will be discarded:")
        for k, v in passed_records_with_no_zone1.items():
            print(k)
    return zones_to_edit1, passed_records_with_no_zone1


def check_records(my_zone_int, records, v4ip, v6ip, ttl):
    existing_list = list(my_zone_int.list_resource_record_sets())
    existing_del = {}
    create = {}
    # This is a really hacky and shit method of doing this.
    # In this thing we start iterating over the list of records passed in as args
    # then we append a period to the end of a record if it does not have one;
    #   this is to conform to the way a record needs to be formatted
    # After that, we compare that record, with the list of returned records from the first line of this func
    # Comparing against the record names to see if they are already existing or not.
    # If we find a matching record, we then proceed to check if the existing record's data
    #   is equal to the IP we just retrieved.
    #   if it is, we don't edit the record
    #   otherwise, we do edit it.
    for record in records:
        no_touch = False
        ttl_diff = False
        existing_record = False
        resource_record_set = None
        if not record[0].endswith("."):
            record[0] = "{0}.".format(record[0])
        for recordset in existing_list:
            if recordset.name == record[0] and record[1] == recordset.record_type:
                # We explicitly do not want to modify records that have more than one entry.
                if len(recordset.rrdatas) > 1:
                    no_touch = True
                    break
                # Check the TTL length
                existing_record = True
                if ttl != recordset.ttl:
                    ttl_diff = True
                # Small if/else for A/AAAA records
                if (recordset.record_type == "A") and (str(recordset.rrdatas[0]) == str(v4ip)):
                    no_touch = True
                    if ttl_diff:
                        no_touch = False
                        resource_record_set = recordset
                    break
                elif (recordset.record_type == "AAAA") and (str(recordset.rrdatas[0]) == str(v6ip)):
                    no_touch = True
                    if ttl_diff:
                        no_touch = False
                        resource_record_set = recordset
                    break
                else:
                    no_touch = False
                    resource_record_set = recordset
                    break
            else:
                no_touch = False
                pass
        if existing_record:
            existing_del[str(resource_record_set.name)] = resource_record_set
        if not no_touch:
            create['{0}.{1}'.format(record[0], record[1])] = record
    return existing_del, create, len(existing_del)


def delete_records(my_zone_int, existing_del, new_create):
    my_zone_changes = my_zone_int.changes()
    for k, v in existing_del.items():
        my_zone_changes.delete_record_set(v)
    my_zone_changes.create()
    while my_zone_changes.status != 'done':
        time.sleep(1)
        my_zone_changes.reload()
    return existing_del, new_create


def add_records(my_zone_int, new_create, v4ip, v6ip, ttl):
    # begin the main bits of the script
    # iterating over the `zones_to_edit1` dictlist and updating DNS for each zone
    my_zone_changes = my_zone_int.changes()
    changes_returned_internal = []
    for _, value in new_create.items():
        if not value[0].endswith("."):
            value[0] = '{0}.'.format(value[0])
        if value[1] == "A" and v4ip is not None:
            rrs = my_zone_int.resource_record_set(value[0], 'A', ttl, [v4ip, ])
            my_zone_changes.add_record_set(rrs)
            changes_returned_internal.append(rrs)
        if value[1] == "AAAA" and v6ip is not None:
            rrs = my_zone_int.resource_record_set(value[0], 'AAAA', ttl, [v6ip, ])
            my_zone_changes.add_record_set(rrs)
            changes_returned_internal.append(rrs)
    my_zone_changes.create()
    while my_zone_changes.status != 'done':
        time.sleep(1)
        my_zone_changes.reload()
    return changes_returned_internal, len(my_zone_changes.additions)


if __name__ == '__main__':
    # Run script
    arg_ns = argparser()
    auto_proceed(arg_ns)
    scoped_credentials = load_creds()
    ipv4ip, ipv6ip = retrieve_addresses(arg_ns)
    gdnsclient = gdns.Client(project=scoped_credentials.project_id, credentials=scoped_credentials)
    zone_list = all_zones(gdnsclient)
    zones_to_edit, passed_records_with_no_zone = zones_to_edit_func(zone_list, arg_ns.record)
    for zone_key, records_to_change in zones_to_edit.items():
        my_zone = zone_list[str(zone_key)]
        print("Currently gathering records for {0}".format(my_zone.dns_name))
        # Check for existing records before doing anything
        existing_to_delete, to_create, _ = check_records(my_zone, records_to_change, ipv4ip, ipv6ip, arg_ns.ttl)
        # Delete existing records
        if existing_to_delete and to_create:
            existing_to_delete, to_create = delete_records(my_zone, existing_to_delete, to_create)
        # If we have records to create, we do it here
        # Else, take no action
        if to_create:
            changes_returned, len_additions = add_records(my_zone, to_create, ipv4ip, ipv6ip, arg_ns.ttl)
            print("Created {0} record{1}.\n".format(len_additions, 's' if len_additions != 1 else ''))
        else:
            print("All given records for {0} are up to date. Not performing any actions on this zone.\n".
                  format(my_zone.dns_name))
