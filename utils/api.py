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

"""Module for dealing with the login API"""

import sys
import logging
import time
import requests

from utils.utils import Row


class UsernameNotFound(Exception):
    """Error class when usernames are not found."""


class CantGetToken(Exception):
    """Error class for not getting token back from API"""


class API:
    """Class to handle PIMD login API"""

    def __init__(self, data: Row, database, proxy, number=0) -> None:

        self.data = data
        self.exception_counter = 0
        self.db = database
        self.proxy = proxy
        self.logger = logging.getLogger(f'Login API:{number}')

    def get_profile(self, profile_name, token=None):
        """Gets the profile data by username"""
        url = "https://api.partyinmydorm.com/game/user/get_profile_by_username/"

        if token:
            t = token
        else:
            t = self.data.access_token
        self.logger.debug('Fetching with name: %s', profile_name)
        r = requests.post(url, data={"profile_username": profile_name}, timeout=400, headers={
            "Authorization": f"Bearer {t}", "user-agent": "pimddroid/526"},
            proxies=self.proxy
        )

        res = r.json()

        ex = res.get('exception')
        if not ex:
            return res

        if "Session expired" in ex:
            if self.exception_counter > 3:
                self.logger.error(
                    'Failed to fetch new valid access token 3 times. Exiting.')
                self.logger.error(ex)

                sys.exit(3)

            self.exception_counter += 1
            self.logger.error(
                '%d: Session expired. Fetching new token and retrying...', self.exception_counter)
            new_token = self.update_access_token()
            time.sleep(10)
            return self.get_profile(profile_name, new_token)

        if "Username doesn't exist" in ex:
            raise UsernameNotFound

        self.logger.error("Unknown error in getting with name %s: %s",
                          profile_name, res)
        sys.exit(4)

    def get_profile_by_id(self, profile_id, token=None):
        """Gets the profile data by ID"""
        url = "https://api.partyinmydorm.com/game/user/get_profile/"

        if token:
            t = token
        else:
            t = self.data.access_token

        self.logger.debug('Fetching with ID: %s', profile_id)

        r = requests.post(url, data={"profile_user_id": profile_id}, timeout=400, headers={
            "Authorization": f"Bearer {t}", "user-agent": "pimddroid/526"}, proxies=self.proxy)

        res = r.json()

        ex = res.get('exception')

        if not ex:
            return res

        if "Session expired" in ex:
            if self.exception_counter > 3:
                self.logger.error(
                    'Failed to fetch new valid access token 3 times. Exiting.')
                self.logger.error(ex)
                sys.exit(3)

            self.exception_counter += 1
            self.logger.error(
                '%d: Session expired. Fetching new token and retrying...', self.exception_counter)
            print(ex)

            new_token = self.update_access_token()
            time.sleep(10)
            return self.get_profile_by_id(profile_id, new_token)

        elif "Username doesn't exist" in ex:
            self.logger.warning(ex)
            sys.exit(6)

        self.logger.error("Unknown error in getting with ID %s: %s",
                          profile_id, res)
        sys.exit(4)

    def update_access_token(self):
        """Tries to update the access token"""
        new_token = self.get_access_token()
        self.db.execute("UPDATE tokens SET access_token = ? WHERE refresh_token = ?",
                        (new_token, self.data.refresh_token))
        self.db.commit()
        return new_token

    def get_access_token(self, resp=False):
        """Fetchs new access token"""
        url = "https://api.partyinmydorm.com/game/login/oauth/"
        payload = {
            "channel_id": "16",
            "client_id": "ata.squid.pimd",
            "client_version": "534",
            "refresh_token": self.data.refresh_token,
            "scope": "[\"all\"]",
            "version": "3320",
            "client_secret": "n0ts0s3cr3t",
            "grant_type": "refresh_token",
            "client_information": self.data.client_info
        }
        r = requests.post(url, payload, timeout=400,
                          proxies=self.proxy)
        t = r.json()
        if "access_token" not in t:
            print(t)
            raise CantGetToken
        if resp:
            rsp = t
            return [rsp, rsp['access_token']]

        return t['access_token']
