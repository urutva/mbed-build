#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
import json
import pathlib
import tempfile
from unittest import TestCase

from mbed_build._internal.config.config_source import ConfigSource, _namespace_data


class TestFromMbedLib(TestCase):
    def test_builds_namespaced_config_source_from_mbed_lib_json(self):
        json_data = {
            "name": "ns-hal-pal",
            "config": {
                "nvm_cfstore": {
                    "help": "Use cfstore as a NVM storage. Else RAM simulation will be used",
                    "value": False,
                },
            },
            "target_overrides": {
                "*": {"rsa-required": True, "target.some-setting": 123, "target.add_features": ["BLE"]}
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            json_file = pathlib.Path(directory, "file.json")
            json_file.write_text(json.dumps(json_data))

            subject = ConfigSource.from_mbed_lib(json_file)

        self.assertEqual(
            subject,
            ConfigSource(
                file=json_file,
                config=_namespace_data(json_data["config"], json_data["name"]),
                target_overrides=_namespace_data(json_data["target_overrides"], json_data["name"]),
            ),
        )

    def test_gracefully_handles_missing_data(self):
        json_data = {"name": "foo"}

        with tempfile.TemporaryDirectory() as directory:
            json_file = pathlib.Path(directory, "file.json")
            json_file.write_text(json.dumps(json_data))

            subject = ConfigSource.from_mbed_lib(json_file)

        self.assertEqual(subject, ConfigSource(file=json_file, config={}, target_overrides={}))


class TestNamespaceData(TestCase):
    def test_prefixes_keys_without_namespace(self):
        data = {
            "foo": True,
            "hat.bar": 123,
        }

        self.assertEqual(_namespace_data(data, "my-prefix"), {"my-prefix.foo": True, "hat.bar": 123})
