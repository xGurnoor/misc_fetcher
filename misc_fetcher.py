# MIT License

# Copyright (c) [2026] [Gurnoor Singh]

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
import logging
import os
import sys
import json
import sqlite3
import argparse


from prettytable import PrettyTable
from util.utils import Row, convert_to_human, ProxyManager
from util.api import API, UsernameNotFound

parser = argparse.ArgumentParser(
    description='Gets and calculated misc of given username',
    epilog="APIs for the win"
)

parser.add_argument('-H', '--human',
                    action="store_true", help='shows data in human readable numbers')
parser.add_argument('-s', '--stacks',
                    action="store_true", help="If you want stacks to be saved to file.")
parser.add_argument('-c', '--count',
                    type=int, default=2, help="What count of misc is cut to be included in stacks")
parser.add_argument('-S', '--shell',
                    help="Is this used as a shell command", default=False, action="store_true")
parser.add_argument('-f', '--file',
                    help="Save fetched profle to a temp file.", action='store_true')
parser.add_argument('-r', '--relationship',
                    help="Fetch misc from given user's relationship.", action='store_true')
parser.add_argument('-u', '--username',
                    help="The username to search", nargs=argparse.REMAINDER)
parser.add_argument('-d', '--debug',
                    help="Enable debug logging", action='store_true')

parser.add_argument('-t', '--test-ip',
                    help='Test and show what IP is being used', action='store_true')

args = parser.parse_args()

if args.username:
    username = args.username[0]

else:
    parser.print_help()
    sys.exit(1)

with open('proxylist.txt', 'r', encoding='utf-8') as fp:

    proxy_manager = ProxyManager(fp)

db = sqlite3.connect('data/stats.db')
techdb = sqlite3.connect('techtree.sqlite')

logger = logging.getLogger('Misc Fetcher')

if args.debug:
    logging.basicConfig(level=logging.DEBUG)   
    logger.debug('Debug logging enabled')
    print('Debug logging enabled')
else:   
    logging.basicConfig(level=logging.INFO)

db.row_factory = Row
STACK_LIST: list[str] = []

tcur = db.cursor()
tcur.execute('SELECT * FROM tokens')

data = tcur.fetchone()
tcur.close()

api = API(data, db, proxy=proxy_manager.get(), proxy_manager=proxy_manager, test_ip=args.test_ip)

db.execute(
    'CREATE TABLE IF NOT EXISTS tokens(access_token TEXT, refresh_token TEXT, client_info TEXT)')


def refetch(techtree):
    """Refetches new misc items and add to techtree"""

    rsp = api.get_access_token(resp=True)
    logger.debug(f'Fetched new access token: debug_info.json')
    json.dump(rsp, open('debug_info.json', 'w'), indent=2)
    cur = techdb.cursor()

    resp = rsp[0]
    items = resp['new_items']
    logger.debug(f'New items fetched: {items}') 

    for item in items:
        if techtree.get(item['id']):
            continue

        id_ = item['id']
        desc = item['description']
        name = item['name']

        base_id = item.get('base_id', 0)
        att_ = item.get('attack', 0)
        int_att = item.get('spy_attack', 0)
        per = item.get('percentage', 0)

        optionals_json = json.dumps(
            {"attack": att_, "spy_attack": int_att, "percentage": per})
        cur.execute(
            'INSERT INTO counterunit (id, optionals_json, base_id, name, description) VALUES (?, ?, ?, ?, ?)', [id_, optionals_json, base_id, name, desc])
    cur.close()
    techdb.commit()


def build_techtree():
    """Builds the TechTree from SQLite DB and stores in a dict"""
    temp_tree = {}

    cur = techdb.cursor()
    res = cur.execute(
        'SELECT id, optionals_json, base_id, name FROM counterunit')

    result = res.fetchall()

    cur.close()

    for x in result:
        temp_tree[x[0]] = json.loads(x[1])
        temp_tree[x[0]]['base_id'] = x[2]
        temp_tree[x[0]]['name'] = x[3]

    return temp_tree


def calculate(stats_, techtree_):
    """Do the calculation"""

    total_att = 0
    total_def = 0

    total_att_per = 0
    total_def_per = 0

    for stat in stats_:
        item = techtree_.get(stat['id'])
        if not item:
            print("Item ID: "
                  f"{stat['id']} not present in TechTree DB. Refetching.")
            refetch(techtree_)
            sys.exit(0)

        if item['base_id']:
            continue

        is_per = item.get('percentage')
        if is_per is None:
            continue

        if args.stacks:
            if stat.get("count") > args.count and stat.get('count') < 251:

                if item.get("name"):

                    STACK_LIST.append(f"{stat['count']}: {item['name']}")

        if is_per:
            total_att_per += item.get('attack', 0) * stat.get("count")
            total_def_per += item.get('spy_attack', 0) * stat.get("count")

        else:
            total_att += item.get('attack', 0) * stat.get("count")
            total_def += item.get('spy_attack', 0) * stat.get("count")

    if args.stacks:
        # Save stack list to file with username.
        with open(f"stacks/{username}.list", "w", encoding="utf-8") as stack_f:
            stack_f.write("\n".join(STACK_LIST))

    return (
        total_att,
        total_def,
        total_att_per,
        total_def_per
    )


if __name__ == "__main__":

    try:
        profile = api.get_profile(username)
        if args.relationship:
            rs = profile.get('partner_username')
            if not rs:
                print(f'Given username ({username}) has no relationsip.')
                sys.exit(2)
            username = rs
            profile = api.get_profile(rs)

    except UsernameNotFound:
        print('Username not found.')
        sys.exit(0)
    
    if args.file:
        if not os.path.exists('temp'):
            os.mkdir('temp')
        
        with open('temp/profile.json', 'w') as f:
            json.dump(profile, f, indent=2)

    showcase = profile.get('showcase')

    if not showcase:
        print('No showcase present in profile.')
        sys.exit(0)

    tech_tree = build_techtree()
    att, defen, att_per, defen_per, = calculate(showcase, tech_tree)

    t = PrettyTable(['Str', 'Int', 'Total', 'Str%', 'Int%'])
    total = att + defen
    if args.human:
        att = convert_to_human(att)
        defen = convert_to_human(defen)
        total = convert_to_human(total)

    if not args.shell:
        t.add_row([att, defen, f"{total}cs", f"{att_per}%", f"{defen_per}%"])
        print(f'Stats for {username}')
        print(t)

    else:
        print(json.dumps({"attack": att, "defence": defen, "total": total}))
