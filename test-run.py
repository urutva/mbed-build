import pathlib
from mbed_build._internal.config.config import build_config
from pprint import pprint

# mbed_program_directory = pathlib.Path("/Users/muchzill4/Projects/build-tools/playground/mbed-cloud-client-example/")
mbed_program_directory = pathlib.Path("/Users/muchzill4/Projects/build-tools/playground/mbed-os-example-blinky/")
board_type = "K64F"


config = build_config(mbed_program_directory, board_type)

for key, entry in config["settings"].items():
    print(f"{key} = {entry['value']} (macro_name: {entry.get('macro_name', 'n/a')})")
