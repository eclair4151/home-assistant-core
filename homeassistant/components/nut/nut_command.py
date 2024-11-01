"""Defines the NutCommand class for representing NUT commands and their parameters."""

from dataclasses import dataclass


@dataclass
class NutParameter:
    """Class for representing NUT command parameters."""

    name: str
    type: type  # int, str, or None


@dataclass
class NutCommand:
    """Class for representing NUT commands."""

    command: str
    parameter: NutParameter | None = None
