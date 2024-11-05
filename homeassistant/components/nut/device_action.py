"""Provides device actions for Network UPS Tools (NUT)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import (
    InvalidDeviceAutomationConfig,
    async_validate_entity_schema,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import NutRuntimeData
from .const import (
    DOMAIN,
    INTEGRATION_SUPPORTED_COMMANDS,
    INTEGRATION_SUPPORTED_COMMANDS_DICT,
)
from .nut_command import NutParameter

ACTION_TYPES = {cmd.command.replace(".", "_") for cmd in INTEGRATION_SUPPORTED_COMMANDS}


async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate the device action configuration."""
    schema = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        }
    )

    # Check if this command support a param, and if so, add the optional param to the schema
    device_action_name = config[CONF_TYPE]
    param = get_parameter_for_command(device_action_name)
    if param is not None:
        schema = schema.extend({vol.Optional(param.name): param.type})

    return async_validate_entity_schema(hass, config, schema)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Network UPS Tools (NUT) devices."""
    if (runtime_data := _get_runtime_data_from_device_id(hass, device_id)) is None:
        return []
    base_action = {
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }
    return [
        {CONF_TYPE: _get_device_action_name(command_name)} | base_action
        for command_name in runtime_data.user_available_commands
    ]


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    device_action_name: str = config[CONF_TYPE]
    command_name = _get_command_name(device_action_name)
    device_id: str = config[CONF_DEVICE_ID]
    param_value = None
    runtime_data = _get_runtime_data_from_device_id(hass, device_id)
    if not runtime_data:
        raise InvalidDeviceAutomationConfig(
            f"Unable to find a NUT device with id {device_id}"
        )

    param = get_parameter_for_command(device_action_name)
    if param and (param_val := config.get(param.name)):
        param_value = str(param_val)
    await runtime_data.data.async_run_command(command_name, param_value)


def _get_device_action_name(command_name: str) -> str:
    return command_name.replace(".", "_")


def _get_command_name(device_action_name: str) -> str:
    return device_action_name.replace("_", ".")


def _get_runtime_data_from_device_id(
    hass: HomeAssistant, device_id: str
) -> NutRuntimeData | None:
    device_registry = dr.async_get(hass)
    if (device := device_registry.async_get(device_id)) is None:
        return None
    entry = hass.config_entries.async_get_entry(
        next(entry_id for entry_id in device.config_entries)
    )
    assert entry and isinstance(entry.runtime_data, NutRuntimeData)
    return entry.runtime_data


async def async_get_action_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """Get the capabilities of a device action."""
    device_action_name = config[CONF_TYPE]
    if param := get_parameter_for_command(device_action_name):
        return {"extra_fields": vol.Schema({vol.Optional(param.name): param.type})}

    return {}


def get_parameter_for_command(device_action_name: str) -> NutParameter | None:
    """Get the parameter object for a command if one exists, otherwise return None."""
    command_name = _get_command_name(device_action_name)
    if (device_action := INTEGRATION_SUPPORTED_COMMANDS_DICT.get(command_name)) and (
        param := device_action.parameter
    ):
        return param
    return None
