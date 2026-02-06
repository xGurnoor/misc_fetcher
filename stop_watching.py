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
"""Util to stop strip checker from watching an ally"""

import os
import json
import signal
import argparse
import subprocess
import sys

try:
    PID = int(subprocess.check_output(['pidof', 'stripper']).decode().strip())
except subprocess.CalledProcessError:
    print('Strip checker not running')
    sys.exit()

parser = argparse.ArgumentParser(
    description='Tells the strip checker to stop watching an ally',
    epilog="APIs for the win"
)

parser.add_argument('-u', '--username',
                    help='Username of the ally to stop watching FLs of', nargs=argparse.REMAINDER, type=int, required=True)

args = parser.parse_args()
u = [str(x) for x in args.username]

with open('data/stop_fls.json', 'w', encoding='utf-8') as fp:
    json.dump(u, fp)

os.kill(PID, signal.SIGUSR1)
USERS = ', '.join(u)
print(f'Signaled strip checker to stop watching {USERS}.')
