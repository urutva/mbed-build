#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
from unittest import TestCase
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import patchfs

from mbed_build._internal.find_files import (
    find_files,
    exclude_using_mbedignore,
)


class TestFindFiles(TestCase):
    @patchfs
    def test_finds_files_by_name_in_given_root(self, fs):
        files = (
            Path("root", "folder_1", "file.txt"),
            Path("root", "folder_1", "folder_1_1", "file.txt"),
            Path("root", "folder_2", "file.txt"),
        )
        for file in files:
            fs.create_file(file)

        subject = find_files("file.txt", directory=Path("root"))

        for file in files:
            self.assertIn(file, subject)


class TestExcludeListedInMbedignore(TestCase):
    @patchfs
    def test_excludes_files_ignored_by_mbedignore(self, fs):
        mbedignore_contents = """
*.py
hidden.txt

*/test/*
*/stubs/*
stubs/*
"""
        mbedignore_path = Path("project", ".mbedignore")
        fs.create_file(mbedignore_path, contents=mbedignore_contents)

        paths = [
            Path("outside_of_project", "hidden.txt"),
            Path("foo.py"),
            Path("project", "test", "foo.html"),
        ]

        excluded_paths = [
            Path("project", "nested", "test", "file.doc"),
            Path("project", "nested", "stubs", "file.xls"),
            Path("project", "stubs", "file.xls"),
            Path("project", "hidden.txt"),
            Path("project", "file.py"),
        ]

        subject = exclude_using_mbedignore(mbedignore_path, paths + excluded_paths)

        for path in subject:
            self.assertIn(path, paths, f"{path} should be excluded")