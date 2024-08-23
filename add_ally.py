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
"""Adds given username into the SQLite database after getting their ID"""

import sys
import sqlite3
import argparse

from prettytable.colortable import ColorTable, Themes

from utils.utils import ProxyManager, Row
from utils.api import API


parser = argparse.ArgumentParser(
    description='Adds an ally to the ally database',
    epilog="APIs for the win"
)


parser.add_argument('-l', '--list',
                    help="List all the added allies", default=False, action="store_true")
parser.add_argument('-u', '--username',
                    help="The username(s) to add", nargs=argparse.REMAINDER)
args = parser.parse_args()
if not args.list and not args.username:
    print("No arguments supplied.")
    parser.print_help()
    sys.exit()

conn = sqlite3.connect('data/stats.db')
conn.row_factory = Row

cur = conn.cursor()
cur.execute('SELECT * FROM tokens')

data = cur.fetchone()
cur.close()

with open('proxylist.txt', 'r', encoding='utf-8') as fp:
    proxy_manager = ProxyManager(fp)

api = API(data, conn, proxy=proxy_manager.get())

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

    for username in args.username:

        profile = api.get_profile(username)
        uid = profile['user_id']
        username = profile['username']
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO allies (username, profile_id) VALUES (?, ?)', (username, uid))
        conn.commit()
        print("Added ally with username: "
              f"{username} and ID: {uid} to the ally database")
