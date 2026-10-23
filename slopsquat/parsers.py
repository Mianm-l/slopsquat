"""
Parsers for extracting dependency names from requirements.txt and package.json.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional

def parse_requirements_txt(filepath: str) -> List[Dict[str, Any]]:
    """
    Parses a requirements.txt file and returns a list of packages with metadata.
    """
    packages = []
    if not os.path.exists(filepath):
        return packages

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line_num, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            # Ignore empty lines and pure comments
            if not line or line.startswith("#"):
                continue

            # Strip inline comments
            if " #" in line:
                line = line.split(" #", 1)[0].strip()

            # Skip pip options like -r, -i, --extra-index-url
            if line.startswith("-") or line.startswith("--"):
                continue

            # Skip direct VCS / file URLs
            if line.startswith("git+") or line.startswith("http://") or line.startswith("https://") or line.startswith("file:"):
                continue

            # Strip environment markers (; sys_platform == 'win32')
            if ";" in line:
                line = line.split(";", 1)[0].strip()

            # Match package name (including extras like pkg[extra])
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(?:\[[^\]]+\])?(.*)$", line)
            if match:
                pkg_name = match.group(1).strip()
                version_spec = match.group(2).strip()
                packages.append({
                    "name": pkg_name,
                    "ecosystem": "pypi",
                    "spec": version_spec,
                    "line": line_num,
                    "source_file": filepath
                })

    return packages

def parse_package_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Parses a package.json file and returns a list of npm dependencies.
    """
    packages = []
    if not os.path.exists(filepath):
        return packages

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        dep_sections = ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]
        seen = set()

        for sec in dep_sections:
            deps = data.get(sec, {})
            if isinstance(deps, dict):
                for pkg_name, spec in deps.items():
                    if pkg_name in seen:
                        continue
                    seen.add(pkg_name)
                    # Skip local / git / workspace paths
                    if isinstance(spec, str) and (spec.startswith("file:") or spec.startswith("git") or spec.startswith("workspace:") or spec.startswith("link:")):
                        continue
                    packages.append({
                        "name": pkg_name,
                        "ecosystem": "npm",
                        "spec": str(spec),
                        "section": sec,
                        "source_file": filepath
                    })
    except Exception as e:
        print(f"[!] Warning: Failed to parse {filepath}: {e}")

    return packages

def detect_manifests(target_path: str) -> List[str]:
    """
    Detects dependency manifest files in a file or directory.
    """
    manifests = []
    if os.path.isfile(target_path):
        return [target_path]

    if os.path.isdir(target_path):
        for root, dirs, files in os.walk(target_path):
            # Skip hidden and cache folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", ".venv", "__pycache__", "build", "dist")]
            for f in files:
                f_lower = f.lower()
                if f_lower == "requirements.txt" or f_lower.endswith("-requirements.txt") or f_lower.endswith(".requirements.txt"):
                    manifests.append(os.path.join(root, f))
                elif f_lower == "package.json":
                    manifests.append(os.path.join(root, f))

    return manifests
