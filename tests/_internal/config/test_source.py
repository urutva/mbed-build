#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
import json
import pathlib
import tempfile
from unittest import TestCase, mock

from mbed_build._internal.config.source import Source, _namespace_data, _filter_target_overrides


class TestSource(TestCase):
    def test_from_mbed_lib(self):
        with tempfile.TemporaryDirectory() as directory:
            data = {
                "name": "foo",
                "config": {"a-number": 123, "a-bool": {"help": "Simply a boolean", "value": True}},
                "target_overrides": {
                    "*": {"a-number": 456, "target.features_add": ["FOO"]},
                    "NOT_THIS_TARGET": {"a-string": "foo", "target.features_add": ["BAR"]},
                    "THIS_TARGET": {"a-bool": False, "other-lib.something-else": "blah"},
                },
                "macros": ["MACRO=1"],
            }
            file = pathlib.Path(directory, "mbed_lib.json")
            file.write_text(json.dumps(data))

            subject = Source.from_mbed_lib(file, ["THIS_TARGET"])

        self.assertEqual(
            subject,
            Source(
                human_name=f"File: {file}",
                config={"foo.a-number": 123, "foo.a-bool": {"help": "Simply a boolean", "value": True}},
                overrides={
                    "foo.a-number": 456,
                    "foo.a-bool": False,
                    "other-lib.something-else": "blah",
                    "target.features_add": ["FOO"],
                },
                macros=["MACRO=1"],
            ),
        )

    def test_from_mbed_app(self):
        with tempfile.TemporaryDirectory() as directory:
            data = {
                "config": {"a-bool": False, "a-number": {"help": "Simply a number", "value": 0}},
                "target_overrides": {
                    "*": {"a-bool": True, "target.features_add": ["HAT"]},
                    "NOT_THIS_TARGET": {"a-number": 999, "target.features_add": ["BOAT"]},
                    "THIS_TARGET": {"a-number": 2, "some-lib.something-else": "blah"},
                },
                "macros": ["SOME_MACRO=2"],
            }
            file = pathlib.Path(directory, "mbed_app.json")
            file.write_text(json.dumps(data))

            subject = Source.from_mbed_app(file, ["THIS_TARGET"])

        self.assertEqual(
            subject,
            Source(
                human_name=f"File: {file}",
                config={"app.a-bool": False, "app.a-number": {"help": "Simply a number", "value": 0}},
                overrides={
                    "app.a-number": 2,
                    "app.a-bool": True,
                    "some-lib.something-else": "blah",
                    "target.features_add": ["HAT"],
                },
                macros=["SOME_MACRO=2"],
            ),
        )

    @mock.patch("mbed_build._internal.config.source.get_target_by_board_type")
    def test_from_target(self, get_target_by_board_type):
        # Warning: Target is a dataclass and dataclasses provide no type safety when mocking
        target = mock.Mock(
            features={"feature_1"},
            components={"component_1"},
            labels={"label_1"},
            config={"foo": "bar", "target.bool": True},
        )
        get_target_by_board_type.return_value = target
        mbed_target = "K66F"
        mbed_program_directory = pathlib.Path("foo")

        subject = Source.from_target(mbed_target, mbed_program_directory)

        self.assertEqual(
            subject,
            Source(
                human_name=f"mbed_target.Target for {mbed_target}",
                config={"target.foo": "bar", "target.bool": True},
                overrides={
                    "target.features": target.features,
                    "target.components": target.components,
                    "target.labels": target.labels,
                },
                macros=[],
            ),
        )


class TestFilterTargetOverrides(TestCase):
    def test_returns_overrides_only_for_given_labels(self):
        subject = _filter_target_overrides(
            {"*": {"number": 123}, "B_TARGET": {"string": "boat"}, "A_TARGET": {"bool": True}}, ["A_TARGET"]
        )

        self.assertEqual(subject, {"number": 123, "bool": True})


class TestNamespaceData(TestCase):
    def test_prefixes_keys_without_namespace(self):
        data = {
            "foo": True,
            "hat.bar": 123,
        }

        self.assertEqual(_namespace_data(data, "my-prefix"), {"my-prefix.foo": True, "hat.bar": 123})
