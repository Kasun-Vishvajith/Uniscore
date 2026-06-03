import csv
import sys
import re
import time
import unicodedata
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


# ANSI Escape Colors and 24-bit TrueColor Helpers
def safe_exit(code=0):
    """Wait for user input before exiting to prevent terminal closing immediately."""
    try:
        input(f"\n{CLR_DIM}Press Enter to exit...{CLR_RESET}")
    except (KeyboardInterrupt, EOFError):
        pass
    sys.exit(code)

def hex_color(hex_str: str) -> str:
    h = hex_str.lstrip('#')
    r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"\033[38;2;{r};{g};{b}m"

CLR_HEADER = "\033[95m"   # Light magenta
CLR_BOLD = "\033[1m"
CLR_RESET = "\033[0m"

# Hex Colors from HTML CLI Theme
CLR_CYAN = hex_color("#56d4e8")
CLR_GREEN = hex_color("#56e87a")
CLR_BLUE = hex_color("#7aa2f7")
CLR_YELLOW = hex_color("#f0c060")
CLR_RED = hex_color("#e8566a")
CLR_WHITE = hex_color("#eef0f5")
CLR_DIM = hex_color("#6b7594")
CLR_PURPLE = hex_color("#bb9af7")
CLR_ORANGE = hex_color("#ff9e64")
CLR_SEPARATOR = hex_color("#3a3f5c")

def get_display_width(s: str) -> int:
    """Calculate the display width of a string in a terminal, accounting for emojis, hyperlinks, and ANSI escapes."""
    ansi_escape = re.compile(r'\033\[[0-9;]*m')
    hyperlink_escape = re.compile(r'\033\]8;.*?\033\\')
    clean_s = ansi_escape.sub("", s)
    clean_s = hyperlink_escape.sub("", clean_s)
    
    width = 0
    for idx, char in enumerate(clean_s):
        if char == '\ufe0f':
            continue
        
        # Check if this character is followed by U+FE0F (VS16)
        has_vs16 = (idx + 1 < len(clean_s) and clean_s[idx + 1] == '\ufe0f')
        
        if char == '♻':
            width += 2
            continue
        if char == '⚡':
            width += 2
            continue
        if char == '⚠':
            if has_vs16:
                width += 2
            else:
                width += 1
            continue
            
        eaw = unicodedata.east_asian_width(char)
        if eaw in ('W', 'F'):
            width += 2
        elif eaw == 'A':
            # Box-drawing characters and Block Elements (U+2500 to U+259F) should be counted as 1 cell
            if 0x2500 <= ord(char) <= 0x259f:
                width += 1
            elif char in ("✓", "✔", "·", "✗", "✘"):
                width += 1
            else:
                width += 2
        else:
            width += 1
    return width


def pad_visible(plain_text: str, target_width: int) -> str:
    """Pad plain text to target_width using get_display_width to support unicode/emojis."""
    w = get_display_width(plain_text)
    padding = max(0, target_width - w)
    return plain_text + (" " * padding)


def print_logo():
    logo_data = [
        # Row 0
        {4: "#a855f7"},
        # Row 1
        {3: "#7c6cf7", 5: "#7aa2f7"},
        # Row 2
        {2: "#4d96ff", 4: "#56d4e8", 6: "#6bcb77"},
        # Row 3
        {1: "#6bcb77", 3: "#9ee060", 5: "#ffd93d", 7: "#ffbd2e"},
        # Row 4
        {0: "#ff9e64", 2: "#ff9e64", 4: "#ff7b7b", 6: "#ff6b6b", 8: "#e8566a"},
        # Row 5
        {0: "#ff6b6b", 1: "#ff7b7b", 7: "#e8566a", 8: "#c0392b"},
        # Row 6
        {0: "#c0392b", 1: "#e8566a", 8: "#a93226"},
        # Row 7
        {0: "#922b21", 1: "#c0392b", 8: "#7b241c"}
    ]
    width = 90
    logo_width = 18  # 9 columns * 2 characters each
    padding = (width - logo_width) // 2
    for row in logo_data:
        line_chars = []
        for col in range(9):
            if col in row:
                line_chars.append(f"{hex_color(row[col])}██{CLR_RESET}")
            else:
                line_chars.append("  ")
        print(" " * padding + "".join(line_chars))


