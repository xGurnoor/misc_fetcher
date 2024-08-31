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
