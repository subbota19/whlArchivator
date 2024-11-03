from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
from re import match as re_match, findall as re_findall
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from requests import get
from collections import defaultdict

PYTHON_VERSION = "py3"
PYPI_URN = "https://pypi.org/pypi/{}/json"
PYPI_VERSION_URN = "https://pypi.org/pypi/{}/{}/json"
PACKAGE_PATTERN = r"([a-zA-Z0-9_\-]+(?:\[[^\]]+\])?)(.*)"


def get_compatible_version(package_name: str, version_specifier: str) -> str:
    file_info = extract_meta_info(
        package_name=package_name
    )

    releases = file_info.get("releases")

    available_versions = sorted(
        (Version(v) for v in releases if not any(_.isalpha() for _ in v)),
        reverse=True
    )
    compatible_versions = [v for v in available_versions if v in SpecifierSet(version_specifier)]

    if not compatible_versions:
        raise ValueError(f"No compatible version found for {package_name} with specifier {version_specifier}")

    return compatible_versions[0].base_version


def resolve_dependencies(dependencies: Iterable) -> {}:
    dependency_graph = {}

    for dep in dependencies:
        package_name, version_specifier = dep[0], dep[1]

        if package_name == "mashumaro[msgpack]":
            package_name = "mashumaro"

        compatible_version = get_compatible_version(
            package_name=package_name,
            version_specifier=version_specifier
        )

        dependency_graph[package_name] = compatible_version

    return dependency_graph


def split_package_name(package: str, package_pattern: str = PACKAGE_PATTERN) -> tuple:
    match = re_match(package_pattern, package)

    if not match:
        raise ValueError(f"Invalid dependency format: {package}")

    return match.group(1), match.group(2)


def extract_meta_info(package_name: str, version: str = None) -> dict:
    pypi_url = PYPI_URN.format(package_name) if version is None else PYPI_VERSION_URN.format(package_name, version)
    response = get(pypi_url)
    response.raise_for_status()
    return response.json()


def download_whl(package_name: str, version: str, output_path: Path) -> list:
    file_info = extract_meta_info(
        package_name=package_name,
        version=version
    )

    whl_urls_meta = file_info.get("urls", ())
    info_meta = file_info.get("info", {})
    requires_dist = info_meta.get("requires_dist", [])

    for whl_url_meta in whl_urls_meta:
        python_version = whl_url_meta.get("python_version")
        if python_version == PYTHON_VERSION:
            url = whl_url_meta.get("url")
            filename = whl_url_meta.get("filename")
            print(f"Downloading {filename}...")
            whl_data = get(url)
            whl_data.raise_for_status()
            with open(output_path / filename, "wb") as file:
                file.write(whl_data.content)

    return requires_dist


def download_dependencies(output_path: Path, packages: tuple = ()) -> list:
    output_path.mkdir(parents=True, exist_ok=True)

    depend = []

    for package_name, version in packages:
        try:
            print(f"Processing {package_name}=={version}...")
            dist = download_whl(package_name, version, output_path)
            depend.extend(dist)
        except Exception as e:
            print(f"Failed to download {package_name}=={version}: {e}")
            continue

    print(f"All packages and dependencies downloaded to {output_path}")
    return depend


def parse_requirement(requirement_path: str) -> list:
    packages = []

    if requirement_path is not None:

        with open(requirement_path, "r") as req_file:

            for line in req_file.readlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    match = re_match(r"(\S+)==([\d.]+)", line)
                    if match:
                        packages.append(match.groups())

    return packages


def parse_args():
    parser = ArgumentParser(description="Generate .whl files.")

    parser.add_argument(
        "--requirement_path",
        help="Path to the directory containing the initial .whl files"
    )
    parser.add_argument(
        "--output_path",
        help="Path to the directory to store downloaded dependencies and requirements.txt"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    output_path_arg = Path(args.output_path)
    requirement_path_arg = args.requirement_path

    parsed_packages = parse_requirement(
        requirement_path=requirement_path_arg
    )

    raw_dependencies = download_dependencies(
        output_path=output_path_arg,
        packages=tuple(parsed_packages)
    )

    parsed_dependencies = (
        split_package_name(dependency) for dependency in raw_dependencies
    )

    inner_dependencies = resolve_dependencies(
        dependencies=parsed_dependencies
    )

    _ = download_dependencies(
        output_path=output_path_arg,
        packages=tuple((k, v) for k, v in inner_dependencies.items())
    )
