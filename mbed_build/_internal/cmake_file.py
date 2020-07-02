#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
"""Module in charge of CMake file generation."""
import pathlib

from typing import Iterable, Dict, Any

import jinja2

from mbed_targets import Target
from mbed_build._internal.context import BuildContext


TEMPLATES_DIRECTORY = pathlib.Path("_internal", "templates")
KEYS_TEMPLATE_NAME = "CMakeLists.tmpl"
FULL_TEMPLATE_NAME = "CMakeLists.txt.tmpl"
TOOLCHAIN_TEMPLATE_NAME = "toolchain.cmake.tmpl"


def generate_cmakelists_full_file(context: BuildContext) -> str:
    return _render_cmake_template(context.to_dict(), FULL_TEMPLATE_NAME)


def generate_cmake_toolchain_file(context: BuildContext) -> str:
    return _render_cmake_template(context.to_dict(), TOOLCHAIN_TEMPLATE_NAME)


def generate_cmakelists_keys_file(mbed_target: Target, toolchain_name: str) -> str:
    """Generate the top-level CMakeLists.txt file containing the correct definitions for a build.

    Args:
        mbed_target: the target the application is being built for
        program_path: the path to the local Mbed program
        toolchain_name: the toolchain to be used to build the application

    Returns:
        A string of rendered contents for the file.
    """
    context = {
        "target_labels": mbed_target.labels,
        "feature_labels": mbed_target.features,
        "component_labels": mbed_target.components,
        "toolchain_name": toolchain_name,
    }
    return _render_cmake_template(context, KEYS_TEMPLATE_NAME)


def _render_cmake_template(context: Dict[str, Any], template_name: str) -> str:
    """Loads the a cmake file template and renders it with the correct details.

    Args:
        context: The context to pass to jinja2
        template_name: The name of a template file in the templates directory.

    Returns:
        The contents of the rendered CMake file.
    """
    env = jinja2.Environment(loader=jinja2.PackageLoader("mbed_build", str(TEMPLATES_DIRECTORY)),)
    template = env.get_template(template_name)
    return template.render(context)
