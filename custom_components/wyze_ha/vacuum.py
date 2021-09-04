"""Wyze Robot Vacuum Wrapper."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.vacuum import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_CLEANING,
    STATE_RETURNING,
    STATE_ERROR,
    SUPPORT_BATTERY,
    SUPPORT_FAN_SPEED,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
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
        vacuums_devices = []
        vacuums_list = client.vacuums.list()
        for v in vacuums_list:
            vacuum = client.vacuums.info(device_mac=v.mac)
            vacuums_devices.append(vacuum)
        return vacuums_devices

    vacuums = await hass.async_add_executor_job(get_vacuums)

    async_add_entities([WyzeVacuumEntity(hass, client, vacuum) for vacuum in vacuums])


class WyzeVacuumEntity(StateVacuumEntity):
    """Wyze vacuum entity."""

    def __init__(self, hass, client, vacuum):
        """Create a new WyzeVacuumEntity."""
        self._hass = hass
        self._client = client
        self._vacuum = vacuum
        self._mac = (self._vacuum.product.model + "_" + self._vacuum.mac).upper()

    @property
    def is_online(self) -> bool:
        """Tell us if the device is online."""
        return self._vacuum.is_online

    @property
    def name(self) -> str:
        """Device name."""
        return self._vacuum.nickname

    @property
    def serial_number(self) -> str:
        """Vacuum API serial number (DSN)."""
        return self._vacuum.ssid

    @property
    def model(self) -> str:
        """Vacuum model number."""
        return self._vacuum.product.model

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._vacuum.nickname,
            "manufacturer": "WyzeLabs",
            "model": self._vacuum.product.model,
            "sw_version": self._vacuum.firmware_version,
            "hw_version": self._vacuum.hardware_version,
        }

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_WYZE_ROBOT_VACUUM

    @property
    def is_docked(self) -> bool | None:
        """Is vacuum docked."""
        return self._vacuum.mode == ""

    @property
    def operating_mode(self) -> str | None:
        """Operating mode.."""
        return str(self._vacuum.clean_level)

    @property
    def state(self):
        """Get the current vacuum state."""
        return OPERATING_STATE_MAP.get(self._vacuum.mode)

    @property
    def unique_id(self) -> str:
        """Return the unique id of the vacuum cleaner."""
        return self._mac

    @property
    def available(self) -> bool:
        """Determine if the sensor is available based on API results."""
        return self._vacuum.is_online

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

    @property
    def rssi(self) -> int | None:
        """Get the WiFi RSSI."""
        return self._vacuum.rssi

    @property
    def ssid(self) -> int | None:
        """Get the WiFi SSID."""
        return self._vacuum.ssid

    @property
    def ip(self) -> int | None:
        """Get the WiFi IP."""
        return self._vacuum.ip

    def clean_spot(self, **kwargs):
        """Clean a spot. Not yet implemented."""
        raise NotImplementedError()

    async def async_start(self):
        """Start the device."""

        def start():
            self._client.vacuums.clean(
                device_mac=self._mac,
                device_model=self._vacuum.product.model,
            )

        await self._hass.async_add_executor_job(start)

        await self.async_update()

    async def async_pause(self):
        """Pause the cleaning task."""

        def pause():
            self._client.vacuums.pause(
                device_mac=self._mac,
                device_model=self._vacuum.product.model,
            )

        await self._hass.async_add_executor_job(pause)

        await self.async_update()

    async def async_return_to_base(self, **kwargs):
        """Have the device return to base."""

        def dock():
            self._client.vacuums.dock(
                device_mac=self._mac,
                device_model=self._vacuum.product.model,
            )

        await self._hass.async_add_executor_job(dock)

        await self.async_update()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs):
        """Set the fan speed."""

        def set_fan_speed():
            self._client.vacuums.set_suction_level(
                device_mac=self._mac,
                device_model=self._vacuum.product.model,
                suction_level=FAN_SPEEDS_MAP[fan_speed],
            )

        await self._hass.async_add_executor_job(set_fan_speed)

        await self.async_update()

    async def async_update(self):
        """This function updates the entity."""

        def update():
            return self._client.vacuums.info(device_mac=self._mac)

        self._vacuum = await self._hass.async_add_executor_job(update)
