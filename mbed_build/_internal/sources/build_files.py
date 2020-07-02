"""Find all translation units and include directories for the compiler."""
from pathlib import Path
from typing import List, Dict, Set

from mbed_targets import Target
from mbed_build._internal.find_files import find_files, LabelFilter


class BuildFiles:
    def __init__(self, program_dir: Path, target: Target, toolchain_labels: List[str]):
        self._all_build_files = _find_build_files_for_target_and_toolchain(
            program_dir, target, toolchain_labels, ("*.c", "*.cpp", "*.s", "*.S", "*.h", "*.hpp", "mstd_*", "*.ld")
        )

    def get_source_paths(self):
        return set(f for f in self._all_build_files if f.suffix in (".c", ".cpp", ".s", ".S", ""))

    def get_include_paths(self):
        return set(ip for h in self._all_build_files if h.suffix in (".h", ".hpp", "") for ip in h.parents)

    def get_linker_script_path(self):
        return set(l for l in self._all_build_files if l.suffix == ".ld").pop()

    def get_precompiled_header_paths(self):
        return set(h for h in self._all_build_files if h.suffix == "")


def _find_build_files_for_target_and_toolchain(program_root: Path, target: Target, toolchain_labels: List[str], ext_patterns: List[str]) -> Set[Path]:
    labels = _create_label_map(target.labels, target.features, target.components, toolchain_labels)
    filters = _create_filters(labels)
    # Create a set of null filters so we find all build files not in a label directory.
    null_filters = _create_filters(_create_label_map([], [], [], []))
    build_files = []
    for ext in ext_patterns:
        build_files.extend(find_files(ext, program_root, filters))
        build_files.extend(find_files(ext, program_root, null_filters))

    return set(s.relative_to(program_root) for s in build_files)


def _create_label_map(target_labels: List[str], target_features: List[str], target_components: List[str], toolchain: List[str]):
    return {
        "TARGET": target_labels, "FEATURE": target_features, "COMPONENT": target_components, "TOOLCHAIN": toolchain
    }


def _create_filters(labels: Dict[str, List[str]]):
    return [LabelFilter(label_type, label_values) for label_type, label_values in labels.items()]
