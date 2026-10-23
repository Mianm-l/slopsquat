"""
Inspectors for querying PyPI and npm official registries.
"""

import urllib.request
import urllib.error
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

USER_AGENT = "slopsquat/0.1.0 (https://github.com/Mianm-l/slopsquat; security audit)"

def inspect_pypi_package(pkg_name: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Inspects a Python package on PyPI.
    """
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)

    result = {
        "name": pkg_name,
        "ecosystem": "pypi",
        "exists": False,
        "created_at": None,
        "latest_at": None,
        "age_days": None,
        "version": None,
        "total_releases": 0,
        "has_repo": False,
        "repo_url": None,
        "author": None,
        "summary": "",
        "monthly_downloads": None,
        "error": None
    }

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result["exists"] = True

            info = data.get("info", {})
            result["version"] = info.get("version")
            result["author"] = info.get("author") or info.get("author_email")
            result["summary"] = info.get("summary") or ""

            # Check for source code repository link
            urls = []
            if info.get("project_urls"):
                urls.extend(info["project_urls"].values())
            if info.get("home_page"):
                urls.append(info["home_page"])

            for u in urls:
                if isinstance(u, str) and any(host in u.lower() for host in ("github.com", "gitlab.com", "gitee.com", "bitbucket.org")):
                    result["has_repo"] = True
                    result["repo_url"] = u
                    break

            # Analyze releases timestamps
            releases = data.get("releases", {})
            result["total_releases"] = len(releases)

            all_upload_times = []
            for ver, files in releases.items():
                for f in files:
                    up_time = f.get("upload_time_iso_8601")
                    if up_time:
                        try:
                            # Replace Z or handle timezone
                            dt = datetime.fromisoformat(up_time.replace("Z", "+00:00"))
                            all_upload_times.append(dt)
                        except Exception:
                            pass

            if all_upload_times:
                earliest = min(all_upload_times)
                latest = max(all_upload_times)
                result["created_at"] = earliest.isoformat()
                result["latest_at"] = latest.isoformat()
                now = datetime.now(timezone.utc)
                result["age_days"] = max(0, (now - earliest).days)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            result["exists"] = False
            result["error"] = "NOT_FOUND"
        else:
            result["error"] = f"HTTP_{e.code}"
    except Exception as e:
        result["error"] = str(e)

    # If package exists, attempt to fetch download stats (best effort)
    if result["exists"]:
        try:
            stats_url = f"https://pypistats.org/api/packages/{pkg_name}/recent"
            sreq = urllib.request.Request(stats_url, headers=headers)
            with urllib.request.urlopen(sreq, timeout=3) as sresp:
                sdata = json.loads(sresp.read().decode("utf-8"))
                result["monthly_downloads"] = sdata.get("data", {}).get("last_month", 0)
        except Exception:
            pass

    return result

def inspect_npm_package(pkg_name: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Inspects an npm package on registry.npmjs.org.
    """
    # URL encode scoped packages (@org/pkg -> @org%2Fpkg)
    encoded_name = pkg_name.replace("/", "%2F")
    url = f"https://registry.npmjs.org/{encoded_name}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)

    result = {
        "name": pkg_name,
        "ecosystem": "npm",
        "exists": False,
        "created_at": None,
        "latest_at": None,
        "age_days": None,
        "version": None,
        "total_releases": 0,
        "has_repo": False,
        "repo_url": None,
        "author": None,
        "summary": "",
        "monthly_downloads": None,
        "error": None
    }

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result["exists"] = True

            dist_tags = data.get("dist-tags", {})
            result["version"] = dist_tags.get("latest")
            result["summary"] = data.get("description", "")

            author = data.get("author")
            if isinstance(author, dict):
                result["author"] = author.get("name")
            elif isinstance(author, str):
                result["author"] = author

            # Check repo
            repo = data.get("repository")
            if isinstance(repo, dict):
                repo_url = repo.get("url", "")
            elif isinstance(repo, str):
                repo_url = repo
            else:
                repo_url = ""

            if any(host in repo_url.lower() for host in ("github.com", "gitlab.com", "bitbucket.org")):
                result["has_repo"] = True
                result["repo_url"] = repo_url

            # Version counts and time
            versions = data.get("versions", {})
            result["total_releases"] = len(versions)

            times = data.get("time", {})
            created_str = times.get("created")
            if created_str:
                try:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    result["created_at"] = dt.isoformat()
                    now = datetime.now(timezone.utc)
                    result["age_days"] = max(0, (now - dt).days)
                except Exception:
                    pass

            modified_str = times.get("modified")
            if modified_str:
                result["latest_at"] = modified_str

    except urllib.error.HTTPError as e:
        if e.code == 404:
            result["exists"] = False
            result["error"] = "NOT_FOUND"
        else:
            result["error"] = f"HTTP_{e.code}"
    except Exception as e:
        result["error"] = str(e)

    # If package exists, attempt to fetch monthly downloads from npm api
    if result["exists"]:
        try:
            dl_url = f"https://api.npmjs.org/downloads/point/last-month/{encoded_name}"
            dreq = urllib.request.Request(dl_url, headers=headers)
            with urllib.request.urlopen(dreq, timeout=3) as dresp:
                ddata = json.loads(dresp.read().decode("utf-8"))
                result["monthly_downloads"] = ddata.get("downloads", 0)
        except Exception:
            pass

    return result
