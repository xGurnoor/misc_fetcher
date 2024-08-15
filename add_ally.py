"""Adds given username into the SQLite database after getting their ID"""

import sys
import sqlite3
import argparse
import json

import requests

conn = sqlite3.connect('data/stats.db')

parser = argparse.ArgumentParser(
    prog="MiscFetcher",
    description='Gets and calculated misc of given username',
    epilog="APIs for the win"
)


parser.add_argument('-u', '--username',
                    help="The list to use", required=True, nargs=argparse.REMAINDER)


with open("tokens.json", 'r', encoding="UTF-8") as f:
    tokens = json.load(f)

ACCESS_TOKEN = tokens['access_token']
REFERSH_TOKEN = tokens['refresh_token']
EXCEPTION_COUNTER = {"count": 0}
CLIENT_INFORMATION = json.dumps(tokens['client_information'])


def get_profile(profile_name, token=None):
    """Gets the profile data by username"""
    url = "https://api.partyinmydorm.com/game/user/get_profile_by_username/"

    if not token:
        token = ACCESS_TOKEN

    r = requests.post(url, data={"profile_username": profile_name}, timeout=400, headers={
        "Authorization": f"Bearer {token}", "user-agent": "pimddroid/526"})
    res = r.json()
    # fp = open('testing/new_prof.json', 'w', encoding='utf-8')
    # json.dump(res, fp, indent=2)
    # fp.close()
    ex = res.get('exception')
    if not ex:
        return res

    if "Session expired" in ex:
        if EXCEPTION_COUNTER['count'] > 3:
            print('Failed to fetch new valid access token 3 times. Exiting.')
            sys.exit(3)

        EXCEPTION_COUNTER['count'] += 1
        print(
            f'{EXCEPTION_COUNTER["count"]}: Session expired. Fetching new token and retrying...')
        new_token = update_access_token()
        return get_profile(profile_name, new_token)

    if "Username doesn't exist" in ex:
        print(ex)
        sys.exit(6)

    print("Unknown error: ", res)
    sys.exit(4)


def update_access_token():
    """Tries to update the access token"""
    new_token = get_access_token()
    tokens['access_token'] = new_token
    with open('tokens.json', 'w', encoding='UTF-8') as tokens_fp:
        json.dump(tokens, tokens_fp, indent=4)
    return new_token


def get_access_token(resp=False):
    """Fetchs new access token"""
    url = "https://api.partyinmydorm.com/game/login/oauth/"
    payload = {
        "channel_id": "16",
        "client_id": "ata.squid.pimd",
        "client_version": "534",
        "refresh_token": REFERSH_TOKEN,
        "scope": "[\"all\"]",
        "version": "3310",
        "client_secret": "n0ts0s3cr3t",
        "grant_type": "refresh_token",
        "client_information": CLIENT_INFORMATION
    }
    r = requests.post(url, payload, timeout=400)
    if resp:
        rsp = r.json()
        return [rsp, rsp['access_token']]

    return r.json()['access_token']


if __name__ == "__main__":

    args = parser.parse_args()
    username = args.username[0]

    profile = get_profile(username)
    uid = profile['user_id']

    cur = conn.cursor()
    cur.execute(
        'INSERT INTO allies (username, profile_id) VALUES (?, ?)', (username, uid))
    conn.commit()
    print("Add ally with username: "
          f"{username} and ID: {uid} to the ally database")
