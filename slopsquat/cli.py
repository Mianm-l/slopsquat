"""
Main CLI entrypoint for SlopSquat.
"""

import sys
import os
import argparse
import json
from typing import List, Dict, Any

from .parsers import parse_requirements_txt, parse_package_json, detect_manifests
from .scanner import scan_packages_concurrent
from .ui import print_banner, print_scan_table, print_risk_card, Colors

def main():
    parser = argparse.ArgumentParser(
        prog="slopsquat",
        description="SlopSquat: AI Package Hallucination & Slopsquatting Guard."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Path to requirements.txt, package.json, or directory to scan (default: current directory)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON results for CI/CD integration."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Risk score threshold to trigger failure exit code (default: 80)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: exit with error if ANY package scores >= 50 (HIGH or CRITICAL)."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent network workers (default: 10)."
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated package names to whitelist/ignore."
    )

    args = parser.parse_args()

    # Reconfigure stdout for UTF-8 on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if not args.json:
        print_banner()

    target_path = os.path.abspath(args.target)
    manifests = detect_manifests(target_path)

    if not manifests:
        if not args.json:
            print(f"{Colors.YELLOW}[!] No requirements.txt or package.json found in: {target_path}{Colors.RESET}")
            print(f"{Colors.DIM}Usage: slopsquat <path/to/requirements.txt|package.json|folder>{Colors.RESET}\n")
        sys.exit(0)

    # Collect packages from all detected manifests
    all_packages: List[Dict[str, Any]] = []
    for mf in manifests:
        mf_lower = os.path.basename(mf).lower()
        if "package.json" in mf_lower:
            all_packages.extend(parse_package_json(mf))
        else:
            all_packages.extend(parse_requirements_txt(mf))

    if not all_packages:
        if not args.json:
            print(f"{Colors.GREEN}[✓] Manifests found, but no external dependencies detected.{Colors.RESET}")
        sys.exit(0)

    # Filter ignored packages and deduplicate
    ignored_names = set(p.strip().lower() for p in args.ignore.split(",") if p.strip())
    dedup_packages = []
    seen = set()

    for p in all_packages:
        key = (p["ecosystem"], p["name"].lower())
        if key in seen or p["name"].lower() in ignored_names:
            continue
        seen.add(key)
        dedup_packages.append(p)

    if not args.json:
        print(f"🔍 Discovered {len(manifests)} manifest(s), inspecting {len(dedup_packages)} unique package(s)...")

    results = scan_packages_concurrent(dedup_packages, max_workers=args.workers)

    if args.json:
        output_data = {
            "target": target_path,
            "manifests": manifests,
            "total_packages": len(results),
            "results": results
        }
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
        # Exit code determination
        fail_threshold = 50 if args.strict else args.threshold
        has_failure = any(r.get("score", 0) >= fail_threshold for r in results)
        sys.exit(1 if has_failure else 0)

    # Print Table
    print()
    print_scan_table(results)
    print()

    # Detailed Cards for High / Critical risks
    risky_items = [r for r in results if r.get("score", 0) >= 50]
    if risky_items:
        print(f"{Colors.BOLD}🚨 High Risk / Hallucination Diagnosis Details:{Colors.RESET}")
        for item in risky_items:
            print_risk_card(item)

    # Summary Stats
    total = len(results)
    critical_count = sum(1 for r in results if r.get("level") == "CRITICAL")
    high_count = sum(1 for r in results if r.get("level") == "HIGH")
    medium_count = sum(1 for r in results if r.get("level") == "MEDIUM")
    safe_count = sum(1 for r in results if r.get("level") == "SAFE")

    print(f"{Colors.BOLD}📊 Scan Summary:{Colors.RESET}")
    print(f"   • Total Inspected: {total}")
    print(f"   • {Colors.GREEN}Safe:{Colors.RESET}           {safe_count}")
    print(f"   • {Colors.CYAN}Medium Risk:{Colors.RESET}    {medium_count}")
    print(f"   • {Colors.YELLOW}High Risk:{Colors.RESET}      {high_count}")
    print(f"   • {Colors.RED}Critical Risk:{Colors.RESET}  {critical_count}")
    print()

    fail_threshold = 50 if args.strict else args.threshold
    failed_items = [r for r in results if r.get("score", 0) >= fail_threshold]

    if failed_items:
        print(f"{Colors.RED}{Colors.BOLD}❌ [ALERT] Found {len(failed_items)} package(s) exceeding risk threshold ({fail_threshold})!{Colors.RESET}")
        print(f"{Colors.RED}Please review suspected dependencies before installing or merging.{Colors.RESET}\n")
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ [PASS] All scanned dependencies passed SlopSquat safety checks!{Colors.RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
