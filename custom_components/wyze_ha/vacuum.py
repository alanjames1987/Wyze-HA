"""Wyze Robot Vacuum Wrapper."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.vacuum import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_CLEANING,
    STATE_RETURNING,
    STATE_DOCKED,
    STATE_ERROR,
    SUPPORT_BATTERY,
    SUPPORT_FAN_SPEED,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_STOP,
    StateVacuumEntity,
)

from homeassistant.helpers.entity import DeviceInfo

from wyze_sdk import Client
from wyze_sdk.models.devices.vacuums import VacuumSuctionLevel, VacuumMode

from .const import _LOGGER, DOMAIN, CONF_CLIENT

SUPPORT_WYZE_ROBOT_VACUUM = (
    SUPPORT_BATTERY
    | SUPPORT_FAN_SPEED
    | SUPPORT_PAUSE
    | SUPPORT_RETURN_HOME
    | SUPPORT_START
    | SUPPORT_STATE
    | SUPPORT_STATUS
    | SUPPORT_STOP
)

OPERATING_STATE_MAP = {
    VacuumMode.IDLE: STATE_IDLE,
    VacuumMode.PAUSE: STATE_PAUSED,
    VacuumMode.SWEEPING: STATE_CLEANING,
    VacuumMode.ON_WAY_CHARGE: STATE_RETURNING,
    VacuumMode.FULL_FINISH_SWEEPING_ON_WAY_CHARGE: STATE_RETURNING,
    VacuumMode.BREAK_POINT: STATE_ERROR,
}

FAN_SPEEDS_MAP = {
    "Quiet": VacuumSuctionLevel.QUIET,
    "Standard": VacuumSuctionLevel.STANDARD,
    "Strong": VacuumSuctionLevel.STRONG,
}

SCAN_INTERVAL = timedelta(seconds=(60 * 5))


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Wyze vacuum cleaner."""

    client: Client = hass.data[DOMAIN][config_entry.entry_id][CONF_CLIENT]

    def get_vacuums():
        vacuums = []
        for v in client.vacuums.list():
            vacuum = client.vacuums.info(device_mac=v.mac)
            vacuums.append(WyzeVacuumEntity(hass, client, vacuum))
        return vacuums

    vacuums = await hass.async_add_executor_job(get_vacuums)

    async_add_entities(vacuums)


class WyzeVacuumEntity(StateVacuumEntity):
    """Wyze vacuum entity."""

    def __init__(self, hass, client, vacuum):
        """Create a new WyzeVacuumEntity."""
        self._hass = hass
        self._client = client
        self._vacuum = vacuum
        self._mac = (self._vacuum.product.model + "_" + self._vacuum.mac).upper()
        self._mode = STATE_DOCKED

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._vacuum.nickname,
            "manufacturer": "WyzeLabs",
            "model": self._vacuum.product.model,
            "sw_version": self._vacuum.firmware_version,
        }

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_WYZE_ROBOT_VACUUM

    @property
    def extra_state_attributes(self) -> dict:
        """Return a dictionary of device state attributes specific to sharkiq."""
        data = {
            "IP Address": self._vacuum.ip,
            "SSID": self._vacuum.ssid,
            "Firmware Version": self._vacuum.firmware_version,
            "Hardware Version": self._vacuum.hardware_version,
            "MAC": self._mac,
        }
        return data

    @property
    def unique_id(self) -> str:
        """Return the unique id of the vacuum cleaner."""
        return self._mac

    @property
    def name(self) -> str:
        """Device name."""
        return self._vacuum.nickname

    @property
    def status(self):
        """Return the status of the vacuum cleaner."""
        return self._mode

    @property
    def state(self):
        """Get the current vacuum state."""
        return self._mode

    @property
    def battery_level(self):
        """Get the current battery level."""
        return self._vacuum.voltage

    @property
    def fan_speed(self) -> str:
        """Return the current fan speed."""
        for k, val in FAN_SPEEDS_MAP.items():
            if val == self._vacuum.clean_level:
                fan_speed = k
                break
        return fan_speed

    @property
    def fan_speed_list(self):
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(FAN_SPEEDS_MAP)

    def start(self):
        """Start the device."""

        self._client.vacuums.clean(
            device_mac=self._mac,
            device_model=self._vacuum.product.model,
        )

        self._mode = STATE_CLEANING

        self.update()

    def pause(self):
        """Pause the cleaning task."""

        self._client.vacuums.pause(
            device_mac=self._mac,
            device_model=self._vacuum.product.model,
        )

        self._mode = STATE_PAUSED

        self.update()

    def stop(self):
        """Stop the cleaning task."""

        self._client.vacuums.pause(
            device_mac=self._mac,
            device_model=self._vacuum.product.model,
        )

        self._mode = STATE_STOP

        self.update()

    def return_to_base(self, **kwargs):
        """Have the device return to base."""

        self._client.vacuums.dock(
            device_mac=self._mac,
            device_model=self._vacuum.product.model,
        )

        self._mode = STATE_RETURNING

        self.update()

    def clean_spot(self, **kwargs):
        """Clean a spot. Not yet implemented."""
        raise NotImplementedError()

    def set_fan_speed(self, fan_speed: str, **kwargs):
        """Set the fan speed."""

        self._client.vacuums.set_suction_level(
            device_mac=self._mac,
            device_model=self._vacuum.product.model,
            suction_level=FAN_SPEEDS_MAP[fan_speed],
        )

        self.update()

    def update(self):
        """This function updates the entity."""

        self._vacuum = self._client.vacuums.info(device_mac=self._mac)

        if self._vacuum.mode in [VacuumMode.SWEEPING]:
            self._mode = STATE_CLEANING
        elif self._vacuum.mode in [VacuumMode.IDLE, VacuumMode.BREAK_POINT]:
            self._mode = STATE_DOCKED
        elif self._vacuum.mode in [VacuumMode.ON_WAY_CHARGE, VacuumMode.FULL_FINISH_SWEEPING_ON_WAY_CHARGE]:
            self._mode = STATE_RETURNING
        elif self._vacuum.mode in [VacuumMode.PAUSE]:
            self._mode = STATE_PAUSED
        else:
            self._mode = STATE_ERROR