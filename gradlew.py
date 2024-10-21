#!/usr/bin/env python3
# encoding: utf-8
# SPDX-FileCopyrightText: 2024 FC (Fay) Stegerman <flx@obfusk.net>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

GRADLE_VERSIONS_ALL_URL = "https://services.gradle.org/versions/all"
GRADLE_BINZIP_URL = "https://services.gradle.org/distributions/gradle-{}-bin.zip"
GRADLE_SHA256_URL = "https://services.gradle.org/distributions/gradle-{}-bin.zip.sha256"
GRADLE_BINZIP_RX = re.compile(r"https://services\.gradle\.org/distributions/gradle-(.*)-bin.zip")

LIBDIR = os.environ.get("GRADLEW_PY_LIBDIR") or str(Path.home() / ".gradlewpy")


class Error(Exception):
    """Error."""


def gradlew(*args: str, libdir: str, version: Optional[str] = None,
            verbose: bool = False) -> None:
    """Gradle wrapper."""
    gradle_versions = load_gradle_versions()
    wrapper_binzip_url = wrapper_sha256 = None
    if not version:
        if not os.path.exists(_wrapper_props()):
            raise Error(f"No such file: {_wrapper_props()!r}")
        wrapper_binzip_url, wrapper_sha256 = load_wrapper_urls()
        if not (m := GRADLE_BINZIP_RX.fullmatch(wrapper_binzip_url)):
            raise Error(f"Unsupported URL: {wrapper_binzip_url!r}")
        version = m[1]
    if version not in gradle_versions:
        raise Error(f"Unknown gradle version: {version!r}")
    binzip_url = gradle_versions[version]["binzip_url"]
    sha256 = gradle_versions[version]["sha256"]
    if wrapper_binzip_url and binzip_url != wrapper_binzip_url:
        raise Error(f"URL mismatch: expected {binzip_url!r}, .properties has {wrapper_binzip_url!r}")
    if wrapper_sha256 and sha256 != wrapper_sha256:
        raise Error(f"SHA-256 mismatch: expected {sha256!r}, .properties has {wrapper_sha256!r}")
    gradle_cmd = download_gradle(libdir, version, binzip_url, sha256, verbose=verbose)
    run_command(gradle_cmd, *args, verbose=verbose)


