from __future__ import annotations

import base64
import hashlib
import pathlib
import tomllib
import zipfile
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parent


def _load_project() -> dict:
    pyproject_path = ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data["project"]


def _top_level_packages() -> list[str]:
    src_root = ROOT / "src"
    packages = []
    for path in src_root.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            packages.append(path.name)
    return sorted(packages)


def _metadata_lines(project: dict) -> list[str]:
    name = project["name"]
    version = project["version"]
    summary = project.get("description", "")
    requires_python = project.get("requires-python")
    dependencies = project.get("dependencies", [])
    optional_dependencies = project.get("optional-dependencies", {})

    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
    ]
    if summary:
        lines.append(f"Summary: {summary}")
    if requires_python:
        lines.append(f"Requires-Python: {requires_python}")

    for req in dependencies:
        lines.append(f"Requires-Dist: {req}")

    for extra, reqs in optional_dependencies.items():
        lines.append(f"Provides-Extra: {extra}")
        for req in reqs:
            lines.append(f"Requires-Dist: {req}; extra == '{extra}'")

    lines.append("")
    return lines


def _dist_info(project: dict) -> str:
    name = project["name"].replace("-", "_")
    version = project["version"]
    return f"{name}-{version}.dist-info"


def _wheel_metadata(project: dict) -> dict[str, bytes]:
    dist_info = _dist_info(project)
    metadata = "\n".join(_metadata_lines(project)).encode("utf-8")
    wheel = (
        "Wheel-Version: 1.0\n"
        "Generator: build_backend\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("utf-8")
    top_level = "\n".join(_top_level_packages()).encode("utf-8") + b"\n"

    return {
        f"{dist_info}/METADATA": metadata,
        f"{dist_info}/WHEEL": wheel,
        f"{dist_info}/top_level.txt": top_level,
    }


def _hash_bytes(data: bytes) -> tuple[str, int]:
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"sha256={encoded}", len(data)


def _record_lines(files: Iterable[tuple[str, bytes]], dist_info: str) -> bytes:
    lines = []
    for path, data in files:
        digest, size = _hash_bytes(data)
        lines.append(f"{path},{digest},{size}")
    lines.append(f"{dist_info}/RECORD,,")
    return "\n".join(lines).encode("utf-8")


def _build_wheel(project: dict, wheel_directory: str, editable: bool) -> str:
    name = project["name"].replace("-", "_")
    version = project["version"]
    wheel_name = f"{name}-{version}-py3-none-any.whl"
    dist_info = _dist_info(project)

    file_map: dict[str, bytes] = {}
    file_map.update(_wheel_metadata(project))

    if editable:
        src_path = ROOT / "src"
        pth_contents = f"{src_path}\n".encode("utf-8")
        file_map[f"{name}.pth"] = pth_contents
    else:
        src_root = ROOT / "src"
        for path in src_root.rglob("*.py"):
            rel_path = path.relative_to(src_root)
            file_map[str(rel_path)] = path.read_bytes()

    record = _record_lines(file_map.items(), dist_info)
    file_map[f"{dist_info}/RECORD"] = record

    wheel_path = pathlib.Path(wheel_directory)
    wheel_path.mkdir(parents=True, exist_ok=True)
    out_path = wheel_path / wheel_name

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, data in file_map.items():
            zf.writestr(path, data)

    return wheel_name


def build_wheel(
    wheel_directory: str,
    config_settings: dict | None = None,
    metadata_directory: str | None = None,
) -> str:
    project = _load_project()
    return _build_wheel(project, wheel_directory, editable=False)


def build_editable(
    wheel_directory: str,
    config_settings: dict | None = None,
    metadata_directory: str | None = None,
) -> str:
    project = _load_project()
    return _build_wheel(project, wheel_directory, editable=True)


def get_requires_for_build_wheel(config_settings: dict | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(
    config_settings: dict | None = None,
) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict | None = None,
) -> str:
    project = _load_project()
    dist_info = _dist_info(project)
    dest = pathlib.Path(metadata_directory) / dist_info
    dest.mkdir(parents=True, exist_ok=True)
    metadata_files = _wheel_metadata(project)
    for rel_path, data in metadata_files.items():
        target = pathlib.Path(metadata_directory) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return dist_info
