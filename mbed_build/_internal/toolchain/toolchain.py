from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Toolchain:
    name: str
    labels: List[str]
    c_compiler: str
    cxx_compiler: str
    cxx_preprocessor: str
    asm_compiler: str
    elf_to_bin: str

    @classmethod
    def from_name(cls, toolchain_name: str):
        if toolchain_name == "GCC":
            return cls(
                name="GCC_ARM",
                labels=["GCC_ARM", "GCC"],
                c_compiler="arm-none-eabi-gcc",
                cxx_compiler="arm-none-eabi-g++",
                cxx_preprocessor="arm-none-eabi-cpp",
                asm_compiler="arm-none-eabi-gcc",
                elf_to_bin="arm-none-eabi-objcopy"
            )

        if toolchain_name == "ARMC6":
            return cls(
                name=toolchain_name,
                c_compiler="armc",
                cxx_compiler="armcxx",
                asm_compiler="armasm",
                elf_to_bin="fromelf",
            )

        raise ValueError(f"{toolchain_name} is not a supported toolchain.")
