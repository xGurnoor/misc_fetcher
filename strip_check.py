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
import requests

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
    exit(3)

with open("tokens.json", 'r', encoding="UTF-8") as f:
    tokens = json.load(f)

if not os.path.exists('allies.json'):
    with open('allies.json', 'w', encoding='utf-8') as fp:
        t = {"usernames": []}
        json.dump(t, fp)

with open('allies.json', 'r', encoding='utf-8') as fp:
    ALLIES = json.load(fp)

if not ALLIES:
    print("allies.json is empty.")
    sys.exit(4)

if not os.path.exists('tut_list.json'):
    with open('tut_list.json', 'w', encoding='utf-8') as fp:
        fp.write('{}')
with open('tut_list.json', 'r', encoding='utf-8') as fp:
    TUT_LIST = json.load(fp)

ACCESS_TOKEN = tokens['access_token']
REFERSH_TOKEN = tokens['refresh_token']
WEBHOOK_URL = tokens['discord_webhook_url']
EXCEPTION_COUNTER = {"count": 0}
STOP = False


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
        "client_version": "526",
        "refresh_token": REFERSH_TOKEN,
        "scope": "[\"all\"]",
        "version": "3137",
        "client_secret": "n0ts0s3cr3t",
        "grant_type": "refresh_token",
        "client_information":
        # pylint: disable=line-too-long
        "{\"android_advertising\":\"002cca36-c10a-4217-829c-78d383a279a5\",\"android_id\":\"fd744b22575e3de1\",\"app_set_id\":\"a443de33-41a2-45a0-9c30-2669a012b6c2\",\"bundle_id\":\"ata.squid.pimd\",\"country\":\"US\",\"dpi\":\"xxhdpi\",\"ether_map\":{\"1\":\"02:00:00:00:00:00\"},\"hardware_version\":\"google|Android SDK built for x86\",\"language\":\"en\",\"limit_ad_tracking\":false,\"locale\":\"en_US\",\"os_build\":\"Build\\/QSR1.190920.001\",\"os_name\":\"Android\",\"os_version\":\"10\",\"referrer\":\"utm_source=google-play&utm_medium=organic\",\"screen_size\":\"screen_normal\",\"user_agent\":\"Mozilla\\/5.0 (Linux; Android 10; Android SDK built for x86 Build\\/QSR1.190920.001; wv) AppleWebKit\\/537.36 (KHTML, like Gecko) Version\\/4.0 Chrome\\/74.0.3729.185 Mobile Safari\\/537.36\",\"version_name\":\"7.00\"}"
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
        tutors = []
        for x in temp:
            tut = {'user_id': x['user_id'], 'username': x['username']}
            tutors.append(tut)
        # print(f"IGN: {username}: \n", json.dumps(tutors, indent=2))
        old_list = TUT_LIST.get(username)
        if not old_list:
            TUT_LIST[username] = tutors
            with open('tut_list.json', 'w', encoding='utf-8') as tut_list_fp:
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

                alert_server(username, list(missing), list(added))
        time.sleep(2)


def alert_server(person, missing=None, added=None):
    """Inform the server of someone missing a tutor in tutor list."""
    embed = Embed(title="Some retard got stripped",
                  description="GET REKT LOL", color=Color.blurple())
    embed.add_field(name="The retard", value=person)
    if missing:
        missing = [f"`{x}`" for x in missing]
        embed.add_field(name="Tutors missing",
                        value=", ".join(missing), inline=False)
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
            time.sleep(30 * 60)
    except KeyboardInterrupt:
        print('Exiting...')
        sys.exit(0)
