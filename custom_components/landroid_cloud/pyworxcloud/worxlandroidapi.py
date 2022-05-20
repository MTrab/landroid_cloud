import logging
import time

API_BASE = "https://{}/api/v2"

_LOGGER = logging.getLogger(__name__)

# Valid clouds for this module
clouds = {
    "worx": {
        "url": "api.worxlandroid.com",
        "key": "725f542f5d2c4b6a5145722a2a6a5b736e764f6e725b462e4568764d4b58755f6a767b2b76526457",
    },
    "kress": {
        "url": "api.kress-robotik.com",
        "key": "5a1c6f60645658795b78416f747d7a591a494a5c6a1c4d571d194a6b595f5a7f7d7b5656771e1c5f",
    },
    "landxcape": {
        "url": "api.landxcape-services.com",
        "key": "071916003330192318141c080b10131a056115181634352016310817031c0b25391c1a176a0a0102",
    },
}


class WorxLandroidAPI:
    """Worx Cloud API definition."""

    def __init__(self) -> None:
        """Initialize new instance of API broker."""
        self.cloud = clouds["worx"]
        self._token_type = "app"
        self.username = None
        self.password = None
        self.type = None
        self._tokenrefresh = 0

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

        import re

        step_one = re.findall(r".{1,2}", seed_token)
        step_two = list(map((lambda hex: int(hex, 16)), step_one))

        import functools
        import operator

        step_three = list(
            map(
                (
                    lambda foo: functools.reduce(
                        (lambda x, y: operator.xor(x, y)), text_to_char, foo
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
        import json
        import uuid

        self.uuid = str(uuid.uuid1())
        self.cloud = clouds[self.type]
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

        callData = self._call("/oauth/token", payload, checktoken=False)

        return callData

    def get_profile(self):
        """Get user profile."""
        callData = self._call("/users/me")
        self._data = callData
        return callData

    def get_cert(self):
        """Get user certificate."""
        callData = self._call("/users/certificate")
        self._data = callData
        return callData

    def get_products(self):
        """Get devices associated with this user."""
        callData = self._call("/product-items")
        self._data = callData
        return callData

    def get_status(self, serial):
        """Get device status."""
        callStr = "/product-items/{}/status".format(serial)
        callData = self._call(callStr)
        return callData

    def _call(self, path: str, payload: str = None, checktoken: bool = True):
        """Do the actual call to the device."""
        import json
        import requests

        # Check if token needs refreshing
        now = int(time.time())  # Current time in unix timestamp format
        if checktoken and ((self._tokenrefresh + 3000) < now):
            _LOGGER.debug("Refreshing token for %s", self.username)
            try:
                auth_data = self.auth()

                if 'return_code' in auth_data:
                    return

                self.set_token(auth_data["access_token"], now)
                self.set_token_type(auth_data["token_type"])
            except:
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
        except:
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
