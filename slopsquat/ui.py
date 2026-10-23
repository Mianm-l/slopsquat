"""
Terminal user interface and formatting for SlopSquat scanner.
"""

import sys
import os

# Enable ANSI escape sequences on Windows 10/11
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}   _____ _             _____             _   
  / ____| |           / ____|           | |  
 | (___ | | ___  _ __| (___   __ _ _   _| |_ 
  \\___ \\| |/ _ \\| '_ \\\\___ \\ / _` | | | | __|
  ____) | | (_) | |_) |___) | (_| | |_| | |_ 
 |_____/|_|\\___/| .__/_____/ \\__, |\\__,_|\\__|
                | |             | |          
                |_|             |_|          {Colors.RESET}
 {Colors.DIM}v0.1.0 • AI Package Hallucination & Slopsquatting Guard{Colors.RESET}
"""
    print(banner)

def format_age(age_days):
    if age_days is None:
        return "Unknown"
    if age_days == 0:
        return "Today"
    if age_days < 30:
        return f"{age_days}d"
    if age_days < 365:
        months = age_days // 30
        return f"{months}mo"
    years = age_days / 365.0
    return f"{years:.1f}y"

def format_downloads(dl):
    if dl is None:
        return "N/A"
    if dl >= 1_000_000:
        return f"{dl / 1_000_000:.1f}M"
    if dl >= 1_000:
        return f"{dl / 1_000:.1f}K"
    return str(dl)

def print_scan_table(results):
    """
    Prints a clean overview table of scanned dependencies.
    """
    col_pkg = 26
    col_eco = 8
    col_age = 10
    col_dl = 10
    col_score = 12
    col_level = 12

    header = (
        f"{Colors.BOLD}"
        f"{'Package':<{col_pkg}} "
        f"{'Eco':<{col_eco}} "
        f"{'Age':<{col_age}} "
        f"{'Downloads':<{col_dl}} "
        f"{'Risk Score':<{col_score}} "
        f"{'Status':<{col_level}}"
        f"{Colors.RESET}"
    )

    separator = "-" * (col_pkg + col_eco + col_age + col_dl + col_score + col_level + 5)
    print(header)
    print(separator)

    for item in results:
        name = item["name"][:col_pkg-1]
        eco = item.get("ecosystem", "")[:col_eco-1]
        age = format_age(item.get("age_days"))
        dl = format_downloads(item.get("monthly_downloads"))
        score = item.get("score", 0)
        level = item.get("level", "UNKNOWN")

        # Color coding based on risk level
        if level == "CRITICAL":
            score_str = f"{Colors.RED}{Colors.BOLD}{score}/100{Colors.RESET}"
            level_str = f"{Colors.RED}{Colors.BOLD}🔴 CRITICAL{Colors.RESET}"
        elif level == "HIGH":
            score_str = f"{Colors.YELLOW}{score}/100{Colors.RESET}"
            level_str = f"{Colors.YELLOW}🟡 HIGH{Colors.RESET}"
        elif level == "MEDIUM":
            score_str = f"{Colors.CYAN}{score}/100{Colors.RESET}"
            level_str = f"{Colors.CYAN}🟠 MEDIUM{Colors.RESET}"
        else:
            score_str = f"{Colors.GREEN}{score}/100{Colors.RESET}"
            level_str = f"{Colors.GREEN}🟢 SAFE{Colors.RESET}"

        print(f"{name:<{col_pkg}} {eco:<{col_eco}} {age:<{col_age}} {dl:<{col_dl}} {score_str:<{col_score+9}} {level_str}")

    print(separator)

def print_risk_card(item):
    """
    Renders an in-depth diagnosis card for high risk items.
    """
    name = item["name"]
    level = item["level"]
    score = item["score"]
    status = item.get("status", "")
    age = format_age(item.get("age_days"))
    dl = format_downloads(item.get("monthly_downloads"))
    has_repo = "Yes (" + str(item.get("repo_url")) + ")" if item.get("has_repo") else "No (Ghost Repository)"

    box_color = Colors.RED if level == "CRITICAL" else Colors.YELLOW
    title = f" 🚨 {level} RISK DETECTED: {name} (Score: {score}/100) "

    print(f"\n{box_color}┌{'─'*68}┐{Colors.RESET}")
    print(f"{box_color}│{Colors.BOLD}{title:^68}{Colors.RESET}{box_color}│{Colors.RESET}")
    print(f"{box_color}├{'─'*68}┤{Colors.RESET}")
    print(f"{box_color}│{Colors.RESET}  • Ecosystem:     {item.get('ecosystem')}")
    print(f"{box_color}│{Colors.RESET}  • Registry Status:{status}")
    print(f"{box_color}│{Colors.RESET}  • Package Age:   {age} ({item.get('age_days')} days)")
    print(f"{box_color}│{Colors.RESET}  • Monthly DLs:   {dl}")
    print(f"{box_color}│{Colors.RESET}  • Source Repo:   {has_repo}")
    print(f"{box_color}│{Colors.RESET}")
    print(f"{box_color}│{Colors.BOLD}  🔍 Risk Indicators:{Colors.RESET}")
    for reason in item.get("reasons", []):
        print(f"{box_color}│{Colors.RESET}     - {reason}")
    print(f"{box_color}│{Colors.RESET}")
    print(f"{box_color}│{Colors.BOLD}  💡 Recommended Action:{Colors.RESET}")
    print(f"{box_color}│{Colors.RESET}     {item.get('action')}")
    print(f"{box_color}└{'─'*68}┘{Colors.RESET}\n")
