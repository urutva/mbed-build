#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
from unittest import TestCase

from mbed_build._internal.config.config import Config, Option, Macro
from tests._internal.config.factories import SourceFactory


class TestConfigFromSources(TestCase):
    def test_builds_config_from_sources(self):
        source_a = SourceFactory(config={"bool": True, "string": "foo"}, macros=["MACRO_A=A"])
        source_b = SourceFactory(config={"number": 1}, config_overrides={"bool": False}, macros=["MACRO_B=B"])

        config = Config.from_sources([source_a, source_b])

        self.assertEqual(
            config.options,
            {
                "bool": Option.build("bool", True, source_a).set_value(False, source_b),
                "number": Option.build("number", 1, source_b),
                "string": Option.build("string", "foo", source_a),
            },
        )

        self.assertEqual(
            config.macros,
            {"MACRO_A": Macro.build("MACRO_A=A", source_a), "MACRO_B": Macro.build("MACRO_B=B", source_b)},
        )

    def test_raises_when_trying_to_override_unset_option(self):
        source_a = SourceFactory(config={"bool": True})
        source_b = SourceFactory(config_overrides={"string": "hello"})

        with self.assertRaises(ValueError):
            Config.from_sources([source_a, source_b])

    def test_raises_when_trying_to_override_existing_macro(self):
        source_a = SourceFactory(macros=["MACRO_A=X"])
        source_b = SourceFactory(macros=["MACRO_A=Y"])

        with self.assertRaises(ValueError):
            Config.from_sources([source_a, source_b])

    def test_keeps_old_option_data(self):
        source_a = SourceFactory(config={"bool": {"help": "A simple bool", "value": True}})
        source_b = SourceFactory(config_overrides={"bool": False})

        config = Config.from_sources([source_a, source_b])

        self.assertEqual(config.options["bool"].help_text, "A simple bool")


class TestOptionBuild(TestCase):
    def test_builds_option_from_config_data(self):
        source = SourceFactory()
        data = {
            "value": 123,
            "help": "some help text",
            "macro_name": "FOO_MACRO",
        }
        option = Option.build(key="target.stack-size", data=data, source=source)

        self.assertEqual(
            option,
            Option(
                key="target.stack-size",
                value=data["value"],
                help_text=data["help"],
                macro_name=data["macro_name"],
                set_by=source.human_name,
            ),
        )

    def test_generates_macro_name_if_not_in_data(self):
        source = SourceFactory()
        data = {
            "value": 123,
            "help": "some help text",
        }
        option = Option.build(key="update-client.storage-size", data=data, source=source)

        self.assertEqual(option.macro_name, "MBED_CONF_UPDATE_CLIENT_STORAGE_SIZE")


class TestMacroBuild(TestCase):
    def test_builds_macros_with_value(self):
        source = SourceFactory()
        macro = Macro.build("FOO=BAR", source)

        self.assertEqual(
            macro, Macro(name="FOO", value="BAR", set_by=source.human_name),
        )

    def test_builds_macros_without_value(self):
        source = SourceFactory()
        macro = Macro.build("FOO", source)

        self.assertEqual(
            macro, Macro(name="FOO", value=None, set_by=source.human_name),
        )
