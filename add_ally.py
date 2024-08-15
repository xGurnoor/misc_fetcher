"""Adds given username into the SQLite database after getting their ID"""

import sys
import sqlite3
import argparse
import json

import requests
from prettytable.colortable import ColorTable, Themes


parser = argparse.ArgumentParser(
    description='Adds an ally to the ally database',
    epilog="APIs for the win"
)


parser.add_argument('-l', '--list',
                    help="List all the added allies", default=False, action="store_true")
parser.add_argument('-u', '--username',
                    help="The list to use", nargs=argparse.REMAINDER)
args = parser.parse_args()
if not args.list and not args.username:
    print("No arguments supplied.")
    parser.print_help()
    sys.exit()


class Row(sqlite3.Row):
    """Overriden row class to make row data printable
    Not performant."""

    def __repr__(self) -> str:
        return str(dict(self))

    def get(self, key):
        """Mimic get function from builtin Dict class"""
        try:
            return self[key]
        except IndexError:
            return None


conn = sqlite3.connect('data/stats.db')
conn.row_factory = Row

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

    resp = requests.post(url, data={"profile_username": profile_name}, timeout=400, headers={
        "Authorization": f"Bearer {token}", "user-agent": "pimddroid/526"})
    res = resp.json()
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
    res = requests.post(url, payload, timeout=400)
    if resp:
        rsp = res.json()
        return [rsp, rsp['access_token']]

    return res.json()['access_token']


if __name__ == "__main__":
    if args.list:

        t = ColorTable(['Name', 'ID'], theme=Themes.OCEAN)

        cur = conn.cursor()
        cur.execute('select * from allies')

        r = cur.fetchall()

        cur.close()

        for ally in r:
            t.add_row([ally['username'], ally['profile_id']])

        print(t)
    if not args.username:
        sys.exit()

    username = args.username[0]

    profile = get_profile(username)
    uid = profile['user_id']

    cur = conn.cursor()
    cur.execute(
        'INSERT INTO allies (username, profile_id) VALUES (?, ?)', (username, uid))
    conn.commit()
    print("Add ally with username: "
          f"{username} and ID: {uid} to the ally database")
