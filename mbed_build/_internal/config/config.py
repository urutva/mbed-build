#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
"""Build configuration abstraction layer."""
from typing import Any, Callable, Dict, List, Set, Optional
from typing_extensions import TypedDict

from mbed_targets import get_target_by_board_type, Target

from mbed_build._internal.find_files import find_files, LabelFilter
from mbed_build._internal.config.config_layer import ConfigLayer
from mbed_build._internal.config.config_source import ConfigSource


class Config(TypedDict):
    """Represents a build configuration."""

    settings: Dict[str, "Setting"]
    target: "TargetOverrides"


class Setting(TypedDict):
    """Represents a config setting."""

    help: Optional[str]
    value: Any


class TargetOverrides(TypedDict):
    """Represents target cumulative overrides."""

    components: Set[str]
    device_has: Set[str]
    extra_labels: Set[str]
    features: Set[str]
    macros: Set[str]


def build_config_from_layers(layers: List[ConfigLayer]) -> Config:
    """Create configuration from layers."""
    config = _empty_config()
    for layer in layers:
        layer.apply(config)
    return config


def _apply_layers(config: Config, layers: List[ConfigLayer]) -> Config:
    # TODO: don't mutate
    for layer in layers:
        layer.apply(config)
    return config


def build_config(mbed_program_directory, board_type) -> Config:
    target = get_target_by_board_type(board_type, mbed_program_directory)
    base_layer = ConfigLayer.from_target_data(target)
    initial_config = _apply_layers(_empty_config(), [base_layer])

    all_mbed_lib_files = find_files("mbed_lib.json", mbed_program_directory)

    old_filters = []
    filters = _build_filters(initial_config)

    while old_filters != filters:
        config_specific_mbed_lib_files = filter_files(all_mbed_lib_files, filters)
        mbed_lib_sources = [ConfigSource.from_file(file) for file in target_specific_mbed_lib_files]
        mbed_lib_layers = [ConfigLayer.from_config_source(source, target.labels) for source in mbed_lib_sources]

        config = _apply_layers(initial_config, mbed_lib_layers)

        old_filters = filters
        filters = _build_filters(config)

    return config


def _build_config_from_target(target: Target) -> Config:
    config = _empty_config()
    config.settings = target.settings
    config.target["features"] = target.features
    return config


def _build_filters(config: Config) -> List[Callable]:
    return [
        LabelFilter("TARGET", config.labels),
        LabelFilter("FEATURE", config.features),
        LabelFilter("COMPONENT", config.components),
    ]


def _empty_config() -> Config:
    return Config(
        settings={},
        target={"components": set(), "device_has": set(), "extra_labels": set(), "features": set(), "macros": set()},
    )
