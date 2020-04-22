#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
"""Build configuration abstraction layer."""
from typing import Any, Callable, Dict, List, Set, Optional
from typing_extensions import TypedDict

from mbed_targets import get_target_by_board_type, Target

from mbed_build._internal.find_files import find_files, filter_files, LabelFilter
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
    # TODO (extra_labels vs labels)
    labels: Set[str]
    features: Set[str]
    macros: Set[str]


def build_config_from_layers(layers: List[ConfigLayer], base_config: Optional[Config] = None) -> Config:
    """Create configuration from layers."""
    # TODO: ensure config is not mutated
    if not base_config:
        base_config = _empty_config()
    for layer in layers:
        layer.apply(base_config)
    return base_config


def build_config(mbed_program_directory, board_type) -> Config:
    """Assemble build configuration.

    Configuration is assembled from:
    - targets.json file (pre-parsed in `mbed-targets`)
    - mbed_lib.json files
    - mbed_app.json file

    All the source files which contain build configuration affect labelling filters, which are used
    to find mbed_lib.json files. Whenever those filters change, we need to re-assemble the configuration
    taking into account files, which might've previously been excluded.
    An example of such behaviour would be an `mbed_lib.json` file which adds a "feature" to configuration.
    Since "features" are one of the ingredients which determine directory filtering rules, adding one during
    configuration assembly pass changes file filtering rules.
    """
    target = get_target_by_board_type(board_type, mbed_program_directory)
    config = _empty_config()
    config["settings"] = target.config
    config["features"] = target.features

    all_mbed_lib_files = find_files("mbed_lib.json", mbed_program_directory)

    old_filters = []
    filters = _build_filters(config)

    while old_filters != filters:
        config_specific_mbed_lib_files = filter_files(all_mbed_lib_files, filters)
        mbed_lib_sources = [ConfigSource.from_mbed_lib(file) for file in config_specific_mbed_lib_files]
        mbed_lib_layers = [
            ConfigLayer.from_config_source(source, list(config["target"]["labels"])) for source in mbed_lib_sources
        ]

        config = build_config_from_layers(mbed_lib_layers, config)

        old_filters = filters
        filters = _build_filters(config)
    return config


def _build_filters(config: Config) -> List[Callable]:
    return [
        LabelFilter("TARGET", config["target"]["labels"]),
        LabelFilter("FEATURE", config["target"]["features"]),
        LabelFilter("COMPONENT", config["target"]["components"]),
    ]


def _empty_config() -> Config:
    return Config(
        settings={},
        target={"components": set(), "device_has": set(), "labels": set(), "features": set(), "macros": set()},
    )