def init_ansi():
    """Enable virtual terminal processing on Windows to support ANSI color codes."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
            if hOut != -1:
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(hOut, mode.value | 0x0004) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            pass


def get_masked_password(prompt="Password: ") -> str:
    """Prompt for a password and mask the input with asterisks (*) in the CLI (Windows support)."""
    try:
        import msvcrt
        sys.stdout.write(prompt)
        sys.stdout.flush()
        password = []
        while True:
            ch = msvcrt.getch()
            if ch in (b'\r', b'\n'):
                sys.stdout.write('\n')
                sys.stdout.flush()
                break
            elif ch == b'\x08':  # Backspace
                if len(password) > 0:
                    password.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == b'\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                try:
                    char = ch.decode('utf-8')
                    # Exclude non-printable control characters
                    if ord(char) >= 32:
                        password.append(char)
                        sys.stdout.write(f'{CLR_CYAN}*{CLR_RESET}')
                        sys.stdout.flush()
                except UnicodeDecodeError:
                    pass
        return "".join(password)
    except ImportError:
        import getpass
        return getpass.getpass(prompt)


BASE_URL = "https://sis.cmb.ac.lk/sci"
LOGIN_URL = f"{BASE_URL}/index"
AJAX_LOGIN = f"{BASE_URL}/ajax.php?req=login"
LOGOUT_URL = f"{BASE_URL}/ajax.php?req=logout"
RESULTS_URL = f"{BASE_URL}/results/result_sheet"
OUTPUT_FILE = "results.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Referer": LOGIN_URL,
}


def login(session: requests.Session, username: str, password: str) -> tuple[bool, str]:
    """Log in and return (True, "") on success, or (False, error_msg) on failure."""
    r = session.get(LOGIN_URL, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    payload = {}
    for inp in soup.find_all("input", type="hidden"):
        if inp.get("name"):
            payload[inp["name"]] = inp.get("value", "")

    payload["uname"] = username
    payload["pw"] = password

    r = session.post(AJAX_LOGIN, data=payload, headers=HEADERS)
    r.raise_for_status()

    soup2 = BeautifulSoup(r.text, "html.parser")
    title = soup2.title.string if soup2.title else ""

    if "Faculty of Science | Student Information System" in title:
        return True, ""

    err = soup2.find(class_="error")
    err_text = err.get_text(strip=True) if err else "Invalid username or password."
    return False, err_text


def parse_results(html: str) -> list[dict]:
    """Parse all result tables and return a flat list of course dicts."""
    soup = BeautifulSoup(html, "html.parser")
    all_rows = []

    for table in soup.find_all("table", class_="data-table"):
        # The thead has 2 rows:
        #   row 0 → section title e.g. "Level 1 - Semester 1"  (colspan=11)
        #   row 1 → actual column headers: #, Level, Course Unit, ...
        thead_rows = table.find("thead").find_all("tr") if table.find("thead") else []
        if len(thead_rows) < 2:
            continue

        # Get clean column names from the second header row
        col_headers = [th.get_text(strip=True) for th in thead_rows[1].find_all("th")]
        if "Grade" not in col_headers:
            continue

        # Get FULL section label — may contain semester info
        section = (
            thead_rows[0].find("th").get_text(strip=True)
            if thead_rows[0].find("th")
            else ""
        )

        # Try to extract semester directly from section label
        # e.g. "Level 1 - Semester 1", "Level 1 (Sem 2)", "Year 1 S1", etc.
        inferred_sem = ""
        sec_lower = section.lower()
        if re.search(r'sem(?:ester)?[\s\-_]*1|s1\b|\b1st\s*sem', sec_lower):
            inferred_sem = "Sem 1"
        elif re.search(r'sem(?:ester)?[\s\-_]*2|s2\b|\b2nd\s*sem', sec_lower):
            inferred_sem = "Sem 2"

        tbody = table.find("tbody")
        if not tbody:
            continue

        for tr in tbody.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cols or len(cols) < len(col_headers):
                continue
            row = dict(zip(col_headers, cols))
            row["Section"] = section
            row["_sem"] = inferred_sem  # pre-extracted semester (may be empty)
            all_rows.append(row)

    return all_rows



def center_line(content: str, width: int, fill: str = " ") -> str:
    """Center visible content inside a fixed terminal width, ignoring ANSI codes."""
    visible = get_display_width(content)
    padding = max(0, width - visible)
    left = padding // 2
    right = padding - left
    return fill * left + content + fill * right


def box_top(width: int) -> str:
    return f"{CLR_SEPARATOR}┌{'─' * (width - 2)}┐{CLR_RESET}"

def box_mid(width: int) -> str:
    return f"{CLR_SEPARATOR}├{'─' * (width - 2)}┤{CLR_RESET}"

def box_bot(width: int) -> str:
    return f"{CLR_SEPARATOR}└{'─' * (width - 2)}┘{CLR_RESET}"

def box_row(content: str, width: int) -> str:
    """Print a bordered row with content inside, auto-centered."""
    inner_width = width - 4  # 2 for border chars + 2 for spaces
    centred = center_line(content, inner_width)
    return f"{CLR_SEPARATOR}│{CLR_RESET} {centred} {CLR_SEPARATOR}│{CLR_RESET}"

def box_row_left(content: str, width: int) -> str:
    """Print a bordered row, left-padded with 2 spaces."""
    visible_len = get_display_width(content)
    pad = max(0, width - 6 - visible_len)
    return f"{CLR_SEPARATOR}│{CLR_RESET}  {content}{' ' * pad}  {CLR_SEPARATOR}│{CLR_RESET}"

def box_row_split(left_content: str, right_content: str, width: int) -> str:
    """Print a bordered row split left/right with a mid divider."""
    mid = width // 2
    left_vis = get_display_width(left_content)
    right_vis = get_display_width(right_content)
    left_pad = max(0, mid - left_vis - 3)
    right_pad = max(0, width - mid - right_vis - 6)
    return (
        f"{CLR_SEPARATOR}│{CLR_RESET}  {left_content}{' ' * left_pad}"
        f"{CLR_SEPARATOR}│{CLR_RESET}  {right_content}{' ' * right_pad}  {CLR_SEPARATOR}│{CLR_RESET}"
    )


def resolve_course_attempts(rows: list[dict]) -> list[dict]:
    """
    Applies academic grade and credit calculation logic rules:
    - Rule 1: Medical Attempt gets GPV = 0.0 if not re-sat (no subsequent attempt).
    - Rule 2: Medical Attempt negated (voided) if there is any subsequent attempt.
    - Rule 3 & 4: Only the final/active attempt contributes credits/GPA weight.
    - Repeat Cap: Capping standard repeated passing attempts at 2.0 GPV.
    """
    from collections import defaultdict
    course_map = defaultdict(list)
    for idx, row in enumerate(rows):
        code = row.get("Course Unit", "").strip()
        if code:
            course_map[code].append((idx, row))
            
    resolved_rows = [dict(row) for row in rows]
    for code, atts in course_map.items():
        n = len(atts)
        had_fail = False
        for i, (idx, row) in enumerate(atts):
            grade = row.get("Grade", "").strip().upper()
            is_last = (i == n - 1)
            
            resolved_rows[idx]["_is_voided"] = False
            resolved_rows[idx]["_gpv_override"] = None
            resolved_rows[idx]["_credits_override"] = None
            
            if is_last:
                if grade == 'MC':
                    resolved_rows[idx]["_gpv_override"] = 0.0
                elif had_fail:
                    if classify_grade(grade) == 'pass':
                        orig_gpv = float(row.get("GPV", 0.0) or 0.0)
                        if orig_gpv > 2.0:
                            resolved_rows[idx]["_gpv_override"] = 2.0
            else:
                resolved_rows[idx]["_is_voided"] = True
                resolved_rows[idx]["_credits_override"] = 0.0
                
            if classify_grade(grade) in ('fail', 'absent'):
                had_fail = True
                
    return resolved_rows


def print_summary(rows: list[dict]) -> str:
    """Print a structured GPA summary and return a clean borderless text summary string."""
    WIDTH = 90  # Total box width
    output_lines = []

    def output(line):
        print(line)
        output_lines.append(line)

    # ── Semester detection ────────────────────────────────────────
    def infer_semester(course_code: str, section: str, row: dict) -> str:
        """Multi-stage semester detection: stored value → row column → section label → course code."""
        pre = row.get("_sem", "").strip()
        if pre:
            return pre

        for key in ("Semester", "Sem", "Period", "Term", "semester"):
            val = row.get(key, "").strip()
            if val:
                if "1" in val:
                    return "Sem 1"
                if "2" in val:
                    return "Sem 2"

        sec = section.lower()
        if re.search(r'sem(?:ester)?[\s\-_]*1|s1\b|\b1st\s*sem', sec):
            return "Sem 1"
        if re.search(r'sem(?:ester)?[\s\-_]*2|s2\b|\b2nd\s*sem', sec):
            return "Sem 2"

        code = course_code.strip().upper()
        nums = re.findall(r'\d+', code)
        if nums:
            n = nums[0]
            if len(n) >= 4:
                s = int(n[1])
                return "Sem 1" if s <= 1 else "Sem 2"
            elif len(n) == 3:
                s = int(n[1])
                return "Sem 1" if s <= 1 else "Sem 2"

        return "Sem 1"  # safe default

    # ── Data collection ───────────────────────────────────────────
    levels = defaultdict(lambda: defaultdict(list))
    seen_sections = set()

    resolved_rows = resolve_course_attempts(rows)

    for row in resolved_rows:
        code    = row.get("Course Unit", "")
        grade   = row.get("Grade", "")
        section = row.get("Section", "")
        seen_sections.add(section)

        if "enhancement" in section.lower() or "enchancement" in section.lower():
            continue
        if row.get("_is_voided"):
            continue
        if grade in ('S', 'H', 'U', 'W', 'I', '--', ''):
            continue
        if grade.upper() == 'MC' and row.get("_is_voided"):
            continue
        try:
            gpv_val = row.get("GPV")
            if row.get("_gpv_override") is not None:
                gpv = row["_gpv_override"]
            elif gpv_val in ("", None, "--"):
                continue
            else:
                gpv = float(gpv_val)

            if row.get("_credits_override") is not None:
                cred = row["_credits_override"]
            else:
                cred = float(row.get("Credits", 0) or 0)

            level = row.get("Level", "?")
            if cred > 0 or (grade.upper() == 'MC' and not row.get("_is_voided")):
                sem = infer_semester(code, section, row)
                levels[level][sem].append((gpv, cred))
        except ValueError:
            continue

    # ── Print header ─────────────────────────────────────────────
    print()
    time.sleep(0.2)
    output(box_top(WIDTH))
    title = f"{CLR_PURPLE}{CLR_BOLD}💜  SIS SUMMARY  ·  University of Colombo{CLR_RESET}"
    output(box_row(title, WIDTH))
    output(box_mid(WIDTH))

    all_points_total, all_credits_total = 0, 0
    level_bar_colors = {"1": CLR_CYAN, "2": CLR_GREEN, "3": CLR_BLUE}

    txt_summary = []
    txt_summary.append("University of Colombo - SIS Summary")
    txt_summary.append("=" * 35)

    for level_key in sorted(levels.keys()):
        sems = levels[level_key]

        yr_pts = sum(g * c for sem_data in sems.values() for g, c in sem_data)
        yr_cred = sum(c for sem_data in sems.values() for _, c in sem_data)
        yr_gpa = yr_pts / yr_cred if yr_cred else 0

        if yr_cred < 24:
            cred_color = CLR_RED
            status_tag = f" {CLR_RED}[Incomplete]{CLR_RESET}"
        elif yr_cred < 30:
            cred_color = CLR_YELLOW
            status_tag = f" {CLR_YELLOW}[Incomplete]{CLR_RESET}"
        else:
            cred_color = CLR_GREEN
            status_tag = ""

        bar_color = level_bar_colors.get(level_key, CLR_WHITE)

        # ── Year header row ───────────────────────────────────────
        year_lbl = f"{CLR_WHITE}{CLR_BOLD}Year / Level {level_key}{CLR_RESET}"
        cred_info = f"{cred_color}{int(yr_cred)} credits{CLR_RESET}{status_tag}"
        output(box_row_split(year_lbl, cred_info, WIDTH))

        txt_summary.append(f"\nYear / Level {level_key}: {int(yr_cred)} credits")

        # ── Per-semester rows ─────────────────────────────────────
        for sem_key in sorted(sems.keys()):
            sem_data = sems[sem_key]
            s_pts = sum(g * c for g, c in sem_data)
            s_cred = sum(c for _, c in sem_data)
            s_gpa = s_pts / s_cred if s_cred else 0

            sem_label = f"  {CLR_DIM}└─ {sem_key:<6}{CLR_RESET}"
            gpa_val = f"{CLR_CYAN}{s_gpa:.2f}{CLR_RESET}"
            crd_val = f"{CLR_DIM}({int(s_cred)} cr){CLR_RESET}"
            sem_content = f"{sem_label}  GPA {gpa_val}  {crd_val}"
            output(box_row_left(sem_content, WIDTH))

            txt_summary.append(f"  {sem_key} GPA: {s_gpa:.2f} ({int(s_cred)} cr)")

        # ── Animated Year GPA bar ─────────────────────────────────
        bar_length = 16
        target = int(round((yr_gpa / 4.0) * bar_length))
        target = max(0, min(bar_length, target))

        yr_gpa_lbl = f"  {CLR_WHITE}Year {level_key} GPA{CLR_RESET}  "
        yr_gpa_val = f"{bar_color}{CLR_BOLD}{yr_gpa:.3f}{CLR_RESET}"

        for i in range(target + 1):
            filled = f"{bar_color}{'█' * i}{CLR_RESET}"
            empty  = f"{CLR_SEPARATOR}{'░' * (bar_length - i)}{CLR_RESET}"
            bar_str = f"{CLR_SEPARATOR}▕{CLR_RESET}{filled}{empty}{CLR_SEPARATOR}▏{CLR_RESET}"
            line_content = f"{yr_gpa_lbl}{yr_gpa_val}  {bar_str}"
            sys.stdout.write(f"\r{box_row_left(line_content, WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.03)
        print()
        output_lines.append(box_row_left(line_content, WIDTH))

        txt_summary.append(f"  Year {level_key} GPA: {yr_gpa:.3f}")

        all_points_total += yr_pts
        all_credits_total += yr_cred
        output(box_mid(WIDTH))
        time.sleep(0.12)

    # ── Overall GPA ───────────────────────────────────────────────
    if all_credits_total:
        overall_gpa = all_points_total / all_credits_total
        ov_bar_len = 16
        ov_target = int(round((overall_gpa / 4.0) * ov_bar_len))
        ov_target = max(0, min(ov_bar_len, ov_target))

        ov_lbl = f"  {CLR_WHITE}{CLR_BOLD}Cumulative GPA{CLR_RESET}  "
        ov_val = f"{CLR_YELLOW}{CLR_BOLD}{overall_gpa:.4f}{CLR_RESET}"
        total_cr_lbl = f"  {CLR_DIM}Total: {int(all_credits_total)} credits{CLR_RESET}"

        for i in range(ov_target + 1):
            filled = f"{CLR_YELLOW}{'█' * i}{CLR_RESET}"
            empty  = f"{CLR_SEPARATOR}{'░' * (ov_bar_len - i)}{CLR_RESET}"
            bar_str = f"{CLR_SEPARATOR}▕{CLR_RESET}{filled}{empty}{CLR_SEPARATOR}▏{CLR_RESET}"
            line_content = f"{ov_lbl}{ov_val}  {bar_str}"
            sys.stdout.write(f"\r{box_row_left(line_content, WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.03)
        print()
        output_lines.append(box_row_left(line_content, WIDTH))

        output(box_row_left(total_cr_lbl, WIDTH))

        txt_summary.append(f"\nCumulative GPA: {overall_gpa:.4f}")
        txt_summary.append(f"Total: {int(all_credits_total)} credits")

    # ── Enhancement Courses ───────────────────────────────────────
    enh_rows = [
        r for r in rows
        if 'enhancement' in r.get('Section', '').lower()
        or 'enchancement' in r.get('Section', '').lower()
    ]
    if enh_rows:
        output(box_mid(WIDTH))
        enh_title = f"{CLR_PURPLE}{CLR_BOLD}\U0001f393  ENHANCEMENT COURSES{CLR_RESET}"
        output(box_row(enh_title, WIDTH))
        output(box_mid(WIDTH))
        # Column header
        hdr = f"{CLR_DIM}{'Code':<10}  {'Title':<28}  {'Cr':>3}  {'Grade'}{CLR_RESET}"
        output(box_row_left(hdr, WIDTH))
        sep = f"{CLR_SEPARATOR}{'\u2500'*10}  {'\u2500'*28}  {'\u2500'*3}  {'\u2500'*6}{CLR_RESET}"
        output(box_row_left(sep, WIDTH))
        total_enh_cr = 0
        for er in enh_rows:
            ec  = er.get('Course Unit', '')
            et  = er.get('Course Title', '')
            eg  = er.get('Grade', '')
            try:
                ecr = float(er.get('Credits', 0) or 0)
            except ValueError:
                ecr = 0
            total_enh_cr += ecr
            ec_s  = f"{CLR_CYAN}{ec:<10}{CLR_RESET}"
            et_s  = f"{CLR_WHITE}{et[:28]:<28}{CLR_RESET}"
            ecr_s = f"{CLR_DIM}{int(ecr):>3}{CLR_RESET}"
            eg_s  = f"{CLR_GREEN}{eg}{CLR_RESET}"
            output(box_row_left(f"{ec_s}  {et_s}  {ecr_s}  {eg_s}", WIDTH))
        output(box_mid(WIDTH))
        enh_sum = (
            f"{CLR_WHITE}{CLR_BOLD}{len(enh_rows)} course(s){CLR_RESET}"
            f"  {CLR_SEPARATOR}\u00b7{CLR_RESET}  "
            f"{CLR_YELLOW}{int(total_enh_cr)} enhancement credits earned{CLR_RESET}"
        )
        output(box_row_left(enh_sum, WIDTH))
        txt_summary.append(f"\nEnhancement Courses: {len(enh_rows)} course(s), {int(total_enh_cr)} credits")

    time.sleep(0.2)
    return "\n".join(txt_summary) + "\n"


# ── Grade classification ──────────────────────────────────────────────────────
PASS_GRADES = frozenset({'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'S', 'H', 'M'})
FAIL_GRADES = frozenset({'C-', 'D+', 'D', 'E'})


def classify_grade(grade: str) -> str:
    """Return 'pass', 'fail', 'medical', 'absent', or 'pending' for a grade string."""
    g = grade.strip()
    if g in PASS_GRADES:
        return 'pass'
    if g in FAIL_GRADES:
        return 'fail'
    if g.upper() == 'MC':
        return 'medical'
    if g.upper() == 'AB':
        return 'absent'
    return 'pending'  # --, '', W, I, U, etc.


def get_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def find_repeated_courses(rows: list[dict]) -> list[dict]:
    """
    Find courses whose Course Unit code appears more than once and are standard repeats (not medical).
    If the first attempt was a medical attempt (MC), it's a medical resit, not a repeat.
    """
    from collections import defaultdict
    resolved_rows = resolve_course_attempts(rows)
    course_map: dict[str, list] = defaultdict(list)
    for row in resolved_rows:
        code = row.get('Course Unit', '').strip()
        if code:
            course_map[code].append(row)

    result = []
    for code, attempts in course_map.items():
        if len(attempts) < 2:
            continue
        first_grade = attempts[0].get('Grade', '').strip().upper()
        if first_grade == 'MC':
            continue  # Medical resit, not a standard repeat
            
        title  = attempts[0].get('Course Title', code)
        attempt_details = []
        for idx, att in enumerate(attempts):
            grade = att.get('Grade', '').strip()
            cls_val = classify_grade(grade)
            attempt_details.append({
                'attempt_no': idx + 1,
                'grade': grade,
                'class': cls_val,
                'is_voided': att.get('_is_voided', False)
            })
        grades = [r.get('Grade', '').strip() for r in attempts]
        cls    = [classify_grade(g) for g in grades]
        if 'pass' in cls:
            status = 'completed'
        elif all(c == 'pending' for c in cls):
            status = 'pending'
        else:
            status = 'outstanding'
        result.append({
            'code': code, 'title': title,
            'attempts': len(attempts), 'grades': grades, 'status': status,
            'details': attempt_details,
        })
    return result


def find_medical_courses(rows: list[dict]) -> list[dict]:
    """
    Find all courses with at least one MC attempt.
    Returns details of all attempts so they can be displayed as outstanding/resolved.
    """
    from collections import defaultdict
    resolved_rows = resolve_course_attempts(rows)
    course_map: dict[str, list] = defaultdict(list)
    for row in resolved_rows:
        code = row.get('Course Unit', '').strip()
        if code:
            course_map[code].append(row)

    result = []
    for code, attempts in course_map.items():
        grades = [r.get('Grade', '').strip() for r in attempts]
        has_mc = any(g.upper() == 'MC' for g in grades)
        if not has_mc:
            continue
            
        title = attempts[0].get('Course Title', code)
        attempt_details = []
        for idx, att in enumerate(attempts):
            grade = att.get('Grade', '').strip()
            cls_val = classify_grade(grade)
            attempt_details.append({
                'attempt_no': idx + 1,
                'grade': grade,
                'class': cls_val,
                'is_voided': att.get('_is_voided', False)
            })
        
        latest_grade = attempts[-1].get('Grade', '').strip().upper()
        if latest_grade == 'MC':
            status = 'outstanding'
        else:
            status = 'resolved'
            
        result.append({
            'code': code, 'title': title,
            'attempts': len(attempts), 'grades': grades, 'status': status,
            'details': attempt_details,
        })
    return result


def main():
    init_ansi()
    WIDTH = 90

    use_interactive = HAS_MSVCRT


    while True:
        print()
        print_logo()
        print()

        # Welcome Card
        print(box_top(WIDTH))
        print(box_row(f"{CLR_CYAN}{CLR_BOLD}Welcome to Uniscore CLI!{CLR_RESET}", WIDTH))
        print(box_row(f"{CLR_DIM}University of Colombo · Uniscore V1.0{CLR_RESET}", WIDTH))
        print(box_row(f"{CLR_DIM}Build by Kasun Vishvajith{CLR_RESET}", WIDTH))
        print(box_bot(WIDTH))
        print()

        # Sign-In Box
        print(box_top(WIDTH))
        print(box_row(f"{CLR_YELLOW}{CLR_BOLD}🔐  SIS PORTAL SIGN IN{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))
        print(box_row_left(f"{CLR_DIM}Please enter your SIS login credentials to authenticate{CLR_RESET}", WIDTH))
        print(box_row_left(f"{CLR_DIM}and securely download your course results.{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))

        reg_no = ""
        while not reg_no.strip():
            # Print left border and input prompt inside the box
            sys.stdout.write(f"{CLR_SEPARATOR}│{CLR_RESET}  {CLR_WHITE}Registration No.:{CLR_RESET} ")
            sys.stdout.flush()
            reg_no = input().strip()
            if not reg_no:
                sys.stdout.write("\033[A\r")
                error_msg = f"{CLR_RED}⚠  Registration number cannot be empty.{CLR_RESET}"
                print(box_row_left(error_msg, WIDTH))
                print(box_mid(WIDTH))
                continue
            
            # Overwrite the input line with a styled, boxed version
            sys.stdout.write(f"\033[A\r{box_row_left(f'{CLR_WHITE}Registration No.:{CLR_RESET} {CLR_CYAN}{reg_no}{CLR_RESET}', WIDTH)}\n")
            sys.stdout.flush()

        username = reg_no if "@" in reg_no else f"{reg_no}@stu.cmb.ac.lk"

        password = ""
        while not password:
            # Prompt for password inside the box
            password = get_masked_password(f"{CLR_SEPARATOR}│{CLR_RESET}  {CLR_WHITE}Password:{CLR_RESET} ")
            if not password:
                sys.stdout.write("\033[A\r")
                error_msg = f"{CLR_RED}⚠  Password cannot be empty.{CLR_RESET}"
                print(box_row_left(error_msg, WIDTH))
                print(box_mid(WIDTH))
                continue
            
            # Overwrite the password input line with a styled, boxed version
            sys.stdout.write(f"\033[A\r{box_row_left(f'{CLR_WHITE}Password:{CLR_RESET} {CLR_CYAN}{'*' * len(password)}{CLR_RESET}', WIDTH)}\n")
            sys.stdout.flush()

        print(box_bot(WIDTH))
        print()

        # Now show Gateway Panel
        print()
        print(box_top(WIDTH))
        print(box_row(f"{CLR_CYAN}{CLR_BOLD}🌐  SYSTEM GATEWAY PIPELINE{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))

        session = requests.Session()
        try:
            # 1. Login
            sys.stdout.write(f"\r{box_row_left(f'{CLR_YELLOW}⚡{CLR_RESET}  Logging into SIS portal...', WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.5)
            
            success, err_msg = login(session, username, password)
            if not success:
                sys.stdout.write(f"\r{box_row_left(f'{CLR_RED}❌  Login failed: {err_msg}{CLR_RESET}', WIDTH)}\n")
                print(box_bot(WIDTH))
                # Instead of exiting directly, offer the user a retry menu
                print()
                print(box_top(WIDTH))
                print(box_row(f"{CLR_RED}{CLR_BOLD}⚠️  CONNECTION FAILED{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
                
                loop_options = ["Retry / Sign in again", "Exit Uniscore"]
                loop_idx = 0
                if use_interactive:
                    def draw_fail_menu(with_bot=True):
                        sys.stdout.write(box_row_left(f"{CLR_WHITE}Would you like to try again or exit?{CLR_RESET}", WIDTH) + "\n")
                        sys.stdout.write(box_row_left("", WIDTH) + "\n")
                        for idx, opt in enumerate(loop_options):
                            if idx == loop_idx:
                                opt_str = f" {CLR_CYAN}❯{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}"
                            else:
                                opt_str = f"   {CLR_DIM}{opt}{CLR_RESET}"
                            sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                        if with_bot:
                            sys.stdout.write(box_bot(WIDTH) + "\n")
                        else:
                            sys.stdout.write(box_mid(WIDTH) + "\n")
                        sys.stdout.flush()

                    draw_fail_menu(with_bot=True)
                    while True:
                        ch = msvcrt.getch()
                        if ch in (b'\r', b'\n'):
                            break
                        elif ch == b'\xe0':
                            ch2 = msvcrt.getch()
                            if ch2 == b'H':
                                loop_idx = (loop_idx - 1) % len(loop_options)
                            elif ch2 == b'P':
                                loop_idx = (loop_idx + 1) % len(loop_options)
                            sys.stdout.write("\033[5A")
                            draw_fail_menu(with_bot=True)
                    sys.stdout.write("\033[5A")
                    draw_fail_menu(with_bot=False)
                    loop_choice = str(loop_idx + 1)
                else:
                    print(box_row_left(f"{CLR_WHITE}Would you like to try again or exit?{CLR_RESET}", WIDTH))
                    print(box_row_left("", WIDTH))
                    for idx, opt in enumerate(loop_options):
                        print(box_row_left(f"  {CLR_CYAN}[{idx+1}]{CLR_RESET}  {CLR_DIM}{opt}{CLR_RESET}", WIDTH))
                    print(box_mid(WIDTH))
                    loop_choice = ""
                    while loop_choice not in ("1", "2"):
                        loop_choice = input(f"  {CLR_CYAN}❯ {CLR_RESET}{CLR_WHITE}Choose option (1-2): {CLR_RESET}").strip()
                    
                if loop_choice == "2":
                    print(box_row(f"{CLR_RED}Exiting Uniscore. Goodbye!{CLR_RESET}", WIDTH))
                    print(box_bot(WIDTH))
                    safe_exit(1)
                else:
                    print(box_row(f"{CLR_CYAN}Restarting session...{CLR_RESET}", WIDTH))
                    print(box_bot(WIDTH))
                    time.sleep(0.5)
                    continue

            sys.stdout.write(f"\r{box_row_left(f'{CLR_GREEN}✓{CLR_RESET}  Successfully authenticated with SIS portal.', WIDTH)}\n")
            sys.stdout.flush()
            time.sleep(0.3)

            # 2. Fetching
            sys.stdout.write(f"\r{box_row_left(f'{CLR_BLUE}⚡{CLR_RESET}  Requesting result sheet from servers...', WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.5)
            
            try:
                r = session.get(RESULTS_URL, headers=HEADERS)
                r.raise_for_status()
            except Exception:
                print()
                print(box_row_left(f"{CLR_RED}❌  Failed to reach SIS result portal.{CLR_RESET}", WIDTH))
                print(box_bot(WIDTH))
                safe_exit(1)

            # 3. Parsing
            rows = parse_results(r.text)
            if not rows:
                print()
                print(box_row_left(f"{CLR_RED}❌  No result sheets detected in HTML response.{CLR_RESET}", WIDTH))
                print(box_bot(WIDTH))
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(r.text)
                safe_exit(1)

            sys.stdout.write(f"\r{box_row_left(f'{CLR_GREEN}✓{CLR_RESET}  Retrieved and compiled {CLR_CYAN}{len(rows)}{CLR_RESET} course records.', WIDTH)}\n")
            sys.stdout.flush()
            time.sleep(0.3)

            # 4. Preparing Session Finish
            sys.stdout.write(f"\r{box_row_left(f'{CLR_GREEN}✓{CLR_RESET}  Compiled database records successfully.', WIDTH)}\n")
            sys.stdout.flush()
            time.sleep(0.3)

            # 5. Logout
            sys.stdout.write(f"\r{box_row_left(f'{CLR_BLUE}⚡{CLR_RESET}  Terminating active portal session...', WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.4)
            
            try:
                logout_r = session.get(LOGOUT_URL, headers=HEADERS, timeout=8)
                if logout_r.status_code not in (200, 302, 301):
                    session.post(LOGOUT_URL, headers=HEADERS, timeout=8)
                sys.stdout.write(f"\r{box_row_left(f'{CLR_GREEN}✓{CLR_RESET}  Session securely terminated. Portals closed.', WIDTH)}\n")
            except Exception:
                sys.stdout.write(f"\r{box_row_left(f'{CLR_YELLOW}⚠{CLR_RESET}  Session terminated locally (portal unreachable).', WIDTH)}\n")
        finally:
            session.close()

        print(box_bot(WIDTH))
        print()

        # Now print the summary report (box is kept open at the bottom)
        txt_summary_str = print_summary(rows)

        # Cohesive menu inside the same box!
        print(box_mid(WIDTH))

        safe_reg_no_menu = re.sub(r'[\\/*?:"<>|]', "-", reg_no.strip())
        options = [
            f"Save as CSV database ({safe_reg_no_menu}.csv)",
            f"Save as TXT Summary report ({safe_reg_no_menu}.txt)",
            "Save both CSV & TXT Summary",
            "Do not save anything"
        ]
        selected_idx = 0

        if use_interactive:
            def draw_interactive_menu(with_bot=True):
                sys.stdout.write(box_row_left(f"{CLR_WHITE}How would you like to save the retrieved records?{CLR_RESET}", WIDTH) + "\n")
                sys.stdout.write(box_row_left("", WIDTH) + "\n")
                for idx, opt in enumerate(options):
                    if idx == selected_idx:
                        opt_str = f" {CLR_CYAN}❯{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}"
                    else:
                        opt_str = f"   {CLR_DIM}{opt}{CLR_RESET}"
                    sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                if with_bot:
                    sys.stdout.write(box_bot(WIDTH) + "\n")
                else:
                    sys.stdout.write(box_mid(WIDTH) + "\n")
                sys.stdout.flush()

            draw_interactive_menu(with_bot=True)

            while True:
                ch = msvcrt.getch()
                if ch in (b'\r', b'\n'):
                    break
                elif ch == b'\xe0':  # Arrow prefix
                    ch2 = msvcrt.getch()
                    if ch2 == b'H':  # Up Arrow
                        selected_idx = (selected_idx - 1) % len(options)
                    elif ch2 == b'P':  # Down Arrow
                        selected_idx = (selected_idx + 1) % len(options)
                    
                    sys.stdout.write("\033[7A")
                    draw_interactive_menu(with_bot=True)
            
            sys.stdout.write("\033[7A")
            draw_interactive_menu(with_bot=False)
            choice = str(selected_idx + 1)
        else:
            print(box_row_left(f"{CLR_WHITE}How would you like to save the retrieved records?{CLR_RESET}", WIDTH))
            print(box_row_left("", WIDTH))
            for idx, opt in enumerate(options):
                print(box_row_left(f"  {CLR_CYAN}[{idx+1}]{CLR_RESET}  {CLR_DIM}{opt}{CLR_RESET}", WIDTH))
            print(box_mid(WIDTH))
            
            choice = ""
            while choice not in ("1", "2", "3", "4"):
                choice = input(f"  {CLR_CYAN}❯ {CLR_RESET}{CLR_WHITE}Choose export option (1-4): {CLR_RESET}").strip()
                if choice not in ("1", "2", "3", "4"):
                    print(f"  {CLR_RED}⚠  Invalid choice. Please enter 1, 2, 3, or 4.{CLR_RESET}")

        import os
        safe_reg_no = re.sub(r'[\\/*?:"<>|]', "-", reg_no.strip())
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_dir):
            downloads_dir = os.getcwd()
            
        csv_filename = os.path.join(downloads_dir, f"{safe_reg_no}.csv")
        txt_filename = os.path.join(downloads_dir, f"{safe_reg_no}.txt")

        save_csv_flag = choice in ("1", "3")
        save_txt_flag = choice in ("2", "3")

        if save_csv_flag:
            try:
                with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Saved course records to {CLR_ORANGE}{csv_filename}{CLR_RESET}", WIDTH))
            except Exception as e:
                print(box_row_left(f"{CLR_RED}⚠  Failed to save CSV: {e}{CLR_RESET}", WIDTH))

        if save_txt_flag:
            try:
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(txt_summary_str)
                print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Saved clean text summary to {CLR_ORANGE}{txt_filename}{CLR_RESET}", WIDTH))
            except Exception as e:
                print(box_row_left(f"{CLR_RED}⚠  Failed to save text summary: {e}{CLR_RESET}", WIDTH))

        # Show Exit or Re-enter menu inside the box (inner loop allows
        # viewing analysis panels without restarting the session)
        print(box_mid(WIDTH))

        loop_options = [
            "View Repeated",
            "View Medicals",
            "Sign in with a different account",
            "Visit Developer's Portfolio",
            "Exit Uniscore",
        ]
        # Lines drawn by draw_loop_menu: question + blank + 5 options + border = 8
        _LOOP_LINES = 8

        session_action = None
        while session_action is None:
            loop_idx = 0

            if use_interactive:
                def draw_loop_menu(with_bot=True):
                    sys.stdout.write(box_row_left(f"{CLR_WHITE}Session complete. What would you like to do next?{CLR_RESET}", WIDTH) + "\n")
                    sys.stdout.write(box_row_left("", WIDTH) + "\n")
                    for idx, opt in enumerate(loop_options):
                        if idx == loop_idx:
                            opt_str = f" {CLR_CYAN}\u276f{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}"
                        else:
                            opt_str = f"   {CLR_DIM}{opt}{CLR_RESET}"
                        sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                    if with_bot:
                        sys.stdout.write(box_bot(WIDTH) + "\n")
                    else:
                        sys.stdout.write(box_mid(WIDTH) + "\n")
                    sys.stdout.flush()

                draw_loop_menu(with_bot=True)

                while True:
                    ch = msvcrt.getch()
                    if ch in (b'\r', b'\n'):
                        break
                    elif ch == b'\xe0':
                        ch2 = msvcrt.getch()
                        if ch2 == b'H':
                            loop_idx = (loop_idx - 1) % len(loop_options)
                        elif ch2 == b'P':
                            loop_idx = (loop_idx + 1) % len(loop_options)
                        sys.stdout.write(f"\033[{_LOOP_LINES}A")
                        draw_loop_menu(with_bot=True)

                sys.stdout.write(f"\033[{_LOOP_LINES}A")
                draw_loop_menu(with_bot=False)
                loop_choice = str(loop_idx + 1)
            else:
                print(box_row_left(f"{CLR_WHITE}Session complete. What would you like to do next?{CLR_RESET}", WIDTH))
                print(box_row_left("", WIDTH))
                for idx, opt in enumerate(loop_options):
                    print(box_row_left(f"  {CLR_CYAN}[{idx+1}]{CLR_RESET}  {CLR_DIM}{opt}{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))

                loop_choice = ""
                while loop_choice not in ("1", "2", "3", "4", "5"):
                    loop_choice = input(f"  {CLR_CYAN}\u276f {CLR_RESET}{CLR_WHITE}Choose option (1-5): {CLR_RESET}").strip()

            # ── Handle choice ─────────────────────────────────────────────────────
            if loop_choice == "1":
                # Repeated / resit courses — printed inline inside open box
                rpt = find_repeated_courses(rows)
                print(box_row(f"{CLR_ORANGE}{CLR_BOLD}\u267b\ufe0f  REPEATED / RESIT COURSES{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
                if not rpt:
                    print(box_row_left(
                        f"{CLR_GREEN}\u2713{CLR_RESET}  {CLR_DIM}No repeated courses detected.{CLR_RESET}", WIDTH))
                else:
                    hdr = f"{CLR_DIM}{'Code':<8}  {'Title':<20}  {'Att':>3}  {'Status':<28}  {'Result':<9}{CLR_RESET}"
                    print(box_row_left(hdr, WIDTH))
                    sep = f"{CLR_SEPARATOR}{'\u2500'*8}  {'\u2500'*20}  {'\u2500'*3}  {'\u2500'*28}  {'\u2500'*9}{CLR_RESET}"
                    print(box_row_left(sep, WIDTH))
                    for r in rpt:
                        for det in r['details']:
                            att_val = get_ordinal(det['attempt_no'])
                            att_s   = f"{CLR_DIM}{att_val:>3}{CLR_RESET}"
                            is_voided = det.get('is_voided', False)
                            void_suffix_plain = " (Voided)" if is_voided else ""
                            
                            if det['class'] == 'pass':
                                plain_status = f"✓ Completed{void_suffix_plain}"
                                sts_s = f"{CLR_GREEN}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                code_s = f"{CLR_GREEN}{r['code']:<8}{CLR_RESET}"
                            elif det['class'] == 'medical':
                                plain_status = f"\u26a0\ufe0f Medical{void_suffix_plain}"
                                sts_s = f"{CLR_BLUE}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                code_s = f"{CLR_BLUE}{r['code']:<8}{CLR_RESET}"
                            elif det['class'] == 'pending':
                                plain_status = f"⏳ Pending{void_suffix_plain}"
                                sts_s = f"{CLR_YELLOW}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                code_s = f"{CLR_YELLOW}{r['code']:<8}{CLR_RESET}"
                            else:
                                plain_status = f"✗ Repeat{void_suffix_plain}"
                                sts_s = f"{CLR_RED}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                code_s = f"{CLR_RED}{r['code']:<8}{CLR_RESET}"
                            
                            title_s = f"{CLR_WHITE}{r['title'][:20]:<20}{CLR_RESET}"
                            
                            plain_grd = f"[{det['grade']}]"
                            padded_grd = f"{plain_grd:<9}"
                            if det['class'] == 'pass':
                                grd_s = f"{CLR_GREEN}{padded_grd}{CLR_RESET}"
                            elif det['class'] == 'medical':
                                grd_s = f"{CLR_BLUE}{padded_grd}{CLR_RESET}"
                            elif det['class'] == 'pending':
                                grd_s = f"{CLR_YELLOW}{padded_grd}{CLR_RESET}"
                            else:
                                grd_s = f"{CLR_RED}{padded_grd}{CLR_RESET}"

                            print(box_row_left(f"{code_s}  {title_s}  {att_s}  {sts_s}  {grd_s}", WIDTH))
                print(box_mid(WIDTH))

            elif loop_choice == "2":
                # Medical / Aegrotat Attempts — printed inline inside open box
                meds = find_medical_courses(rows)
                print(box_row(f"{CLR_BLUE}{CLR_BOLD}🏥  MEDICAL / RESIT COURSES{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
                if not meds:
                    print(box_row_left(
                        f"{CLR_GREEN}✓{CLR_RESET}  {CLR_DIM}No medical attempts recorded.{CLR_RESET}", WIDTH))
                else:
                    hdr = f"{CLR_DIM}{'Code':<8}  {'Title':<20}  {'Att':>3}  {'Status':<28}  {'Result':<9}{CLR_RESET}"
                    print(box_row_left(hdr, WIDTH))
                    sep = f"{CLR_SEPARATOR}{'\u2500'*8}  {'\u2500'*20}  {'\u2500'*3}  {'\u2500'*28}  {'\u2500'*9}{CLR_RESET}"
                    print(box_row_left(sep, WIDTH))
                    for m in meds:
                        for det in m['details']:
                            att_val = get_ordinal(det['attempt_no'])
                            att_s   = f"{CLR_DIM}{att_val:>3}{CLR_RESET}"
                            is_voided = det.get('is_voided', False)
                            void_suffix_plain = " (Voided)" if is_voided else ""
                            
                            if det['class'] == 'medical':
                                if is_voided:
                                    plain_status = f"\u26a0\ufe0f Resolved Medical{void_suffix_plain}"
                                    sts_s = f"{CLR_DIM}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                    code_s = f"{CLR_BLUE}{m['code']:<8}{CLR_RESET}"
                                    grd_s = f"{CLR_DIM}[{det['grade']}]{CLR_RESET}"
                                else:
                                    plain_status = f"\u26a0\ufe0f Outstanding Medical{void_suffix_plain}"
                                    sts_s = f"{CLR_RED}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                    code_s = f"{CLR_BLUE}{m['code']:<8}{CLR_RESET}"
                                    grd_s = f"{CLR_RED}[{det['grade']}]{CLR_RESET}"
                            else:
                                if det['class'] == 'pass':
                                    plain_status = f"✓ Completed (Resit){void_suffix_plain}"
                                    sts_s = f"{CLR_GREEN}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                    code_s = f"{CLR_GREEN}{m['code']:<8}{CLR_RESET}"
                                else:
                                    plain_status = f"✗ Resit Attempt{void_suffix_plain}"
                                    sts_s = f"{CLR_YELLOW}{pad_visible(plain_status, 28)}{CLR_RESET}"
                                    code_s = f"{CLR_YELLOW}{m['code']:<8}{CLR_RESET}"
                                    
                            title_s = f"{CLR_WHITE}{m['title'][:20]:<20}{CLR_RESET}"
                            
                            plain_grd = f"[{det['grade']}]"
                            padded_grd = f"{plain_grd:<9}"
                            if det['class'] == 'medical':
                                if is_voided:
                                    grd_s = f"{CLR_DIM}{padded_grd}{CLR_RESET}"
                                else:
                                    grd_s = f"{CLR_RED}{padded_grd}{CLR_RESET}"
                            else:
                                if det['class'] == 'pass':
                                    grd_s = f"{CLR_GREEN}{padded_grd}{CLR_RESET}"
                                else:
                                    grd_s = f"{CLR_YELLOW}{padded_grd}{CLR_RESET}"

                            print(box_row_left(f"{code_s}  {title_s}  {att_s}  {sts_s}  {grd_s}", WIDTH))
                print(box_mid(WIDTH))

            elif loop_choice == "3":
                session_action = "restart"
            elif loop_choice == "4":
                import webbrowser
                try:
                    webbrowser.open("https://kasun-vishvajith.github.io/Portfolio/")
                    print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Opening portfolio in your browser...", WIDTH))
                except Exception:
                    print(box_row_left(f"{CLR_RED}⚠  Could not open browser. Link: https://kasun-vishvajith.github.io/Portfolio/{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
            else:  # "5"
                session_action = "exit"

        if session_action == "exit":
            # Exit: print goodbye message inside the box and seal it
            print(box_row(f"{CLR_GREEN}Done!{CLR_RESET} {CLR_DIM}Thank you for using Uniscore. Goodbye! \U0001f44b{CLR_RESET}", WIDTH))
            print(box_bot(WIDTH))
            print()
            safe_exit(0)
        else:
            # Re-enter: inform user, close box, loop back to outer while
            print(box_row(f"{CLR_CYAN}Resetting console and starting new session...{CLR_RESET}", WIDTH))
            print(box_bot(WIDTH))
            print()
            time.sleep(0.8)


if __name__ == "__main__":
    main()
