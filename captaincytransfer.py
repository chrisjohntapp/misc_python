#!/usr/bin/python3
import requests
import json
# import os
import subprocess
import getpass
import csv
import sys
# stackfile = "teststack.csv"
stackfile = sys.argv[1]


def getVaultToken():
    print("### Get vault token")
    username = getpass.getuser() + "@splunk.com"
    password = getpass.getpass()
    data = '{"password": "' + password + '"}'
    try:
        print("### Please verify 2FA")
        r = requests.post('https://vault.splunkcloud.systems/v1/auth/okta/login/' + username, data=data)
        data = json.loads(r.text)
        fs = open(".token", "w+")
        fs.write(data['auth']['client_token'])
        fs.close()
        return data['auth']['client_token']
    except:
        return "Error in getVaultToken"


def getCredentials(stack, token, host):
    headers = {
        'Authorization': 'Bearer ' + token,
    }
    url = 'https://vault.splunkcloud.systems/v1/cloud-sec-lve-ephemeral/creds/' + stack + '-admin/' + host
    print()
    r = requests.get('https://vault.splunkcloud.systems/v1/cloud-sec-lve-ephemeral/creds/' + stack + '-admin/' + host, headers=headers)
    if r.status_code == 403 or r.status_code == 401:
        print("### The API call to generate Ephemeral Credentials returned a " + r.status_code + ", as such we need to refresh the token.")
        getVaultToken()
        print("### Please try to execute the script again.")
        exit()
    else:
        print(r)
        data = json.loads(r.text)
        return("'" + data['data']['username'] + ":" + data['data']['password'] + "'")


def readVaultToken():
    try:
        f = open(".token", "r")
        token = f.read()
        return token
        f.close()
    except:
        return "token file does not exist"


def executeCaptainChange(token):
    with open(stackfile, "rt") as f:
        lookup_table = csv.DictReader(f, delimiter=',')
        for row in lookup_table:
            stack = row['stack']
            host = row['host']
            credentials = getCredentials(stack, token, host)
            # Prepare shell script
            print("##### Proceeding with stack:", stack, "(transfering captain to:", host, ")")
            fs = open("captain_change.sh", "w+")
            fs.write("#!/bin/bash")
            fs.write("\n\n")
            fs.write("logger --id=$$ -t transfer_captaincy_script 'Start transfer captaincy'")
            fs.write("\n")
            fs.write("stdout=`curl -ksS -u " + credentials + " ")
            fs.write("'https://localhost:8089/services/shcluster/member/consensus/foo/transfer_captaincy?output_mode=json' ")
            fs.write("-X POST -d mgmt_uri=https%3A%2F%2F" + host + "%3A8089`\n")
            fs.write("echo ${stdout}\n")
            fs.write("logger --id=$$ -t transfer_captaincy_script \"task_uuid=$UUID stepnum=1 step=\\\"send_api\\\" msg=\\\"${stdout}\\\"\"\n")
            fs.write("logger --id=$$ -t transfer_captaincy_script 'End transfer captaincy'")
            fs.write("\n")
            fs.close()
            subprocess.run(["chmod", "+x", "captain_change.sh"])
            # Copy script to host
            scpScript(host)
            # Execute script on host
            executeScript(host)
            # # Delete script from host
            removeScript(host)


def scpScript(host):
    print("Copying script to", host)
    subprocess.call(["scp", "captain_change.sh", getpass.getuser() + "@" + host.split('.')[0] + ":/home/" + getpass.getuser()])


def executeScript(host):
    print("Executing script on", host)
    result = subprocess.run(["sft", "ssh", host.split('.')[0], "--command", "./captain_change.sh"], capture_output=True)
    print(result.stdout)
    if result.returncode:
        print("Curl returned {}".format(result.returncode))
    if result.stderr:
        print("Curl stderr: {}".format(result.stderr))


def removeScript(host):
    print("Removing script on", host)
    subprocess.run(["sft", "ssh", host.split('.')[0], "--command", "rm captain_change.sh"])


if __name__ == "__main__":
    vaulttoken = readVaultToken()
    if vaulttoken == "token file does not exist":
        print("### Token file does not exist, requesting new token.")
        try:
            getVaultToken()
            print("### Token saved.")
            print("### Trying to execute the script again.")
            executeCaptainChange(readVaultToken())
        except:
            print("## Error")
    else:
        executeCaptainChange(vaulttoken)
