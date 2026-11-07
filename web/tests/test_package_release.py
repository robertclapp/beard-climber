"""Privacy and safety regressions for the allowlisted local release packager."""
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile


WEB = Path(__file__).absolute().parents[1]
SPEC = importlib.util.spec_from_file_location("package_release", WEB / "package_release.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)
EXPECTED = [".nojekyll", "LICENSE", "assets/world2.js", "assets/world3.js", "index.html"]


class ReleasePackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # /tmp itself can be a symlink on macOS. Resolve only the test fixture.
        self.root = Path(self.temporary.name).resolve() / "repo"
        self.root.mkdir()
        self.inputs = {
            "web/index.html": b"<html>fixed development candidate</html>\n",
            "web/assets/world2.js": b"window.world2 = {};\n",
            "web/assets/world3.js": b"window.world3 = {};\n",
            "LICENSE": b"All rights reserved.\n",
        }
        for name, content in self.inputs.items():
            self.write(name, content)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def build(self, name="first.zip"):
        output = "out/release/" + name
        digest = PACKAGER.package_release(self.root, output)
        path = self.root / output
        self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
        return path

    def assert_rejected(self, output=PACKAGER.DEFAULT_OUTPUT):
        with self.assertRaises((OSError, PACKAGER.ReleaseError)):
            PACKAGER.package_release(self.root, output)

    def test_exact_allowlist_and_canonical_bytes(self):
        self.write("index.html", b"old root release")
        self.write("assets/world2.js", b"old root pack")
        self.write(".nojekyll", b"not copied; marker must always be empty")
        path = self.build()
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(archive.namelist(), EXPECTED)
            self.assertEqual(archive.read(".nojekyll"), b"")
            for member, source in PACKAGER.SOURCE_FILES:
                self.assertEqual(archive.read(member), self.inputs[source])
            self.assertIsNone(archive.testzip())

    def test_extra_secrets_docs_source_and_output_are_never_included(self):
        excluded = [
            ".env", ".env.production", ".git/config", "README.md", "DEVELOPMENT.md",
            "HANDOFF.md", "docs/private.txt", "beard.py", "levels/secret.py",
            "native/private.txt", "web/src/game.js", "web/src/secret.env",
            "web/assets/.env", "web/assets/extra.js", "web/assets/private/secret.txt",
            "web/tests/private.txt", "web/build/cache.txt", "out/release/old.zip",
        ]
        for name in excluded:
            self.write(name, b"DO-NOT-SHIP-PRIVATE-MARKER")
        path = self.build()
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(archive.namelist(), EXPECTED)
        self.assertNotIn(b"DO-NOT-SHIP-PRIVATE-MARKER", path.read_bytes())
        for name in excluded:
            self.assertEqual((self.root / name).read_bytes(), b"DO-NOT-SHIP-PRIVATE-MARKER")

    def test_unlisted_symlinks_are_not_traversed(self):
        (self.root / "web/assets/unlisted").symlink_to(self.root, target_is_directory=True)
        (self.root / "web/assets/secret.txt").symlink_to(self.root / "missing-secret")
        self.build()

    def test_reproducible_bytes_ignore_mtimes_permissions_and_creation_order(self):
        first = self.build().read_bytes()
        for name, content in reversed(list(self.inputs.items())):
            path = self.root / name
            path.unlink()
            path.write_bytes(content)
            path.chmod(0o600)
            os.utime(path, (123456789, 123456789))
        second = self.build("second.zip").read_bytes()
        self.assertEqual(first, second)

    def test_normalized_archive_metadata(self):
        with zipfile.ZipFile(self.build()) as archive:
            self.assertEqual(archive.comment, b"")
            for item in archive.infolist():
                self.assertEqual(item.date_time, PACKAGER.ZIP_DATE)
                self.assertEqual(item.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(item.create_system, 3)
                self.assertEqual(item.external_attr >> 16, stat.S_IFREG | 0o644)
                self.assertEqual(item.extra, b"")
                self.assertEqual(item.comment, b"")

    def test_paths_reject_absolute_parent_dot_empty_and_windows_variants(self):
        invalid = ["", "/tmp/release.zip", "../release.zip", "out/../release/a.zip",
                   "out//release/a.zip", "out/release/./a.zip", "out/release/a.zip/",
                   "C:/out/release/a.zip", "out\\release\\a.zip", "out/release/a\x00.zip",
                   "web/index.html", "index.html", "out/release/a.txt", "out/release/sub/a.zip"]
        for output in invalid:
            with self.subTest(output=output):
                self.assert_rejected(output)
        self.assertFalse((self.root / "out").exists())

    def test_zip_member_paths_are_checked(self):
        for name in ("../secret", "/secret", "assets//secret", "assets/./secret", "C:secret", "a\\b"):
            with self.subTest(name=name), mock.patch.object(PACKAGER, "GENERATED_FILES", ((name, b""),)):
                self.assert_rejected()
        self.assertFalse((self.root / "out").exists())

    def test_duplicate_member_is_rejected(self):
        with mock.patch.object(PACKAGER, "GENERATED_FILES", (("index.html", b""),)):
            self.assert_rejected()

    def test_missing_input_fails_without_output(self):
        (self.root / "web/assets/world3.js").unlink()
        self.assert_rejected()
        self.assertFalse((self.root / "out").exists())

    def test_allowlisted_symlink_rejected_even_when_target_is_inside_repo(self):
        for name in self.inputs:
            with self.subTest(name=name):
                path = self.root / name
                path.unlink()
                path.symlink_to(self.write("secret", b"secret"))
                self.assert_rejected()
                path.unlink()
                path.write_bytes(self.inputs[name])
        self.assertFalse((self.root / "out").exists())

    def test_source_parent_symlink_rejected(self):
        assets = self.root / "web/assets"
        target = self.root / "other-assets"
        assets.rename(target)
        assets.symlink_to(target, target_is_directory=True)
        self.assert_rejected()
        self.assertFalse((self.root / "out").exists())

    def test_repository_symlink_rejected(self):
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            PACKAGER.package_release(alias)
        self.assertFalse((self.root / "out").exists())

    def test_hardlinked_input_rejected(self):
        os.link(self.root / "web/index.html", self.root / "another-name")
        self.assert_rejected()
        self.assertFalse((self.root / "out").exists())

    def test_nonregular_input_rejected_without_hanging(self):
        target = self.root / "web/assets/world3.js"
        target.unlink()
        os.mkfifo(target)
        self.assert_rejected()
        self.assertFalse((self.root / "out").exists())

    def test_stale_archive_refused_without_modifying_it_or_neighbors(self):
        path = self.write(PACKAGER.DEFAULT_OUTPUT, b"old release must survive")
        sentinel = self.write("out/release/unrelated.txt", b"do not remove")
        self.assert_rejected()
        self.assertEqual(path.read_bytes(), b"old release must survive")
        self.assertEqual(sentinel.read_bytes(), b"do not remove")
        self.assertEqual(sorted(p.name for p in path.parent.iterdir()), [path.name, sentinel.name])

    def test_existing_directory_refused_without_clearing_contents(self):
        sentinel = self.write(PACKAGER.DEFAULT_OUTPUT + "/private.txt", b"preserve")
        self.assert_rejected()
        self.assertEqual(sentinel.read_bytes(), b"preserve")

    def test_existing_output_symlink_and_dangling_symlink_refused(self):
        output = self.root / PACKAGER.DEFAULT_OUTPUT
        output.parent.mkdir(parents=True)
        outside = self.root.parent / "outside.zip"
        for existing in (True, False):
            with self.subTest(existing=existing):
                if existing:
                    outside.write_bytes(b"preserve")
                output.symlink_to(outside)
                self.assert_rejected()
                self.assertTrue(output.is_symlink())
                if existing:
                    self.assertEqual(outside.read_bytes(), b"preserve")
                    outside.unlink()
                else:
                    self.assertFalse(outside.exists())
                output.unlink()

    def test_output_parent_symlinks_rejected(self):
        for parent in ("out", "out/release"):
            with self.subTest(parent=parent):
                outside = self.root.parent / "outside-output"
                outside.mkdir(exist_ok=True)
                path = self.root / parent
                path.parent.mkdir(exist_ok=True)
                path.symlink_to(outside, target_is_directory=True)
                self.assert_rejected()
                self.assertEqual(list(outside.iterdir()), [])
                path.unlink()

    def test_failed_write_cleans_only_its_temporary(self):
        sentinel = self.write("out/release/keep.txt", b"keep")
        with mock.patch.object(PACKAGER.os, "fsync", side_effect=OSError("simulated disk failure")):
            self.assert_rejected()
        self.assertEqual(list(sentinel.parent.iterdir()), [sentinel])

    def test_failed_publish_cleans_only_its_temporary(self):
        sentinel = self.write("out/release/keep.txt", b"keep")
        # Patch publication rather than the filesystem capability probe.
        original = PACKAGER.publish_archive
        def fail_link(parent, name, content):
            with mock.patch.object(PACKAGER.os, "link", side_effect=OSError("simulated publication failure")):
                original(parent, name, content)
        with mock.patch.object(PACKAGER, "publish_archive", side_effect=fail_link):
            self.assert_rejected()
        self.assertEqual(list(sentinel.parent.iterdir()), [sentinel])

    def test_root_release_and_all_inputs_remain_unchanged(self):
        self.write("index.html", b"old root release")
        self.write("assets/world2.js", b"old root pack")
        before = {str(path.relative_to(self.root)): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        self.build()
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
