"""
Concurrent scanning orchestrator for SlopSquat.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional

from .inspector import inspect_pypi_package, inspect_npm_package
from .scorer import evaluate_package_risk

def scan_package(pkg_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspects and scores a single package.
    """
    name = pkg_info["name"]
    ecosystem = pkg_info.get("ecosystem", "pypi")

    if ecosystem == "npm":
        inspected = inspect_npm_package(name)
    else:
        inspected = inspect_pypi_package(name)

    evaluated = evaluate_package_risk(inspected)
    # Merge source metadata
    evaluated["source_file"] = pkg_info.get("source_file")
    evaluated["spec"] = pkg_info.get("spec")
    return evaluated

def scan_packages_concurrent(
    packages: List[Dict[str, Any]],
    max_workers: int = 10,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Concurrently scans multiple packages.
    """
    results = []
    total = len(packages)

    if total == 0:
        return results

    completed_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pkg = {
            executor.submit(scan_package, pkg): pkg
            for pkg in packages
        }

        for future in as_completed(future_to_pkg):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                pkg = future_to_pkg[future]
                results.append({
                    "name": pkg["name"],
                    "ecosystem": pkg.get("ecosystem"),
                    "score": 0,
                    "level": "UNKNOWN",
                    "status": "SCAN_EXCEPTION",
                    "reasons": [str(e)],
                    "action": "Retry"
                })
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total, pkg["name"])

    # Sort results by score descending (highest risk first)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
