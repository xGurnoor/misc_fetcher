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
import logging
import sqlite3
import signal

# pylint: disable=wrong-import-order
from discord import Embed, SyncWebhook, Color
from collections import namedtuple
from setproctitle import setproctitle

from util.api import API
from util.utils import convert_to_human, ProxyManager, Row

# change process name to accomodate using pidof to get pid of this process
setproctitle('stripper')

# logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(
    description='Watches allies for strips',
    epilog="APIs for the win"
)

if not os.path.exists('data'):
    os.mkdir('data')

if not os.path.exists('data/tut_list.json'):
    with open('data/tut_list.json', 'w', encoding='utf-8') as fp:
        fp.write('{}')


with open('tokens.json', 'r', encoding='utf-8') as fp:
    config = json.load(fp)

with open('proxylist.txt', 'r', encoding='utf-8') as fp:
    proxy_manager = ProxyManager(fp)


# globals

# ACCESS_TOKEN = tokens['access_token']
# REFERSH_TOKEN = tokens['refresh_token']

WEBHOOK_URL = config['discord_webhook_url']


STOP = False
WATCH_LIST = []
BATTLE_STATS = {}
ALLIES = []
STOP_WATCHING = []

lock = threading.Lock()

conn = sqlite3.connect('data/stats.db')
conn.row_factory = Row

if not os.path.exists('data'):
    os.mkdir('data')

BattleStats = namedtuple('BattleStats', ['fl', 'dl', 'pl', 'el'])

def handle_signal(_sig, _frame):
    """Signal handler function to handle SIGUSR1 signal sent to tell program to check a new addition"""

    with open('data/stop_fls.json', 'r', encoding='utf-8') as file:
        t = json.load(file)
    t = [str(x) for x in t]
    lock.acquire(blocking=True, timeout=15)
    STOP_WATCHING.extend(t)
    lock.release()

    os.unlink('data/stop_fls.json')

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def setup_db():
    """Setups the SQLite database before use"""
    # pylint: disable=line-too-long
    conn.execute(
        "CREATE TABLE IF NOT EXISTS allies(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, profile_id BIGINT)")
    conn.execute('CREATE TABLE IF NOT EXISTS tokens(id INTEGER PRIMARY KEY AUTOINCREMENT, access_token TEXT, refresh_token TEXT, client_info TEXT)')
    conn.execute(
        'CREATE TABLE IF NOT EXISTS tutors(id INTEGER PRIMARY KEY AUTOINCREMENT, tutor_username TEXT, tutor_id TEXT, uid BIGINT)')
    conn.commit()

    cur = conn.cursor()
    cur.execute('SELECT * FROM ALLIES')
    res = cur.fetchall()
    if not res:
        print('Ally list is empty, exiting.')
        sys.exit(4)
    ALLIES.extend(res)


def update_user_id(db, uid, username):
    """Updates user ID in the database"""
    cur = db.cursor()
    cur.execute("UPDATE allies SET profile_id=? WHERE username=?",
                (uid, username))
    db.commit()
    cur.close()


def update_username(db, name, uid):
    """Update username in the database"""
    cur = db.cursor()
    cur.execute(
        'UPDATE allies SET username = ? WHERE profile_id = ?', (name, uid))
    db.commit()
    cur.close()


def alert_mame_change(old, new, count=1):
    """Alerts the server about a new name change"""
    wh = SyncWebhook.from_url(WEBHOOK_URL)
    wb_user = f"Strip checking slave #{count}"
    wh.send(f"Ally changed name from `{old}` to `{new}`.", username=wb_user)


def check_tuts(api, allies, num):
    """Checks the tutors for strips for all allies."""

    db = sqlite3.connect('data/stats.db')
    db.row_factory = Row
    api.db = db

    logger = logging.getLogger(f'Stripper:{num}')
    for ally in allies:
        username = ally.get('username')
        uid = ally.get('profile_id')

        logger.info('Checking ally %s (%s)', username, uid)

        if not uid:
            profile = api.get_profile(username)

            if not profile:
                logger.error('No ID present and username doesn\'t exist')
                sys.exit(5)

            uid = int(profile.get('user_id'))
            update_user_id(db, uid, username)

        else:
            logger.info('getting profile %d', uid)
            profile = api.get_profile_by_id(uid)
            if not profile['username'] == username:
                alert_mame_change(username, profile['username'])

                ally.username = profile['username']
                username = profile['username']
                update_username(db, profile['username'], uid)

        tmp_stats = (profile.get('fights_lost'), profile.get('steals_lost'),
                     profile.get('assassinates_lost'), profile.get('scouts_lost'))
        battle_sts = BattleStats(*tmp_stats)

        tutors = []

        for x in profile.get('clan_members'):
            tut = {'user_id': x['user_id'], 'username': x['username']}
            tutors.append(tut)

        # print(f"IGN: {username}: \n", json.dumps(tutors, indent=2))
        cur = db.cursor()
        cur.execute('SELECT * FROM tutors WHERE owner = ?', (uid,))
        old_list = cur.fetchall()

        if not old_list:
            args = []
            for x in tutors:
                args.append((x['username'], x['user_id'], uid))
            cur.executemany(
                "INSERT INTO tutors(tutor_username, tutor_id, owner) VALUES (?, ?, ?)", args)
            db.commit()
            cur.close()
        else:

            temp1 = []
            for x in tutors:
                temp1.append(x['user_id'])

            temp2 = []
            for x in old_list:
                temp2.append(int(x['tutor_id']))

            missing = set(temp2).difference(temp1)
            added = set(temp1).difference(temp2)

            if missing or added:
                cur.execute('DELETE FROM tutors WHERE owner = ?', (uid,))
                db.commit()

                args = []
                for x in tutors:
                    args.append((x['username'], x['user_id'], uid))
                cur.executemany(
                    "INSERT INTO tutors(tutor_username, tutor_id, owner) VALUES (?, ?, ?)", args)

                db.commit()
                cur.close()

                if missing:

                    confirm_strip(api, missing, username, uid, battle_sts, num)

        time.sleep(3)


