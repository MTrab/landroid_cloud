"""API implementation"""
from __future__ import annotations

import logging
import time
import re
import functools
import operator
import json
import uuid
import requests

from .clouds import CLOUDS
from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class LandroidAPI:
    """Worx Cloud API definition."""

    def __init__(self) -> None:
        """Initialize new instance of API broker."""
        self.cloud = CLOUDS["worx"]
        self._token_type = "app"
        self.username = None
        self.password = None
        self.type = None
        self._token = None
        self._tokenrefresh = 0
        self.uuid = None
        self._api_host = None
        self._data = None

    def set_token(self, token: str, now: int = -1) -> None:
        """Set the token used for communication."""
        if now == -1:
            now = int(time.time())

        self._tokenrefresh = now
        self._token = token

    def set_token_type(self, token_type: str) -> None:
        """Set type of token."""
        self._token_type = token_type

    def _generate_identify_token(self, seed_token: str) -> str:
        """Generate identify token."""
        text_to_char = [ord(c) for c in self.cloud["url"]]

        step_one = re.findall(r".{1,2}", seed_token)
        step_two = list(map((lambda hex: int(hex, 16)), step_one))

        step_three = list(
            map(
                (
                    lambda foo: functools.reduce(
                        (lambda x, y: operator.xor(x, y)), text_to_char, foo # pylint: disable=unnecessary-lambda
                    )
                ),
                step_two,
            )
        )
        step_four = list(map(chr, step_three))

        final = "".join(step_four)
        return final

    def _get_headers(self) -> dict:
        """Create header object for communication packets."""
        header_data = {}
        header_data["Content-Type"] = "application/json"
        header_data["Authorization"] = self._token_type + " " + self._token

        return header_data

    def auth(self):
        """Authenticate."""
        self.uuid = str(uuid.uuid1())
        self.cloud = CLOUDS[self.type]
        self._api_host = (API_BASE).format(self.cloud["url"])

        self._token = self._generate_identify_token(self.cloud["key"])

        payload_data = {}
        payload_data["username"] = self.username
        payload_data["password"] = self.password
        payload_data["grant_type"] = "password"
        payload_data["client_id"] = 1
        payload_data["type"] = "app"
        payload_data["client_secret"] = self._token
        payload_data["scope"] = "*"

        payload = json.dumps(payload_data)

        calldata = self._call("/oauth/token", payload, checktoken=False)

        return calldata

    def get_profile(self):
        """Get user profile."""
        calldata = self._call("/users/me")
        self._data = calldata
        return calldata

    def get_cert(self):
        """Get user certificate."""
        calldata = self._call("/users/certificate")
        self._data = calldata
        return calldata

    def get_products(self):
        """Get devices associated with this user."""
        calldata = self._call("/product-items")
        self._data = calldata
        return calldata

    def get_status(self, serial):
        """Get device status."""
        callstr = f"/product-items/{serial}/status"
        calldata = self._call(callstr)
        return calldata

    def _call(self, path: str, payload: str = None, checktoken: bool = True):
        """Do the actual call to the device."""
        # Check if token needs refreshing
        now = int(time.time())  # Current time in unix timestamp format
        if checktoken and ((self._tokenrefresh + 3000) < now):
            _LOGGER.debug("Refreshing token for %s", self.username)
            try:
                auth_data = self.auth()

                if "return_code" in auth_data:
                    return

                self.set_token(auth_data["access_token"], now)
                self.set_token_type(auth_data["token_type"])
            except: # pylint: disable=bare-except
                _LOGGER.debug("Error occured when refreshing token")

        try:
            if payload:
                req = requests.post(
                    self._api_host + path,
                    data=payload,
                    headers=self._get_headers(),
                    timeout=10,
                )
            else:
                req = requests.get(
                    self._api_host + path, headers=self._get_headers(), timeout=10
                )

            if not req.ok:
                response = {}
                response["return_code"] = req.status_code
                response["original_response"] = req.json()
                if req.status_code == 400:
                    response["error"] = "Bad request"
                    _LOGGER.error("Error: Bad request")
                elif req.status_code == 401:
                    response["error"] = "Unauthorized"
                    _LOGGER.error("Error: Unauthorized")
                elif req.status_code == 404:
                    response["error"] = "API endpoint doesn't exist"
                    _LOGGER.error("Error: API endpoint doesn't exist")
                elif req.status_code == 500:
                    response["error"] = "Internal server error"
                    _LOGGER.error("Error: Internal server error")
                elif req.status_code == 503:
                    response["error"] = "Service unavailable"
                    _LOGGER.error("Error: Service unavailable")
                else:
                    response["error"] = "Unknown error"
                    _LOGGER.error(
                        "Error: Return code %s was received - unknown error",
                        req.status_code,
                    )
                return json.dumps(response)
        except TimeoutError:
            response = {"error": "timeout"}
            _LOGGER.warning("Error: Timeout in communication with API service")
            return json.dumps(response)
        except: # pylint: disable=bare-except
            response = {"error": "unexpected error"}
            _LOGGER.warning(
                "Error: Unexpected error occured in communication with API service"
            )
            return json.dumps(response)

        return req.json()

    @property
    def data(self):
        """Return data for device."""
        return self._data
