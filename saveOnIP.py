#!/usr/bin/python3

# DyDNS alike purposed script to apply A record(s) for newly started EC2 instance
# allows to save money on elastic ip addresses
# create your own hosted zone and use its id in there
# you can put it like in /etc/rc.local and use assigned A record to enter host
# do not forget to assign Route53 role to EC2 instance to have rights for boto to run its instructions

import boto3
import subprocess

zoneid = 'yourzoneid'
name1 = 'hostname1'
name2 = 'hostname2'
weight = 99
TTL = 600
atype = 'A'

# FORCE DELETE old A records since UPSERT can't recognize right after shutdown

try:
    response = boto3.client('route53').list_resource_record_sets(HostedZoneId=zoneid)
    for rset in response['ResourceRecordSets']:
        if rset['Name'] in [name1+'.', name2+'.']:
            nam = (rset['Name'])
            ip = (rset['ResourceRecords'][0]['Value'])
            resp = boto3.client('route53').change_resource_record_sets(
                HostedZoneId=zoneid,
                ChangeBatch={
                    'Comment': 'FORCE DELETE orphaned A records for '+nam,
                    'Changes':
                    [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet':
                            {
                                'Name': nam, 'Type': atype, 'SetIdentifier': '__A__ record for '+ip, 'Weight': weight, 'TTL': TTL, 'ResourceRecords': [
                                    {'Value': ip},
                                ],
                            } 
                        },
                    ]
                }
            )
            print (resp)
except (RuntimeError):
    print ('Error during FORCE DELETE')

# creating couple A records for the only host

try:
    ipaddress = subprocess.check_output(
        ['curl -s http://169.254.169.254/latest/meta-data/public-ipv4'], shell=True, universal_newlines=True)
except subprocess.CalledProcessError as e:
    return_code = e.returncode

response = boto3.client('route53').change_resource_record_sets(
    HostedZoneId=zoneid,
    ChangeBatch={
        'Comment': 'UPSERT hostname for '+ipaddress,
        'Changes':
        [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet':
                {
                    'Name': name1, 'Type': atype, 'SetIdentifier': '__A__ record for '+ipaddress, 'Weight': weight, 'TTL': TTL, 'ResourceRecords': [
                            {'Value': ipaddress},
                    ],
                }
            },
            {
                'Action': 'UPSERT',
                'ResourceRecordSet':
                {
                    'Name': name2, 'Type': atype, 'SetIdentifier': '__A__ record for '+ipaddress, 'Weight': weight, 'TTL': TTL, 'ResourceRecords': [
                            {'Value': ipaddress},
                    ],
                }
            },
        ]
    }
)
print(response)