def download_gradle(libdir: str, version: str, binzip_url: str, sha256: str,
                    *, verbose: bool = False) -> str:
    """Download gradle."""
    gradle_cmd = os.path.join(libdir, f"gradle-{version}", "bin", "gradle")
    if os.path.exists(gradle_cmd):
        return gradle_cmd
    if verbose:
        print(f"[DOWNLOAD] {binzip_url!r}", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmpdir:
        outfile = os.path.join(tmpdir, "gradle.zip")
        if shutil.which("wget"):
            run_command("wget", "-q", "-O", outfile, "--", binzip_url, verbose=verbose)
            dl_sha256 = sha256_file(outfile)
        else:
            dl_sha256 = download_file(binzip_url, outfile)
        if dl_sha256 != sha256:
            raise Error(f"SHA-256 mismatch: expected {sha256!r}, actual {dl_sha256!r}")
        Path(libdir).mkdir(exist_ok=True)
        if shutil.which("unzip"):
            run_command("unzip", "-q", "-d", libdir, outfile, verbose=verbose)
        else:
            if verbose:
                print(f"[UNZIP] path={libdir!r} {outfile!r}", file=sys.stderr)
            import zipfile
            with zipfile.ZipFile(outfile) as zf:
                zf.extractall(libdir)
            os.chmod(gradle_cmd, 0o755)
    return gradle_cmd


def load_wrapper_urls() -> Tuple[str, Optional[str]]:
    """Load gradle-wrapper.properties."""
    binzip_url, sha256 = None, None
    with open(_wrapper_props(), encoding="utf-8") as fh:
        for line in (line.rstrip("\n") for line in fh):
            if line.startswith("distributionUrl="):
                if binzip_url:
                    print("Warning: more than one distributionUrl in gradle-wrapper.properties",
                          file=sys.stderr)
                binzip_url = line.split("=", 1)[-1].replace("https\\:", "https:", 1)
            elif line.startswith("distributionSha256Sum="):
                if sha256:
                    print("Warning: more than one distributionSha256Sum in gradle-wrapper.properties",
                          file=sys.stderr)
                sha256 = line.split("=", 1)[-1]
    if not binzip_url:
        raise Error("No distributionUrl in gradle-wrapper.properties")
    if not sha256:
        print("Warning: no distributionSha256Sum in gradle-wrapper.properties", file=sys.stderr)
    return binzip_url, sha256


def _wrapper_props() -> str:
    return os.path.join("gradle", "wrapper", "gradle-wrapper.properties")


def load_gradle_versions() -> Dict[Any, Any]:
    """Load gradle-versions.json."""
    with open(_gradle_versions_json(), encoding="utf-8") as fh:
        return json.load(fh)        # type: ignore[no-any-return]


def save_gradle_versions(data: Dict[Any, Any]) -> None:
    """Save gradle-versions.json."""
    with open(_gradle_versions_json(), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def update_gradle_versions(*, verbose: bool = False) -> None:
    """Update gradle-versions.json."""
    with urllib.request.urlopen(GRADLE_VERSIONS_ALL_URL) as fh:
        data = {}
        for vsn in json.load(fh):
            if vsn["nightly"] or vsn["snapshot"]:
                continue
            version = vsn["version"]
            binzip_url = vsn["downloadUrl"]
            sha256_url = vsn["checksumUrl"]
            if GRADLE_BINZIP_URL.format(version) != binzip_url:
                print(f"Warning: skipping bad URL {binzip_url!r}", file=sys.stderr)
                continue
            if GRADLE_SHA256_URL.format(version) != sha256_url:
                print(f"Warning: skipping bad URL {sha256_url!r}", file=sys.stderr)
                continue
            if version in data:
                raise Error(f"Duplicate version: {version!r}")
            sha256 = _gradle_sha256(sha256_url)
            if verbose:
                print(f"Processed {version!r}.")
            data[version] = {"binzip_url": binzip_url, "sha256": sha256}
        save_gradle_versions(data)


def _gradle_sha256(url: str) -> str:
    with urllib.request.urlopen(url) as fh:
        sha256: str = fh.read().decode()
        if not len(sha256) == 64 and all(c in "0123456789abcdef" for c in sha256):
            raise Error(f"Malformed SHA-256: {sha256!r}")
        return sha256


def _gradle_versions_json() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "gradle-versions.json")


# FIXME: retry!
def download_file(url: str, outfile: str) -> str:
    """Download file and get SHA-256."""
    with open(outfile, "wb") as fho:
        with urllib.request.urlopen(url) as fhi:
            sha = hashlib.sha256()
            while chunk := fhi.read(4096):
                fho.write(chunk)
                sha.update(chunk)
            return sha.hexdigest()


def sha256_file(filename: str) -> str:
    r"""
    Calculate SHA-256 checksum of file.

    >>> sha256_file("/dev/null")
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

    """
    with open(filename, "rb") as fh:
        sha = hashlib.sha256()
        while chunk := fh.read(4096):
            sha.update(chunk)
        return sha.hexdigest()


def run_command(*args: str, verbose: bool = False) -> None:
    """Run command."""
    if verbose:
        print(f"[RUN] {' '.join(map(repr, args))}", file=sys.stderr)
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        raise Error(f"{args[0]} command failed") from e
    except FileNotFoundError as e:
        raise Error(f"{args[0]} command not found") from e


def main() -> None:
    usage = "gradlew.py [-h] [--libdir LIBDIR] [--version VERSION] [-v] [GRADLE_ARG ...]"
    parser = argparse.ArgumentParser(description="pure python gradle wrapper", usage=usage)
    parser.add_argument("--libdir", default=LIBDIR,
                        help=f"directory for gradle [default: {LIBDIR!r}]")
    parser.add_argument("--version", help="override gradle version")
    parser.add_argument("-v", "--verbose", action="store_true")
    args, rest = parser.parse_known_args()
    if rest and rest[0] == "--":
        rest = rest[1:]
    try:
        gradlew(*rest, libdir=args.libdir, version=args.version, verbose=args.verbose)
    except Error as e:
        print(f"Error: {e}.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# vim: set tw=80 sw=4 sts=4 et fdm=marker :
