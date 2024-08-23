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

import sqlite3
import argparse
import sys

parser = argparse.ArgumentParser(
    description='Adds a token to the ally database',
    epilog="APIs for the win"
)


parser.add_argument('-a', '--access',
                    help="The acccess tokeb")
parser.add_argument('-r', '--refresh',
                    help="The refresh token to use")

parser.add_argument('-c', '--client_info',
                    help="The client info to use")

parser.add_argument('-f', '--file',
                    help="File to add tokens from")
args = parser.parse_args()
if not args.file and not any([args.access, args.refresh, args.client_info]):
    print('access_token, refresh_token and client_info are required if file is not provided')
    parser.print_help()
    sys.exit()

conn = sqlite3.connect('data/stats.db')


if __name__ == "__main__":
    sql = 'INSERT INTO tokens(access_token, refresh_token, client_info) VALUES(?, ?, ?)'
    if not args.file:
        a_token = args.access
        r_token = args.refresh
        c_info = args.client_info

        conn.execute(sql,
                     (a_token, r_token, c_info))
        conn.commit()
        conn.close()

        print('Token added successfully')
    else:
        file = args.file
        with open(file, 'r', encoding='utf-8') as fp:
            l = fp.readlines()
            args = []
            for x in l:
                refresh_token, client_info = x.split(":SPLIT:")
                client_info = client_info.replace("'", '"')
                client_info = client_info.replace("False", "false")
                args.append(('placeholder', refresh_token, client_info))
            conn.executemany(sql, args)
            conn.commit()
            conn.close()
        print('Tokens added succesfully.')
