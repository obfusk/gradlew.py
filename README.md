<!-- SPDX-FileCopyrightText: 2024 FC (Fay) Stegerman <flx@obfusk.net> -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

[![GPLv3+](https://img.shields.io/badge/license-GPLv3+-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

# gradlew.py

## pure python gradle wrapper

```bash
$ git clone https://github.com/obfusk/gradlew.py.git
$ gradlew.py/gradlew.py --help
usage: gradlew.py [-h] [--distdir DISTDIR] [--version VERSION] [-v] [GRADLE_ARG ...]

pure python gradle wrapper

options:
  -h, --help         show this help message and exit
  --distdir DISTDIR  directory for gradle dists [default: '/home/username/.gradlewpy']
  --version VERSION  override gradle version
  -v, --verbose
$ gradlew.py/gradlew.py assembleRelease
[...]
```

## running gradle commands (after downloading and verifying the .zip)

* runs `bin/gradle` from the specified `gradle` version with the arguments
  (`GRADLE_ARG ...`) passed to it, just like the commonly used `gradlew` (which
  uses the `gradle` wrapper JAR);
* unless that version is already installed, downloads the `.zip` for the
  `gradle` version found in `gradle/wrapper/gradle-wrapper.properties` via
  `distributionUrl` (and also ensures a `distributionSha256Sum` if present
  matches the recorded SHA-256 checksum in `gradle-versions.json`);
* alternatively, the `gradle` version can be specified using `--version`;
* saves the unpacked `gradle` in e.g. `~/.gradlewpy/gradle-8.10` (for `gradle`
  `8.10`), the dist directory (`~/.gradlewpy` by default) can be overridden
  using `--distdir` or the `GRADLEW_PY_DISTDIR` environment variable;
* always checks the SHA-256 checksum of the downloaded `.zip` against the one
  recorded in `gradle-versions.json`, which is generated from
  `https://services.gradle.org/versions/all` (using `make`) before unpacking;
* this repository will be kept up-to-date with the latest checksums, all commits
  are signed with `C8EA133B41208D0BBA887452743E6469A1E8FF4E`, any changes to
  existing published checksums should be detected when updating (and anyone can
  run `make` to see if the checksums they get match);
* downloads using `wget` if available on `$PATH`, falls back to a Python
  implementation that does not currently retry failed downloads otherwise;
* extracts using `unzip` if available on `$PATH`, falls back to using Python's
  `zipfile` module (which should not be used with untrusted data) otherwise;
* to pass e.g. `--version` or `--help` to `gradle`, use `--` (if you need to
  also pass `--` to `gradle`, use `--` `--`).

## update checksums

```bash
$ make
```

## License

[![GPLv3+](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl-3.0.html)

<!-- vim: set tw=70 sw=2 sts=2 et fdm=marker : -->
