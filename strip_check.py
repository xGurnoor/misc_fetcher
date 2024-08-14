# MIT License

# Copyright (c) [2024] [Gurnoor Singh]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Script to get and calculate misc"""

import sys
import json
import os
import argparse
import time
import threading
import requests

# pylint: disable=wrong-import-order
from collections import namedtuple
from discord import Embed, SyncWebhook, Color

parser = argparse.ArgumentParser(
    prog="MiscFetcher",
    description='Gets and calculated misc of given username',
    epilog="APIs for the win"
)


parser.add_argument('-l', '--list',
                    help="The list to use", default="allies.json", nargs=argparse.REMAINDER)


args = parser.parse_args()
if isinstance(args.list, list):
    args.list = ' '.join(args.list)
if args.list.strip() == '':
    print('Provide a value for \'list\' parameter.')
    sys.exit(3)

with open("tokens.json", 'r', encoding="UTF-8") as f:
    tokens = json.load(f)

if not os.path.exists('allies.json'):
    with open('allies.json', 'w', encoding='utf-8') as fp:
        dump = {"usernames": []}
        json.dump(dump, fp)

with open('allies.json', 'r', encoding='utf-8') as fp:
    ALLIES = json.load(fp)

if not ALLIES:
    print("allies.json is empty.")
    sys.exit(4)
if not os.path.exists('stats'):
    os.mkdir('stats')
if not os.path.exists('stats/tut_list.json'):
    with open('stats/tut_list.json', 'w', encoding='utf-8') as fp:
        fp.write('{}')
with open('stats/tut_list.json', 'r', encoding='utf-8') as fp:
    TUT_LIST = json.load(fp)

# globals
ACCESS_TOKEN = tokens['access_token']
REFERSH_TOKEN = tokens['refresh_token']
WEBHOOK_URL = tokens['discord_webhook_url']
CLIENT_INFORMATION = json.dumps(tokens['client_information'])
EXCEPTION_COUNTER = {"count": 0}
STOP = False
WATCH_LIST = []
BATTLE_STATS = {}

BattleStats = namedtuple('BattleStats', ['fl', 'dl', 'pl', 'el'])


def get_profile(token, profile_name):
    """Gets the profile data by username"""
    url = "https://api.partyinmydorm.com/game/user/get_profile_by_username/"
    r = requests.post(url, data={"profile_username": profile_name}, timeout=400, headers={
        "Authorization": f"Bearer {token}", "user-agent": "pimddroid/526"})
    res = r.json()
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
        return get_profile(new_token, profile_name)
    elif "Username doesn't exist" in ex:
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


def convert_to_human(i: int):
    """Converts given long numbers into human readable"""

    if i >= 1_000_000_000:
        temp = i / 1_000_000_000
        return f"{temp:.2f}B"
    if i >= 1_000_000:
        temp = i / 1_000_000
        return f"{temp:.2f}M"
    if i >= 1000:
        temp = i / 1000
        return f"{temp:.2f}K"
    return i


def check_tuts():
    """Checks the tutors for strips for all allies."""
    for username in ALLIES['usernames']:
        profile = get_profile(ACCESS_TOKEN, username)
        # json.dump(profile, open("test.json", "w"), indent=2)
        # exit()
        temp = profile.get('clan_members')
        fl = profile.get('fights_lost')
        dl = profile.get('steals_lost')
        pl = profile.get('assassinates_lost')
        el = profile.get('scouts_lost')
        battle_sts = BattleStats(fl, dl, pl, el)
        tutors = []
        for x in temp:
            tut = {'user_id': x['user_id'], 'username': x['username']}
            tutors.append(tut)
        # print(f"IGN: {username}: \n", json.dumps(tutors, indent=2))
        old_list = TUT_LIST.get(username)
        if not old_list:
            TUT_LIST[username] = tutors
            with open('stats/tut_list.json', 'w', encoding='utf-8') as tut_list_fp:
                json.dump(TUT_LIST, tut_list_fp, indent=2)
        else:
            temp1 = []
            for x in tutors:
                temp1.append(x['username'])

            temp2 = []
            for x in old_list:
                temp2.append(x['username'])
            missing = set(temp2).difference(temp1)
            added = set(temp1).difference(temp2)
            if missing or added:

                TUT_LIST[username] = tutors
                with open('tut_list.json', 'w', encoding='utf-8') as tut_list_fp:
                    json.dump(TUT_LIST, tut_list_fp, indent=2)
                if missing:
                    confirm_strip(missing, username, battle_sts)
                    # alert_server(username, list(missing), list(added))
        time.sleep(2)


