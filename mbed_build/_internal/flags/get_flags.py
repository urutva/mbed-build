from pathlib import Path

from mbed_targets import Target
from mbed_build._internal.flags.flags import BuildFlags
from mbed_build._internal.toolchain import Toolchain


def get_build_flags(build_profiles_dir: Path, toolchain: Toolchain, target: Target, profile_type: str = "debug"):
    return BuildFlags.from_build_data(
        build_profiles_dir / f"{profile_type.lower()}.json",
        toolchain,
        target,
    )
