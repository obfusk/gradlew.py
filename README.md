<!-- SPDX-FileCopyrightText: 2024 FC (Fay) Stegerman <flx@obfusk.net> -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

[![GPLv3+](https://img.shields.io/badge/license-GPLv3+-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

# gradlew.py

## pure python gradle wrapper

```bash
$ git clone https://github.com/obfusk/gradlew.py.git
$ gradlew.py/gradlew.py --help
usage: gradlew.py [-h] [--libdir LIBDIR] [--version VERSION] [-v] [GRADLE_ARG ...]

pure python gradle wrapper

options:
  -h, --help         show this help message and exit
  --libdir LIBDIR    directory for gradle [default: '/home/username/.gradlewpy']
  --version VERSION  override gradle version
  -v, --verbose
$ gradlew.py/gradlew.py assembleRelease
[...]
```

## update checksums

```bash
$ make
```

## License

[![GPLv3+](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl-3.0.html)

<!-- vim: set tw=70 sw=2 sts=2 et fdm=marker : -->
