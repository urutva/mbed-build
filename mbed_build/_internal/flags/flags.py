import datetime
import itertools
import json
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, List, Dict

from mbed_targets import Target
from mbed_build._internal.toolchain import Toolchain


@dataclass(frozen=True)
class BuildFlags:
    cxx: Tuple[str]
    c: Tuple[str]
    cxx_link: Tuple[str]
    cxx_pp: Tuple[str]
    asm: Tuple[str]
    definitions: Tuple[str]
    link_libraries: Tuple[str]

    @classmethod
    def from_build_data(cls, profile_path: Path, toolchain: Toolchain, target: Target):
        flags = json.loads(profile_path.read_text())[toolchain.name]
        flags["common"] += _get_core_common_flags(toolchain.name, target.core)
        flags["common"] += _get_target_specific_common_flags(target)
        common_with_mem_regions = flags["common"] + _get_memory_region_flags(target.device_name)
        flags["ld"] += _get_target_specific_linker_flags(target)
        flags["ld"] = _sanitise_linker_flags(flags["ld"])
        _remove_unused_profile_flags(flags, ["-c"])
        definitions = (
            _get_target_compile_definitions(target)
            + _get_core_compile_definitions(target.core)
            + _get_toolchain_compile_definitions(toolchain)
        )
        return cls(
            cxx=tuple(common_with_mem_regions + flags["cxx"]),
            c=tuple(common_with_mem_regions + flags["c"]),
            asm=tuple(flags["common"] + flags["asm"]),
            cxx_link=tuple(common_with_mem_regions + flags["ld"]),
            cxx_pp=tuple(common_with_mem_regions + flags["ld"] + _get_toolchain_preprocessor_flags(toolchain.name)),
            definitions=tuple(definitions),
            link_libraries=tuple(_get_target_link_libraries(toolchain.name))
        )


FLAGS_DATA_DIR = Path(__file__).parent / "data"
CORE_COMPILE_FLAGS_FILE_PATH = FLAGS_DATA_DIR / "core_compile_flags.json"
CORE_COMPILE_DEFINITIONS_PATH = FLAGS_DATA_DIR / "core_compile_definitions.json"
CMSIS_PACK_INDEX = FLAGS_DATA_DIR / "cmsis_pack_index.json"


def _sanitise_linker_flags(linker_defines):
    new_linker_defines = list()
    for define in linker_defines:
        if re.search(r",_\w", define):
            define = define.replace(",_", ",__")

        new_linker_defines.append(define)

    return new_linker_defines


def _remove_unused_profile_flags(
    profile_flags: Dict[str, List[str]], flags_to_filter: List[str]
) -> Dict[str, List[str]]:
    """Remove flags_to_filter from profile_flags.

    The flags are removed in place, profile_flags is mutated by this function and treated as an in/out parameter.
    """
    for flag_type, filter_flag in itertools.product(profile_flags, flags_to_filter):
        if filter_flag in profile_flags[flag_type]:
            profile_flags[flag_type].remove(filter_flag)


def _get_core_common_flags(toolchain_name: str, target_core: str) -> List[str]:
    return json.loads(CORE_COMPILE_FLAGS_FILE_PATH.read_text())[toolchain_name][target_core]


def _get_memory_region_flags(device_name: str) -> List[str]:
    memory_regions = json.loads(CMSIS_PACK_INDEX.read_text())[device_name]["memories"]
    output = []
    for region_name, region_data in memory_regions.items():
        region_number = int(region_name[-1]) - 1  # region_name always ends with an integer counting from 1
        stringified_region_num = str(region_number if region_number else '')
        region_start = f"-DMBED_{region_name[1:-1]}{stringified_region_num}_START=0x{region_data['start']:0x}"
        region_end = f"-DMBED_{region_name[1:-1]}{stringified_region_num}_SIZE=0x{region_data['size']:0x}"
        output.append(region_start)
        output.append(region_end)

    return output


def _get_target_specific_common_flags(target: Target) -> List[str]:
    if target.printf_lib == "minimal-printf":
        return ["-DMBED_MINIMAL_PRINTF"]

    return []


def _get_target_specific_linker_flags(target: Target) -> List[str]:
    xip_enable = bool(target.config["xip-enable"]["value"])
    output = [
        f"-DXIP_ENABLE={1 if xip_enable else 0}",
        f"-DMBED_BOOT_STACK_SIZE={int(target.config['boot-stack-size']['value'], 16) // 4}",
    ]
    if target.printf_lib == "minimal-printf":
        output += [
            "-Wl,--wrap,printf",
            "-Wl,--wrap,sprintf",
            "-Wl,--wrap,snprintf",
            "-Wl,--wrap,vprintf",
            "-Wl,--wrap,vsprintf",
            "-Wl,--wrap,vsnprintf",
            "-Wl,--wrap,fprintf",
            "-Wl,--wrap,vfprintf",
        ]

    return output


def _get_target_compile_definitions(target: Target) -> List[str]:
    output = []
    for label_def in target.labels:
        output.append(f"-DTARGET_{label_def}")

    for component_def in target.components:
        output.append(f"-DCOMPONENT_{component_def}=1")

    for device_specific in target.device_has:
        output.append(f"-DDEVICE_{device_specific}=1")

    for target_macro in target.macros:
        output.append(f"-D{target_macro}")

    for form_factor in target.supported_form_factors:
        output.append(f"-DTARGET_FF_{form_factor}")

    # Symbols defined for the online build system
    now = datetime.datetime.now()
    output += [f"-DMBED_BUILD_TIMESTAMP={datetime.datetime.timestamp(now)}", '-DTARGET_LIKE_MBED', '-D__MBED__=1']

    return output


def _get_core_compile_definitions(core: str) -> List[str]:
    return [f"-D{core_def}" for core_def in json.loads(CORE_COMPILE_DEFINITIONS_PATH.read_text())[core]]


def _get_toolchain_compile_definitions(toolchain: Toolchain) -> List[str]:
    return [f"-DTOOLCHAIN_{label}" for label in toolchain.labels]


def _get_target_link_libraries(toolchain_name: str) -> List[str]:
    if toolchain_name != "GCC_ARM":
        return []

    return ["-lstdc++", "-lsupc++", "-lm", "-lc", "-lgcc", "-lnosys"]


def _get_toolchain_preprocessor_flags(toolchain_name: str) -> List[str]:
    if toolchain_name != "GCC_ARM":
        return []

    return ["-E", "-P"]
