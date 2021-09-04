from __future__ import annotations

from datetime import timedelta

import logging

_LOGGER = logging.getLogger(__package__)

API_TIMEOUT = 20
PLATFORMS = ["vacuum"]
DOMAIN = "wyze_ha"
UPDATE_INTERVAL = timedelta(seconds=60)
CONF_CLIENT = "wyze_sdk"
