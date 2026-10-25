"""Make a local, allowlisted web ZIP; never copy the repository or deploy it.

Usage: python3 web/package_release.py [--output out/release/NAME.zip]
Requires POSIX Python 3.8+ (Linux/macOS), with no third-party dependencies.
Run the normal checks first. This packages the current generated files; it is
not a substitute for gameplay, browser/device, or release/privacy review.
"""
import argparse
from contextlib import contextmanager
import hashlib
import io
import os
from pathlib import Path
import secrets
import stat
import zipfile


ROOT = Path(__file__).absolute().parents[1]
DEFAULT_OUTPUT = "out/release/beard-climber-web.zip"
# Deliberately enumerate files, not directories, globs, or a configurable input.
# An additional runtime asset requires an explicit code and test review here.
SOURCE_FILES = (
    ("index.html", "web/index.html"),
    ("assets/world2.js", "web/assets/world2.js"),
    ("assets/world3.js", "web/assets/world3.js"),
    ("LICENSE", "LICENSE"),
)
GENERATED_FILES = ((".nojekyll", b""),)
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


class ReleaseError(ValueError):
    """An unsafe or incomplete release request; no publishing is performed."""


def safe_parts(path):
    """Accept only unambiguous relative POSIX paths, including ZIP member names."""
    if not isinstance(path, str) or not path or "\\" in path or ":" in path or "\x00" in path:
        raise ReleaseError("Expected a clean relative POSIX path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ReleaseError("Absolute, empty, dot, and parent path segments are forbidden")
    return tuple(parts)


def output_parts(output):
    parts = safe_parts(output)
    if len(parts) != 3 or parts[:2] != ("out", "release") or not parts[2].endswith(".zip"):
        raise ReleaseError("Output must be out/release/NAME.zip; source/release files cannot be overwritten")
    return parts


def require_safe_filesystem():
    needed = (os.open, os.mkdir, os.link, os.unlink, os.stat)
    if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
            or not all(fn in os.supports_dir_fd for fn in needed)
            or os.link not in os.supports_follow_symlinks):
        raise ReleaseError("Safe packaging requires POSIX no-follow/dir-fd operations (Linux/macOS)")


@contextmanager
def directory_at(parent_fd, parts, create=False):
    """Walk directories without following symlinks, anchored to an open parent."""
    fd = os.dup(parent_fd)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def repository_at(root):
    # Do not resolve(): that would erase evidence of a symlink in the root path.
    root = Path(root).absolute()
    if ".." in root.parts:
        raise ReleaseError("Repository path must not contain parent segments")
    anchor = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with directory_at(anchor, root.parts[1:]) as fd:
            yield fd
    finally:
        os.close(anchor)


def read_regular(root_fd, path):
    parts = safe_parts(path)
    with directory_at(root_fd, parts[:-1]) as parent:
        # NONBLOCK prevents a malicious FIFO from hanging before fstat rejects it.
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ReleaseError("Release inputs must be ordinary, non-hardlinked files: " + path)
            return handle.read()


def release_bytes(root_fd):
    entries = list(GENERATED_FILES)
    for member, source in SOURCE_FILES:
        entries.append((member, read_regular(root_fd, source)))
    names = [member for member, _ in entries]
    for member in names:
        safe_parts(member)
    if len(set(names)) != len(names):
        raise ReleaseError("Duplicate ZIP member names are forbidden")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as bundle:
        for member, content in sorted(entries):
            info = zipfile.ZipInfo(member, ZIP_DATE)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED
            bundle.writestr(info, content)
    # Uncompressed ZIP avoids differences between compression-library versions.
    return archive.getvalue()


def publish_archive(parent_fd, name, content):
    """Publish a complete ZIP atomically, never replacing an existing pathname."""
    temporary = ".beard-release-" + secrets.token_hex(16) + ".tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=parent_fd)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
                    follow_symlinks=False)
        except FileExistsError as exc:
            raise ReleaseError("Output already exists; inspect it and choose a new filename: " + name) from exc
    finally:
        # Only this invocation's random temporary is removed. Never clear out/.
        os.unlink(temporary, dir_fd=parent_fd)


def package_release(root=ROOT, output=DEFAULT_OUTPUT):
    parts = output_parts(output)
    require_safe_filesystem()
    with repository_at(root) as repo_fd:
        # Build and validate every input before creating any output directory.
        content = release_bytes(repo_fd)
        with directory_at(repo_fd, parts[:-1], create=True) as parent:
            publish_archive(parent, parts[-1], content)
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Repository-relative out/release/NAME.zip; existing paths are never overwritten")
    args = parser.parse_args()
    try:
        digest = package_release(output=args.output)
    except (OSError, ReleaseError) as exc:
        parser.exit(1, "Release packaging failed (nothing deployed): " + str(exc) + "\n")
    print("Created " + args.output + " (local artifact only; nothing deployed)")
    print("Contents: .nojekyll, LICENSE, assets/world2.js, assets/world3.js, index.html")
    print("SHA-256: " + digest)


if __name__ == "__main__":
    main()