def confirm_strip(api, missing, username, uid, battle_sts, number):
    """Takes in missing tuts and checks who hired to confirm
      they were hired away not buried in the tut list"""

    missing_tut_list = []
    hired = 0
    logger = logging.getLogger(f'Strip Confirmer:{number}')
    for miss in missing:
        logger.info('Getting missing tutor with ID %s', miss)
        profile = api.get_profile_by_id(miss)

        hv = profile.get("value")
        hired += hv

        owner = profile.get('owner')

        if not owner or not owner['user_id'] == uid:
            owner = owner['username'] if owner else 'No one'
            missing_tut_list.append(
                [profile['username'], hv, owner])
        time.sleep(2)

    if not missing_tut_list:
        return

    alert_server(username, missing=missing_tut_list, total=hired, count=number)

    if not BATTLE_STATS.get(username):
        t = threading.Thread(target=watch_fls, args=(
            api, username, uid, battle_sts, number), daemon=True)

        t.start()


def watch_fls(api, username, uid, bsts, count):
    """Function ran in thread to repeatedly check if FLs are increasing."""
    uid = str(uid)
    if not BATTLE_STATS.get(uid):
        BATTLE_STATS[uid] = bsts
    unchanged = 0

    while True:

        time.sleep(10 * 60)

        if uid in STOP_WATCHING:

            lock.acquire(timeout=15)
            STOP_WATCHING.remove(uid)
            lock.release()

            alert_fls(username, uid, interrupted=True, count=count)

            return

        profile = api.get_profile_by_id(uid)

        fl = profile.get('fights_lost')
        dl = profile.get('steals_lost')
        pl = profile.get('assassinates_lost')
        el = profile.get('scouts_lost')

        new_bsts = BattleStats(fl, dl, pl, el)

        if not fl == bsts.fl or not dl == bsts.dl:

            alert_fls(username, uid, new_bsts, bsts, count=count)

            bsts = new_bsts
            unchanged = 0

        else:

            if unchanged >= 5:

                alert_fls(username, uid, stopping=True, count=count)

                del BATTLE_STATS[uid]
                break

            alert_fls(username, uid, nochange=True, count=count)
            unchanged += 1



def alert_fls(username, uid, new_stats=None, prev_stats=None, nochange=False, stopping=False, interrupted=False, count=1):
    """Alerts the server about any battle stats changes on potentianl strip"""
    wh = SyncWebhook.from_url(WEBHOOK_URL)
    wb_user = f"Strip checking slave #{count}"

    if nochange:
        return wh.send(f"No change in battle losses for `{username}`", username=wb_user)

    if stopping:
        return wh.send("No change in battle losses for"
                       f"`{username}` in 5 consecutive checks, stopped checking.", username=wb_user)
    if interrupted:
        return wh.send(f"Interrupted while watching {username} battle losses. Stopped watching.", username=wb_user)

    initial = BATTLE_STATS[uid]

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

    wh.send(content="<@&1273745059015036938>", embed=embed, username=wb_user)


def alert_server(person, missing=None, added=None, total=None, count=1):
    """Inform the server of someone missing a tutor in tutor list."""
    embed = Embed(title="Strip alert",
                  description=f"{person} was potentially stripped.", color=Color.blurple())
    if missing:

        missing_str = []

        for x in missing:
            missing_str.append(
                f"{x[0]}: ${convert_to_human(x[1])} Hired by: {x[2]}")

        missing_str.append(f'\n\nTotal stripped: ${convert_to_human(total)}')

        embed.add_field(name="Tutors missing",
                        value="\n".join(missing_str), inline=False)
    if added:

        added = [f"`{x}`" for x in added]
        embed.add_field(name="New tutors hired",
                        value=", ".join(added), inline=False)

    wh = SyncWebhook.from_url(WEBHOOK_URL)
    wb_user = f"Strip checking slave #{count}"

    wh.send(content="<@&1273744969978613772>", embed=embed, username=wb_user)


def update_allies():
    """Updates the local ally list after every check"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM allies")

    r = cur.fetchall()
    cur.close()

    ALLIES.clear()
    ALLIES.extend(r)


def start_tasks(chunked_ally_list):
    """Start threaded tasks to check allies"""
    # print(allies)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tokens')

    tokens = cursor.fetchall()
    cursor.close()
    logger = logging.getLogger('ThreadManager')

    index = -1
    count = 0
    for ally in chunked_ally_list:
        logger.info('Starting thread %d', count)
        index = index + 1 if index < (len(tokens) - 1) else 0

        token = tokens[index]
        proxy = proxy_manager.at(index)
        api = API(token, None, proxy=proxy,
                  proxy_manager=proxy_manager, number=count)
        t = threading.Thread(target=check_tuts, args=(
            api, ally, count), daemon=True)
        t.start()
        count += 1


if __name__ == "__main__":
    try:
        print('Starting tutor checker.')

        signal.signal(signal.SIGUSR1, handle_signal)
        setup_db()
    
        while not STOP:
            print('Checking tutors.')

            # update ally list incase new allies were added during checking
            update_allies()

            # chunk allies into 10 per set
            chunked_allies = list(chunks(ALLIES, 10))

            # start all the threads
            start_tasks(chunked_allies)

            # sleep for 10 minutes, pin time is 10 miuntes so most strips should still be caught early
            time.sleep(10 * 60)

    except KeyboardInterrupt:

        STOP = True
        print('Exiting...')
        sys.exit(0)
