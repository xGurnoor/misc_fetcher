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
import sqlite3
import argparse
import requests

from prettytable import PrettyTable

parser = argparse.ArgumentParser(
    prog="MiscFetcher",
    description='Gets and calculated misc of given username',
    epilog="APIs for the win"
)

parser.add_argument('-H', '--human', 
                    action="store_true", help='shows data in human readable numbers')
parser.add_argument('-u', '--username', help="The username to serach", nargs=argparse.REMAINDER)

args = parser.parse_args()
username = args.username
if not username:
    parser.print_help()
    sys.exit()

with open("tokens.json", 'r', encoding="UTF-8") as f:
    tokens = json.load(f)

ACCESS_TOKEN = tokens['access_token']
REFERSH_TOKEN = tokens['refresh_token']
EXCEPTION_COUNTER = {"count": 0}

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
        print(f'{EXCEPTION_COUNTER["count"]}: Session expired. Fetching new token and retrying...')
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
    with open('tokens.json', 'w', encoding='UTF-8') as fp:
        json.dump(tokens, fp, indent=4)
    return new_token

def get_access_token():
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
    return r.json()['access_token']

def build_techtree():
    """Builds the TechTree from SQLite DB and stores in a dict"""
    temp_tree = {}

    db = sqlite3.connect('techtree.sqlite')

    cur = db.cursor()
    res = cur.execute(
        'SELECT id, optionals_json, base_id FROM counterunit')

    result = res.fetchall()

    cur.close()
    db.close()

    for x in result:
        temp_tree[x[0]] = json.loads(x[1])
        temp_tree[x[0]]['base_id'] = x[2]

    return temp_tree

def calculate(stats_, techtree_):
    """Do the calculation"""

    total_att = 0
    total_def = 0

    total_att_per = 0
    total_def_per = 0

    for stat in stats_:
        item = techtree_[stat['id']]
        if item['base_id']:
            continue
        is_per = item.get('percentage')
        if is_per is None:
            continue
        if is_per:
            total_att_per += item.get('attack', 0) * stat.get("count")
            total_def_per += item.get('spy_attack', 0) * stat.get("count")
        else:
            total_att += item.get('attack', 0) * stat.get("count")
            total_def += item.get('spy_attack', 0) * stat.get("count")

    return (
        total_att,
        total_def,
        total_att_per,
        total_def_per
        )

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



if __name__ == "__main__":
    profile = get_profile(ACCESS_TOKEN, username)
    showcase = profile.get('showcase')
    if not showcase:
        print('No showcase present in profile?')
        sys.exit(5)

    tech_tree = build_techtree()
    att, defen, att_per, defen_per, = calculate(showcase, tech_tree)

    t = PrettyTable(['Str', 'Int', 'Total', 'Str%', 'Int%'])
    total = att + defen
    if args.human:
        att = convert_to_human(att)
        defen = convert_to_human(defen)
        total = convert_to_human(total)
    t.add_row([att, defen, f"{total}cs", f"{att_per}%", f"{defen_per}%"])
    print(t)
