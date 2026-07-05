#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


GITHUB_API = "https://api.github.com/repos/{repo}/releases/{selector}"
RAW_PLATFORM_JSON = "https://raw.githubusercontent.com/{repo}/{ref}/platform.json"


def fetch_json(url, token=None):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_text(url, token=None):
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def github_release(repo, tag, token=None):
    selector = "latest" if tag == "latest" else f"tags/{tag}"
    return fetch_json(GITHUB_API.format(repo=repo, selector=selector), token)


def platform_json(repo, ref, token=None):
    text = fetch_text(RAW_PLATFORM_JSON.format(repo=repo, ref=ref), token)
    return json.loads(text)


def clean_platformio_package_version(version):
    return version.lstrip("~^<>=").split(",", 1)[0].split("+", 1)[0].strip()


def decode_platformio_arduino_version(package_version):
    version = clean_platformio_package_version(package_version)
    parts = version.split(".")
    if len(parts) < 2:
        raise ValueError(f"Unsupported PlatformIO Arduino package version: {package_version}")
    encoded = int(parts[1])
    major = encoded // 10000
    minor = (encoded % 10000) // 100
    patch = encoded % 100
    return f"{major}.{minor}.{patch}"


def first_match(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    return ""


def extract_version_from_url(url, patterns):
    return first_match(patterns, url)


def branch_for_arduino(arduino_version):
    major = arduino_version.split(".", 1)[0]
    return f"pm-support/arduino-{major}.x"


def artifact_name(provider, platform_version, arduino_version):
    return (
        "framework-arduinoespressif32-"
        f"pm-support-{provider}-{platform_version}-arduino-{arduino_version}.tar.gz"
    )


def official_platformio(tag, token):
    repo = "platformio/platform-espressif32"
    release = github_release(repo, tag, token)
    platform = platform_json(repo, release["tag_name"], token)
    package_version = platform["packages"]["framework-arduinoespressif32"]["version"]
    arduino_version = decode_platformio_arduino_version(package_version)
    release_text = "\n".join([release.get("name") or "", release.get("body") or ""])
    idf_version = first_match(
        [
            rf"Arduino[^\n]*v?{re.escape(arduino_version)}[^\n]*IDF v?([0-9][0-9A-Za-z.\-_]*)",
            r"based on IDF v?([0-9][0-9A-Za-z.\-_]*)",
        ],
        release_text,
    )
    platform_version = platform.get("version") or release["tag_name"].lstrip("v")
    return {
        "provider": "platformio",
        "platform_repo": repo,
        "platform_tag": release["tag_name"],
        "platform_version": platform_version,
        "platform_release_url": release["html_url"],
        "framework_arduinoespressif32": package_version,
        "arduino_core": arduino_version,
        "idf": idf_version,
        "support_branch": branch_for_arduino(arduino_version),
        "release_tag": f"pm-support-platformio-v{platform_version}-arduino-{arduino_version}",
        "artifact_name": artifact_name("platformio", f"v{platform_version}", arduino_version),
    }


def pioarduino(tag, token):
    repo = "pioarduino/platform-espressif32"
    release = github_release(repo, tag, token)
    platform = platform_json(repo, release["tag_name"], token)
    packages = platform["packages"]
    core_url = packages["framework-arduinoespressif32"]["version"]
    libs_url = packages.get("framework-arduinoespressif32-libs", {}).get("version", "")
    idf_url = packages.get("framework-espidf", {}).get("version", "")
    arduino_version = extract_version_from_url(
        core_url,
        [
            r"/releases/download/([0-9][0-9A-Za-z.\-_]*)/esp32-core-",
            r"esp32-core-([0-9][0-9A-Za-z.\-_]*)\.tar",
        ],
    )
    if not arduino_version:
        arduino_version = first_match(
            [r"Arduino Release v?([0-9][0-9A-Za-z.\-_]*)", r"Arduino to ([0-9][0-9A-Za-z.\-_]*)"],
            "\n".join([release.get("name") or "", release.get("body") or ""]),
        )
    idf_version = extract_version_from_url(idf_url, [r"/releases/download/v?([0-9][0-9A-Za-z.\-_]*)/"])
    if not arduino_version:
        raise ValueError("Could not resolve pioarduino Arduino core version")
    platform_version = platform.get("version") or release["tag_name"].lstrip("v")
    return {
        "provider": "pioarduino",
        "platform_repo": repo,
        "platform_tag": release["tag_name"],
        "platform_version": platform_version,
        "platform_release_url": release["html_url"],
        "framework_arduinoespressif32": core_url,
        "framework_arduinoespressif32_libs": libs_url,
        "arduino_core": arduino_version,
        "idf": idf_version,
        "support_branch": branch_for_arduino(arduino_version),
        "release_tag": f"pm-support-pioarduino-{platform_version}-arduino-{arduino_version}",
        "artifact_name": artifact_name("pioarduino", platform_version, arduino_version),
    }


def write_github_outputs(info):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as fp:
        for key, value in info.items():
            if isinstance(value, str):
                fp.write(f"{key}={value}\n")


def main():
    parser = argparse.ArgumentParser(description="Resolve PM support release metadata.")
    parser.add_argument("--provider", choices=["platformio", "pioarduino"], required=True)
    parser.add_argument("--tag", default="latest", help="Release tag to inspect, or 'latest'.")
    parser.add_argument("--output", help="Write the resolved manifest JSON to this path.")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    try:
        if args.provider == "platformio":
            info = official_platformio(args.tag, token)
        else:
            info = pioarduino(args.tag, token)
    except (KeyError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(info, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(rendered)
            fp.write("\n")
    write_github_outputs(info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
