from mbed_targets import get_target_by_name
from mbed_project import MbedProgram

from mbed_build._internal.flags import get_build_flags
from mbed_build._internal.toolchain import Toolchain
from mbed_build._internal.sources import BuildFiles
from mbed_build._internal.context.build_context import BuildContext


def create_build_context(toolchain_name, program_path, target_name):
    program = MbedProgram.from_existing(program_path)
    target = get_target_by_name(target_name, program.root_path)
    toolchain = Toolchain.from_name(toolchain_name)
    files = BuildFiles(program.root_path, target, toolchain.labels)
    flags = get_build_flags(toolchain, target)

    return BuildContext(
        project_name=program.root_path.stem,
        source_files=files.get_source_paths(),
        include_dirs=files.get_include_paths(),
        precompile_headers=files.get_precompiled_header_paths(),
        linker_script=files.get_linker_script_path(),
        build_flags=flags,
        toolchain=toolchain
    )
