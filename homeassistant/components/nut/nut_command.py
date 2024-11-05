"""Defines the NutCommand class for representing NUT commands and their parameters."""

from dataclasses import dataclass

import voluptuous as vol


@dataclass
class NutParameter:
    """Class for representing NUT command parameters with a name and type."""

    name: str
    type: vol.All | vol.Any


@dataclass
class NutCommand:
    """Class for representing NUT commands."""

    command: str
    parameter: NutParameter | None = None