def confirm_strip(missing, username, battle_sts):
    """Takes in missing tuts and checks who hired to confirm
      they were hired away not buried in the tut list"""
    missing_tut_list = []
    hired = 0
    for miss in missing:
        profile = get_profile(ACCESS_TOKEN, miss)
        hv = profile.get("value")
        hired += hv
        owner = profile.get('owner')
        if not owner or not owner['username'].lower() == username.lower():
            missing_tut_list.append([miss, hv])
    if not missing_tut_list:
        return
    alert_server(username, missing=missing_tut_list, total=hired)
    if not BATTLE_STATS.get(username):
        t = threading.Thread(target=watch_fls, args=(
            username, battle_sts), daemon=True)
        t.start()


def watch_fls(username, bsts):
    """Function ran in thread to repeatedly check if FLs are increasing."""
    if not BATTLE_STATS.get(username):
        BATTLE_STATS[username] = bsts
    unchanged = 0
    while True:

        profile = get_profile(ACCESS_TOKEN, username)

        fl = profile.get('fights_lost')
        dl = profile.get('steals_lost')
        pl = profile.get('assassinates_lost')
        el = profile.get('scouts_lost')
        new_bsts = BattleStats(fl, dl, pl, el)

        if not fl == bsts.fl or not dl == bsts.dl:
            alert_fls(username, new_bsts, bsts)
            bsts = new_bsts
            unchanged = 0

        else:

            if unchanged >= 5:
                alert_fls(username, stopping=True)
                del BATTLE_STATS[username]
                break
            alert_fls(username, nochange=True)
            unchanged += 1

        time.sleep(10)


def alert_fls(username, new_stats=None, prev_stats=None, nochange=False, stopping=False):
    """Alerts the server about any battle stats changes on potentianl strip"""
    wh = SyncWebhook.from_url(WEBHOOK_URL)
    if nochange:
        return wh.send(f"No change in battle losses for `{username}`")

    if stopping:
        return wh.send("No change in battle losses for"
                       f"`{username}` in 5 consecutive checks, stopped checking.")

    initial = BATTLE_STATS[username]

    fl_diff = new_stats.fl - prev_stats.fl
    dl_diff = new_stats.dl - prev_stats.dl

    total_fl = new_stats.fl - initial.fl
    total_dl = new_stats.dl - initial.dl

    b_str = f'FL new: {new_stats.fl} old: {prev_stats.fl} change: {fl_diff}\n' \
        f'DL new {new_stats.dl} old: {prev_stats.dl} change: {dl_diff}\n\n' \
        f'Total losses till now: FL: {total_fl} DL: {total_dl}'

    embed = Embed(title=f"Battle losses update for {username}",
                  description=b_str, color=Color.brand_red())

    embed.add_field(name="Initial stats",
                    value=f"FL: {initial.fl} DL: {initial.dl}")

    wh.send(content="@everyone", embed=embed)


def alert_server(person, missing=None, added=None, total=None):
    """Inform the server of someone missing a tutor in tutor list."""
    embed = Embed(title="Strip alert",
                  description=f"{person} was potentially stripped.", color=Color.blurple())
    if missing:
        missing_str = []
        for x in missing:
            missing_str.append(f"{x[0]}: ${convert_to_human(x[1])}")
        missing_str.append(f'\n\nTotal stripped: ${convert_to_human(total)}')
        embed.add_field(name="Tutors missing",
                        value="\n".join(missing_str), inline=False)
    if added:
        added = [f"`{x}`" for x in added]
        embed.add_field(name="New tutors hired",
                        value=", ".join(added), inline=False)
    wh = SyncWebhook.from_url(WEBHOOK_URL)
    wh.send(content="@everyone", embed=embed)


if __name__ == "__main__":
    try:
        print('Starting tutor checker.')
        while not STOP:
            print('Checking tutors.')
            check_tuts()
            time.sleep(20)
    except KeyboardInterrupt:
        STOP = True
        print('Exiting...')
        sys.exit(0)