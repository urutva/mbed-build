from dataclasses import dataclass
from pathlib import Path
from typing import List, Any, Dict

from mbed_build._internal.toolchain import Toolchain
from mbed_build._internal.flags import BuildFlags


@dataclass
class BuildContext:
    project_name: str
    source_files: List[Path]
    include_dirs: List[Path]
    precompile_headers: List[Path]
    linker_script: Path
    build_flags: BuildFlags
    toolchain: Toolchain

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = vars(self)
        output = dict()

        for key, val in obj_dict.items():
            if not isinstance(val, (BuildFlags, Toolchain)):
                output[key] = val
            else:
                output.update(vars(val))

        return output
