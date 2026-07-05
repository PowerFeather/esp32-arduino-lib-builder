# PM Support Release Flow

This repository keeps power-management-enabled builds in long-lived support
branches and publishes immutable release artifacts from those branches.

## Branches

- `pm-support/arduino-2.x`: Arduino ESP32 2.x / ESP-IDF 4.4 support.
- `pm-support/arduino-3.x`: Arduino ESP32 3.x / ESP-IDF 5.x support.

Release branches are intentionally not required. A release is reproducible from
the support branch, the upstream PlatformIO or pioarduino release, and the
manifest uploaded with the artifact.

## Release Tags

Use tags that include the provider and Arduino version:

- `pm-support-platformio-v7.0.1-arduino-2.0.17`
- `pm-support-pioarduino-55.03.39-arduino-3.3.9`

Artifact names should mirror the tag, for example:

```text
framework-arduinoespressif32-pm-support-platformio-v7.0.1-arduino-2.0.17.tar.gz
framework-arduinoespressif32-pm-support-pioarduino-55.03.39-arduino-3.3.9.tar.gz
```

## Resolving Upstream Versions

Do not scrape release HTML. Use structured metadata:

```bash
python3 tools/pm-support-release-info.py --provider platformio --tag latest
python3 tools/pm-support-release-info.py --provider pioarduino --tag latest
```

For official PlatformIO releases, the script reads `platform.json` and decodes
`framework-arduinoespressif32` package versions such as `~3.20017.0` into
Arduino `2.0.17`.

For pioarduino releases, the script reads `platform.json` and extracts Arduino
and ESP-IDF versions from the pinned Espressif framework artifact URLs.
