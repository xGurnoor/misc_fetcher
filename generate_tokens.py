"""Module for generating more tokens"""

import time
import random
import uuid
import string
import json
from prettytable import PrettyTable
import requests

from util.utils import ProxyManager


with open("proxylist.txt", 'r', encoding='utf-8') as fp:
    proxy_manager = ProxyManager(fp)

WORD_FILE = "/usr/share/dict/words"
WORDS = open(WORD_FILE, 'r', encoding='utf-8').read().splitlines()


def sleep(num, why):
    """helper function to add variablity and log sleeping"""
    num = random.uniform(num, num+0.5)

    print(f"for {num} seconds for {why}")
    time.sleep(num)


tb = PrettyTable(['token', 'advertising ID', 'android ID', 'app set ID'])


def run():
    """main function"""
    proxy = proxy_manager.get()

    r = requests.post("https://api.partyinmydorm.com/game/login/oauth/", data={
        "channel_id": "16",
        "client_id": "ata.squid.pimd",
        "client_version": "534",
        "scope": '["all"]',
        "version": "3282",
        "client_secret": "n0ts0s3cr3t",
        "grant_type": "urn:athinkingape:temporary:v1",
    }, timeout=10, proxies=proxy, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'})

    refresh_token = r.json()['refresh_token']

    android_advertising = str(uuid.uuid4())
    app_set_id = str(uuid.uuid4())
    android_id = ''.join(random.choices(
        string.ascii_letters + string.digits, k=16))
    payload = {
        "channel_id": "16",
        "client_id": "ata.squid.pimd",
        "client_version": "534",
        "refresh_token": refresh_token,
        "scope": '["all"]',
        "client_secret": "n0ts0s3cr3t",
        "client_information": json.dumps({
            # pylint: disable=line-too-long
            "android_advertising": android_advertising, "android_id": android_id,
            "app_set_id": app_set_id, "bundle_id": "ata.squid.pimd", "country": "US", "dpi": "hdpi", "ether_map": {"1": "02:00:00:00:00:00"},
            "hardware_version": "OnePlus|NE211", "language": "en", "limit_ad_tracking": False, "locale": "en_US",
            "os_build": "Build/SKQ1.220617.001", "os_name": "Android", "os_version": "9", "referrer": "utm_source=google-play&utm_medium=organic",
            "screen_size": "screen_xlarge",
            "user_agent": "Mozilla/5.0 (Linux; Android 9; NE2211 Build/SKQ1.220617.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Safari/537.36",
            "version_name": "7.06"
        })
    }

    def track_tutorial(key):
        "posts to track tutorial"
        requests.post("https://api.partyinmydorm.com/game/metrics/tutorial/track_tutorial/", data={
            "channel_id": "16",
            "client_id": "ata.squid.pimd",
            "refresh_token": refresh_token,
            "key": key,
            "client_secret": "n0ts0s3cr3t",
            "grant_type": "refresh_token",
            "client_information": payload["client_information"]
        }, timeout=10, proxies=proxy)

    track_tutorial("tutorial2-a_1-choose_avatar_screen")
    requests.post("https://api.partyinmydorm.com/game/registration/get_tutorial_avatars/", {
        "max_avatars": 12,
        "start_avatar_variation": 0
    }, timeout=10, proxies=proxy)

    sleep(2, "chosing avatar")
    track_tutorial("tutorial2-a_2-choose_username_screen")

    sleep(3, "choosing name")

    body = payload.copy()
    body.update(package_name="ata.squid.pimd", username=random.choice(WORDS),
                scope="[]", version_2_return=True)
    r = requests.post("https://api.partyinmydorm.com/game/registration/oauth/create_game_user/",
                      data=body, timeout=10, proxies=proxy)
    s = r.json()
    if s.get('exception'):
        print(s)
        exit()
    sleep(0.2, "delay in sending name pick success")
    track_tutorial("tutorial2-a_2-name_pick_success")

    sleep(2*60, "finishing questline")
    track_tutorial("tutorial2-a_15-questline_finished")

    sleep(1, "getting quest result")
    track_tutorial("tutorial2-a_16-quest_result")

    sleep(60, "loading into the game")
    hds = payload.copy()
    hds.update({
        "package_name": "ata.squid.pimd",
        "poster_item_id": "12306",
        "building_id1": "38",
        "building_id2": "34",
        "building_id3": "34",
        "scope": "[]",
        "uncovered_land1": "1",
        "uncovered_land2": "2",
        "uncovered_land3": "4",
        "new_user_experience": True,
        "item_id": "133886",
        "version": "3320",
    })
    r = requests.post(
        "https://api.partyinmydorm.com/game/registration/oauth/complete_tutorial/",
        hds, timeout=10, proxies=proxy, headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
    v = r.json()
    if v.get('exception'):
        print(v)
        exit()
    sleep(5, "final complete")
    track_tutorial("tutorial2-a_17-complete")
    row = [refresh_token, android_advertising, android_id, app_set_id]
    tb.add_row(row)
    return row


def get_payload(ad, a_id, a_sid):
    """returns client information"""
    payload = {
        "client_information": {
            "android_advertising": ad, "android_id": a_id,
            "app_set_id": a_sid, "bundle_id": "ata.squid.pimd", "country": "US", "dpi": "hdpi", "ether_map": {"1": "02:00:00:00:00:00"},
            "hardware_version": "OnePlus|NE211", "language": "en", "limit_ad_tracking": False, "locale": "en_US",
            "os_build": "Build/SKQ1.220617.001", "os_name": "Android", "os_version": "9", "referrer": "utm_source=google-play&utm_medium=organic",
            "screen_size": "screen_xlarge",
            "user_agent": "Mozilla/5.0 (Linux; Android 9; NE2211 Build/SKQ1.220617.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Safari/537.36",
            "version_name": "7.06"
        }
    }
    return payload


tokens = []

for x in range(7):
    try:
        res = run()

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        break
    refresh = res[0]
    client_info = get_payload(res[1], res[2], res[3])
    client_info = json.dumps(client_info)
    tokens.append(f"{refresh}:SPLIT:{client_info}")

with open('tokens.txt', 'w', encoding='utf-8') as fp:
    LI = "\n".join(tokens)
    fp.write(LI)
res = run()
print('\n\n')
print(tb)
