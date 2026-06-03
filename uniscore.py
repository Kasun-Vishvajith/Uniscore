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
 
 
# ── ANSI / TrueColor helpers ──────────────────────────────────────────────────
 
def safe_exit(code=0):
    try:
        input(f"\n{CLR_DIM}Press Enter to exit...{CLR_RESET}")
    except (KeyboardInterrupt, EOFError):
        pass
    sys.exit(code)
 
def hex_color(hex_str: str) -> str:
    h = hex_str.lstrip('#')
    r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"\033[38;2;{r};{g};{b}m"
 
CLR_HEADER  = "\033[95m"
CLR_BOLD    = "\033[1m"
CLR_RESET   = "\033[0m"
 
CLR_CYAN      = hex_color("#56d4e8")
CLR_GREEN     = hex_color("#56e87a")
CLR_BLUE      = hex_color("#7aa2f7")
CLR_YELLOW    = hex_color("#f0c060")
CLR_RED       = hex_color("#e8566a")
CLR_WHITE     = hex_color("#eef0f5")
CLR_DIM       = hex_color("#6b7594")
CLR_PURPLE    = hex_color("#bb9af7")
CLR_ORANGE    = hex_color("#ff9e64")
CLR_SEPARATOR = hex_color("#3a3f5c")
CLR_TEAL      = hex_color("#2ac3de")
CLR_PINK      = hex_color("#f7768e")
 
 
def get_display_width(s: str) -> int:
    ansi_escape    = re.compile(r'\033\[[0-9;]*m')
    hyperlink_escape = re.compile(r'\033\]8;.*?\033\\')
    clean_s = ansi_escape.sub("", s)
    clean_s = hyperlink_escape.sub("", clean_s)
    width = 0
    for idx, char in enumerate(clean_s):
        if char == '\ufe0f':
            continue
        has_vs16 = (idx + 1 < len(clean_s) and clean_s[idx + 1] == '\ufe0f')
        if char == '♻':
            width += 2; continue
        if char == '⚡':
            width += 2; continue
        if char == '⚠':
            width += 2 if has_vs16 else 1; continue
        eaw = unicodedata.east_asian_width(char)
        if eaw in ('W', 'F'):
            width += 2
        elif eaw == 'A':
            if 0x2500 <= ord(char) <= 0x259f:
                width += 1
            elif char in ("✓", "✔", "·", "✗", "✘", "◀", "▶"):
                width += 1
            else:
                width += 2
        else:
            width += 1
    return width
 
 
def pad_visible(plain_text: str, target_width: int) -> str:
    w = get_display_width(plain_text)
    return plain_text + (" " * max(0, target_width - w))
 
 
def center_line(content: str, width: int, fill: str = " ") -> str:
    visible  = get_display_width(content)
    padding  = max(0, width - visible)
    left     = padding // 2
    right    = padding - left
    return fill * left + content + fill * right
 
 
# ── Box drawing ───────────────────────────────────────────────────────────────
 
def box_top(width: int, color=CLR_SEPARATOR) -> str:
    return f"{color}┌{'─' * (width - 2)}┐{CLR_RESET}"
 
def box_mid(width: int, color=CLR_SEPARATOR) -> str:
    return f"{color}├{'─' * (width - 2)}┤{CLR_RESET}"
 
def box_bot(width: int, color=CLR_SEPARATOR) -> str:
    return f"{color}└{'─' * (width - 2)}┘{CLR_RESET}"
 
def box_row(content: str, width: int, color=CLR_SEPARATOR) -> str:
    inner_width = width - 4
    centred = center_line(content, inner_width)
    return f"{color}│{CLR_RESET} {centred} {color}│{CLR_RESET}"
 
def box_row_left(content: str, width: int, color=CLR_SEPARATOR) -> str:
    visible_len = get_display_width(content)
    pad = max(0, width - 6 - visible_len)
    return f"{color}│{CLR_RESET}  {content}{' ' * pad}  {color}│{CLR_RESET}"
 
def box_row_split(left_content: str, right_content: str, width: int) -> str:
    mid       = width // 2
    left_vis  = get_display_width(left_content)
    right_vis = get_display_width(right_content)
    left_pad  = max(0, mid - left_vis - 3)
    right_pad = max(0, width - mid - right_vis - 6)
    return (
        f"{CLR_SEPARATOR}│{CLR_RESET}  {left_content}{' ' * left_pad}"
        f"{CLR_SEPARATOR}│{CLR_RESET}  {right_content}{' ' * right_pad}  {CLR_SEPARATOR}│{CLR_RESET}"
    )
 
 
# ── Logo ──────────────────────────────────────────────────────────────────────
 
def print_logo():
    logo_data = [
        {4: "#a855f7"},
        {3: "#7c6cf7", 5: "#7aa2f7"},
        {2: "#4d96ff", 4: "#56d4e8", 6: "#6bcb77"},
        {1: "#6bcb77", 3: "#9ee060", 5: "#ffd93d", 7: "#ffbd2e"},
        {0: "#ff9e64", 2: "#ff9e64", 4: "#ff7b7b", 6: "#ff6b6b", 8: "#e8566a"},
        {0: "#ff6b6b", 1: "#ff7b7b", 7: "#e8566a", 8: "#c0392b"},
        {0: "#c0392b", 1: "#e8566a", 8: "#a93226"},
        {0: "#922b21", 1: "#c0392b", 8: "#7b241c"}
    ]
    width      = 90
    logo_width = 18
    padding    = (width - logo_width) // 2
    for row in logo_data:
        line_chars = []
        for col in range(9):
            if col in row:
                line_chars.append(f"{hex_color(row[col])}██{CLR_RESET}")
            else:
                line_chars.append("  ")
        print(" " * padding + "".join(line_chars))
 
 
def init_ansi():
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)
            if hOut != -1:
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(hOut, mode.value | 0x0004)
        except Exception:
            pass
 
 
def get_masked_password(prompt="Password: ") -> str:
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
            elif ch == b'\x08':
                if password:
                    password.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == b'\x03':
                raise KeyboardInterrupt
            else:
                try:
                    char = ch.decode('utf-8')
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
 
 
# ── Faculty config ────────────────────────────────────────────────────────────
 
FACULTIES = [
    {"name": "Faculty of Science",                   "url": "https://sis.cmb.ac.lk/sci",      "color": "#0082D8"},
    {"name": "Faculty of Arts",                       "url": "https://sis.cmb.ac.lk/arts",     "color": "#D53F8C"},
    {"name": "Faculty of Management and Finance",     "url": "https://sis.cmb.ac.lk/mgmt",     "color": "#E53E3E"},
    {"name": "Faculty of Law",                        "url": "https://sis.cmb.ac.lk/law",      "color": "#00A3C4"},
    {"name": "Sri Palee Campus",                      "url": "https://sis.cmb.ac.lk/spc",      "color": "#ED8936"},
    {"name": "Faculty of Technology",                 "url": "https://sis.cmb.ac.lk/tech",     "color": "#4299E1"},
    {"name": "Faculty of Nursing",                    "url": "https://sis.cmb.ac.lk/nur",      "color": "#E04F5F"},
    {"name": "Faculty of Education (Arts)",           "url": "https://sis.cmb.ac.lk/arts_edu", "color": "#38A169"},
    {"name": "Faculty of Education (Direct Intake)",  "url": "https://sis.cmb.ac.lk/edu",      "color": "#9F7AEA"},
]
 
BASE_URL   = "https://sis.cmb.ac.lk/sci"
LOGIN_URL  = f"{BASE_URL}/index"
AJAX_LOGIN = f"{BASE_URL}/ajax.php?req=login"
LOGOUT_URL = f"{BASE_URL}/ajax.php?req=logout"
RESULTS_URL = f"{BASE_URL}/results/result_sheet"
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Referer": LOGIN_URL,
}
 
def update_faculty_urls(fac_dict):
    global BASE_URL, LOGIN_URL, AJAX_LOGIN, LOGOUT_URL, RESULTS_URL, HEADERS
    BASE_URL    = fac_dict["url"]
    LOGIN_URL   = f"{BASE_URL}/index"
    AJAX_LOGIN  = f"{BASE_URL}/ajax.php?req=login"
    LOGOUT_URL  = f"{BASE_URL}/ajax.php?req=logout"
    RESULTS_URL = f"{BASE_URL}/results/result_sheet"
    HEADERS     = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Referer": LOGIN_URL,
    }
 
 
# ── Auth ──────────────────────────────────────────────────────────────────────
 
def login(session: requests.Session, username: str, password: str) -> tuple[bool, str]:
    r = session.get(LOGIN_URL, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    payload = {}
    for inp in soup.find_all("input", type="hidden"):
        if inp.get("name"):
            payload[inp["name"]] = inp.get("value", "")
    payload["uname"] = username
    payload["pw"]    = password
    r = session.post(AJAX_LOGIN, data=payload, headers=HEADERS)
    r.raise_for_status()
 
    try:
        json_data = r.json()
        if isinstance(json_data, dict):
            status    = str(json_data.get("status", "")).lower()
            success_v = json_data.get("success")
            if status == "error" or success_v is False:
                msg = json_data.get("message") or json_data.get("msg") or json_data.get("error") or "Invalid username or password."
                return False, msg
            if status == "success" or success_v is True:
                return True, ""
    except ValueError:
        pass
 
    soup2 = BeautifulSoup(r.text, "html.parser")
    err   = soup2.find(class_="error") or soup2.find(class_="alert") or soup2.find(id="error") or soup2.find(class_="alert-danger")
 
    if soup2.find("input", {"name": "uname"}) or soup2.find("input", {"name": "pw"}):
        err_text = err.get_text(strip=True) if err else "Invalid username or password."
        return False, err_text
    if err:
        return False, err.get_text(strip=True)
 
    title = soup2.title.string if soup2.title else ""
    if "Student Information System" in title or "SIS" in title or any(f["name"] in title for f in FACULTIES):
        return True, ""
 
    return False, "Invalid username or password."
 
 
# ── HTML parser ───────────────────────────────────────────────────────────────
 
def parse_results(html: str) -> list[dict]:
    soup     = BeautifulSoup(html, "html.parser")
    all_rows = []
    for table in soup.find_all("table", class_="data-table"):
        thead_rows = table.find("thead").find_all("tr") if table.find("thead") else []
        if len(thead_rows) < 2:
            continue
        col_headers = [th.get_text(strip=True) for th in thead_rows[1].find_all("th")]
        if "Grade" not in col_headers:
            continue
        section = thead_rows[0].find("th").get_text(strip=True) if thead_rows[0].find("th") else ""
        inferred_sem = ""
        sec_lower    = section.lower()
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
            row          = dict(zip(col_headers, cols))
            row["Section"] = section
            row["_sem"]    = inferred_sem
            all_rows.append(row)
    return all_rows
 
 
# ── Grade classification ──────────────────────────────────────────────────────
 
PASS_GRADES = frozenset({'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'S', 'H', 'M'})
FAIL_GRADES = frozenset({'C-', 'D+', 'D', 'E'})
 
def classify_grade(grade: str) -> str:
    g = grade.strip()
    if g in PASS_GRADES:  return 'pass'
    if g in FAIL_GRADES:  return 'fail'
    if g.upper() == 'MC': return 'medical'
    if g.upper() == 'AB': return 'absent'
    return 'pending'
 
def get_ordinal(n: int) -> str:
    suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') if not 11 <= (n % 100) <= 13 else 'th'
    return f"{n}{suffix}"
 
 
# ── Academic resolution ───────────────────────────────────────────────────────
 
def resolve_course_attempts(rows: list[dict]) -> list[dict]:
    course_map = defaultdict(list)
    for idx, row in enumerate(rows):
        code = row.get("Course Unit", "").strip()
        if code:
            course_map[code].append((idx, row))
 
    resolved_rows = [dict(row) for row in rows]
    for code, atts in course_map.items():
        n        = len(atts)
        had_fail = False
        for i, (idx, row) in enumerate(atts):
            grade   = row.get("Grade", "").strip().upper()
            is_last = (i == n - 1)
            resolved_rows[idx]["_is_voided"]        = False
            resolved_rows[idx]["_gpv_override"]     = None
            resolved_rows[idx]["_credits_override"] = None
            if is_last:
                if grade == 'MC':
                    resolved_rows[idx]["_gpv_override"] = 0.0
                elif had_fail and classify_grade(grade) == 'pass':
                    orig_gpv = float(row.get("GPV", 0.0) or 0.0)
                    if orig_gpv > 2.0:
                        resolved_rows[idx]["_gpv_override"] = 2.0
            else:
                resolved_rows[idx]["_is_voided"]        = True
                resolved_rows[idx]["_credits_override"] = 0.0
            if classify_grade(grade) in ('fail', 'absent'):
                had_fail = True
    return resolved_rows
 
 
# ── Repeat & Medical finders ──────────────────────────────────────────────────
 
def find_repeated_courses(rows: list[dict]) -> list[dict]:
    """
    Show all courses that have at least one non-mc fail or absent attempt.
    Includes courses regardless of whether the student eventually passed —
    the └─ summary row communicates the final outcome.
    """
    resolved_rows = resolve_course_attempts(rows)
    course_map: dict[str, list] = defaultdict(list)
    for row in resolved_rows:
        code = row.get('Course Unit', '').strip()
        if code:
            course_map[code].append(row)
 
    result = []
    for code, attempts in course_map.items():
        grades = [r.get('Grade', '').strip() for r in attempts]
        cls    = [classify_grade(g) for g in grades]
 
        # Must have at least one genuine fail or absent (mc does NOT count as repeat)
        has_repeat = any(c in ('fail', 'absent') for c in cls)
        if not has_repeat:
            continue
 
        title = attempts[0].get('Course Title', code)
        attempt_details = []
        for idx, att in enumerate(attempts):
            grade   = att.get('Grade', '').strip()
            cls_val = classify_grade(grade)
            attempt_details.append({
                'attempt_no': idx + 1,
                'grade':      grade,
                'class':      cls_val,
                'is_voided':  att.get('_is_voided', False),
            })
 
        last_grade = grades[-1]
        last_cls   = cls[-1]
 
        if last_cls == 'pass':
            status = 'completed'
        elif last_cls == 'pending':
            status = 'pending'
        else:
            status = 'outstanding'
 
        result.append({
            'code':        code,
            'title':       title,
            'attempts':    len(attempts),
            'grades':      grades,
            'status':      status,
            'last_grade':  last_grade,
            'last_cls':    last_cls,
            'details':     attempt_details,
        })
    return result
 
 
def find_medical_courses(rows: list[dict]) -> list[dict]:
    """
    Show all courses that have at least one MC attempt.
    Includes courses regardless of whether the student eventually passed —
    the └─ summary row communicates the final outcome.
    """
    resolved_rows = resolve_course_attempts(rows)
    course_map: dict[str, list] = defaultdict(list)
    for row in resolved_rows:
        code = row.get('Course Unit', '').strip()
        if code:
            course_map[code].append(row)
 
    result = []
    for code, attempts in course_map.items():
        grades = [r.get('Grade', '').strip() for r in attempts]
        cls    = [classify_grade(g) for g in grades]
 
        # Must have at least one MC attempt
        if not any(c == 'medical' for c in cls):
            continue
 
        title = attempts[0].get('Course Title', code)
        attempt_details = []
        for idx, att in enumerate(attempts):
            grade   = att.get('Grade', '').strip()
            cls_val = classify_grade(grade)
            attempt_details.append({
                'attempt_no': idx + 1,
                'grade':      grade,
                'class':      cls_val,
                'is_voided':  att.get('_is_voided', False),
            })
 
        last_grade = grades[-1]
        last_cls   = cls[-1]
        status     = 'outstanding' if last_grade.upper() == 'MC' else 'resolved'
 
        result.append({
            'code':        code,
            'title':       title,
            'attempts':    len(attempts),
            'grades':      grades,
            'status':      status,
            'last_grade':  last_grade,
            'last_cls':    last_cls,
            'details':     attempt_details,
        })
    return result
 
 
# ── Shared renderer for Repeat / Medical tables ───────────────────────────────
 
def _cls_colors(cls: str):
    """Return (text_color, grade_color) for a given classification."""
    if cls == 'pass':    return CLR_GREEN,  CLR_GREEN
    if cls == 'fail':    return CLR_RED,    CLR_RED
    if cls == 'absent':  return CLR_RED,    CLR_RED
    if cls == 'medical': return CLR_DIM,    CLR_DIM
    if cls == 'pending': return CLR_YELLOW, CLR_YELLOW
    return CLR_WHITE, CLR_WHITE
 
 
def _attempt_status_text(det: dict, mode: str) -> str:
    """
    Return the plain status label for an attempt row.
    mode = 'repeat' or 'medical'
    """
    cls       = det['class']
    is_voided = det.get('is_voided', False)
    v         = " (Voided)" if is_voided else ""
 
    if mode == 'repeat':
        if cls == 'pass':    return f"✓ Completed{v}"
        if cls == 'medical': return f"⚠ Medical{v}"
        if cls == 'absent':  return f"✗ Absent{v}"
        if cls == 'pending': return f"⏳ Pending{v}"
        return f"✗ Repeat{v}"
    else:  # medical
        if cls == 'medical':
            return (f"⚠ Resolved Medical{v}" if is_voided else "⚠ Outstanding Medical")
        if cls == 'pass':    return f"✓ Completed (Resit){v}"
        if cls == 'absent':  return f"✗ Absent (Resit){v}"
        if cls == 'pending': return f"⏳ Pending{v}"
        return f"✗ Resit Attempt{v}"
 
 
def _summary_outcome(last_cls: str, last_grade: str, n_att: int) -> str:
    """
    Build the final outcome summary line shown below each course block.
    Format:  OUTCOME LABEL  ·  [GRADE]  ·  N attempt(s)
    Uses a dimmed separator line above it and bold outcome text.
    """
    if last_cls == 'pass':
        clr   = CLR_GREEN
        label = "✓  Passed"
    elif last_cls in ('fail', 'absent'):
        clr   = CLR_RED
        label = "✗  Still Failing"
    elif last_cls == 'medical':
        clr   = CLR_YELLOW
        label = "⏳  Medical Outstanding"
    else:
        clr   = CLR_YELLOW
        label = "⏳  Pending"
 
    att_word = "attempt" if n_att == 1 else "attempts"
    grade_pill = f"{clr}❮{last_grade}❯{CLR_RESET}"
    outcome    = f"{clr}{CLR_BOLD}{label}{CLR_RESET}"
    att_lbl    = f"{CLR_DIM}{n_att} {att_word}{CLR_RESET}"
    dot        = f"{CLR_SEPARATOR} · {CLR_RESET}"
    return f"    {CLR_SEPARATOR}╘══{CLR_RESET}  {outcome}{dot}{grade_pill}{dot}{att_lbl}"
 
 
def _print_course_block(course: dict, mode: str, width: int):
    """
    Render one course block:
      CODE   Full Title
        ├─  1st  Status label        [grade]
        ├─  2nd  Status label        [grade]
        └─  3rd  Status label        [grade]
      ╘══  OUTCOME  ·  ❮grade❯  ·  N attempts
    """
    details   = course['details']
    last_cls  = course['last_cls']
    last_grade = course['last_grade']
    n_att     = course['attempts']
 
    # ── Course title row ───────────────────────────────────────────────────
    code_clr = CLR_GREEN if last_cls == 'pass' else \
               CLR_RED   if last_cls in ('fail', 'absent') else CLR_YELLOW
    code_s   = f"{code_clr}{CLR_BOLD}{course['code']:<8}{CLR_RESET}"
    title_s  = f"{CLR_WHITE}{CLR_BOLD}{course['title']}{CLR_RESET}"
    print(box_row_left(f"{code_s}  {title_s}", width))
 
    # ── Attempt rows ───────────────────────────────────────────────────────
    for i, det in enumerate(details):
        is_last   = (i == len(details) - 1)
        connector = f"{CLR_SEPARATOR}└─{CLR_RESET}" if is_last else f"{CLR_SEPARATOR}├─{CLR_RESET}"
        att_s     = f"{CLR_DIM}{get_ordinal(det['attempt_no']):>3}{CLR_RESET}"
        plain_sts = _attempt_status_text(det, mode)
        txt_clr, grd_clr = _cls_colors(det['class'])
        sts_s     = f"{txt_clr}{pad_visible(plain_sts, 24)}{CLR_RESET}"
        grd_s     = f"{grd_clr}[{det['grade']}]{CLR_RESET}"
        print(box_row_left(f"   {connector}  {att_s}  {sts_s}  {grd_s}", width))
 
    # ── Summary / outcome row ──────────────────────────────────────────────
    print(box_row_left(_summary_outcome(last_cls, last_grade, n_att), width))
 
 
def print_repeated_table(rpt: list[dict], width: int):
    print(box_row(f"{CLR_ORANGE}{CLR_BOLD}♻️  REPEATED / RESIT COURSES{CLR_RESET}", width))
    print(box_mid(width))
 
    if not rpt:
        print(box_row_left(
            f"{CLR_GREEN}✓{CLR_RESET}  {CLR_DIM}No repeated courses on record.{CLR_RESET}", width))
        print(box_mid(width))
        return
 
    # Column header
    hdr = f"{CLR_DIM}  {'Code':<10}  {'Title':<28}   {'Att':<4}  {'Status':<24}  {'Result'}{CLR_RESET}"
    sep = f"{CLR_SEPARATOR}  {'─'*10}  {'─'*28}   {'─'*4}  {'─'*24}  {'─'*6}{CLR_RESET}"
    print(box_row_left(hdr, width))
    print(box_row_left(sep, width))
 
    for r_idx, r in enumerate(rpt):
        _print_course_block(r, 'repeat', width)
        # Dim separator line between courses, not after last
        if r_idx < len(rpt) - 1:
            sep_line = f"{CLR_SEPARATOR}{'╌' * (width - 6)}{CLR_RESET}"
            print(box_row_left(sep_line, width))
 
    print(box_mid(width))
 
 
def print_medical_table(meds: list[dict], width: int):
    print(box_row(f"{CLR_BLUE}{CLR_BOLD}🏥  MEDICAL / RESIT COURSES{CLR_RESET}", width))
    print(box_mid(width))
 
    if not meds:
        print(box_row_left(
            f"{CLR_GREEN}✓{CLR_RESET}  {CLR_DIM}No medical attempts on record.{CLR_RESET}", width))
        print(box_mid(width))
        return
 
    hdr = f"{CLR_DIM}  {'Code':<10}  {'Title':<28}   {'Att':<4}  {'Status':<24}  {'Result'}{CLR_RESET}"
    sep = f"{CLR_SEPARATOR}  {'─'*10}  {'─'*28}   {'─'*4}  {'─'*24}  {'─'*6}{CLR_RESET}"
    print(box_row_left(hdr, width))
    print(box_row_left(sep, width))
 
    for m_idx, m in enumerate(meds):
        _print_course_block(m, 'medical', width)
        if m_idx < len(meds) - 1:
            sep_line = f"{CLR_SEPARATOR}{'╌' * (width - 6)}{CLR_RESET}"
            print(box_row_left(sep_line, width))
 
    print(box_mid(width))
 
 
# ── Grade distribution ────────────────────────────────────────────────────────
 
def print_grade_distribution(rows: list[dict], width: int = 90):
    resolved_rows = resolve_course_attempts(rows)
    distribution  = defaultdict(int)
    for row in resolved_rows:
        if row.get("_is_voided"):
            continue
        section = row.get("Section", "")
        if "enhancement" in section.lower() or "enchancement" in section.lower():
            continue
        grade = row.get("Grade", "").strip().upper()
        if not grade or grade in ('--', ''):
            continue
        distribution[grade] += 1
 
    ordered_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'E']
    total_count    = sum(distribution[g] for g in ordered_grades)
 
    GRADE_COLORS = {
        'A+': hex_color("#10b981"), 'A':  hex_color("#22c55e"),
        'A-': hex_color("#84cc16"), 'B+': hex_color("#a3e635"),
        'B':  hex_color("#facc15"), 'B-': hex_color("#f59e0b"),
        'C+': hex_color("#fb923c"), 'C':  hex_color("#f97316"),
        'C-': hex_color("#ea580c"), 'D+': hex_color("#ef4444"),
        'D':  hex_color("#dc2626"), 'E':  hex_color("#b91c1c"),
    }
 
    print(box_row(f"{CLR_PURPLE}{CLR_BOLD}📊  GRADE DISTRIBUTION{CLR_RESET}", width))
    print(box_mid(width))
 
    max_count   = max((distribution[g] for g in ordered_grades), default=1)
    max_bar_len = 30
 
    hdr = f"{CLR_DIM}{'Grade':<6}  {'Count':<6}  {'Distribution'}{CLR_RESET}"
    print(box_row_left(hdr, width))
    sep = f"{CLR_SEPARATOR}{'─'*6}  {'─'*6}  {'─'*32}{CLR_RESET}"
    print(box_row_left(sep, width))
 
    for grade in ordered_grades:
        count   = distribution[grade]
        color   = GRADE_COLORS[grade]
        bar_len = int(round((count / max_count) * max_bar_len)) if max_count > 0 else 0
        bar_len = max(0, min(max_bar_len, bar_len))
        filled  = f"{color}{'█' * bar_len}{CLR_RESET}"
        empty   = f"{CLR_SEPARATOR}{'░' * (max_bar_len - bar_len)}{CLR_RESET}"
        bar_str = f"{CLR_SEPARATOR}▕{CLR_RESET}{filled}{empty}{CLR_SEPARATOR}▏{CLR_RESET}"
        grade_lbl   = f"{color}{CLR_BOLD}{grade:<6}{CLR_RESET}"
        count_lbl   = f"{CLR_WHITE}{str(count) if count > 0 else '-':<6}{CLR_RESET}"
        print(box_row_left(f"{grade_lbl}  {count_lbl}  {bar_str}", width))
 
    print(box_mid(width))
    print(box_row_left(f"{CLR_WHITE}Total Graded Courses: {CLR_CYAN}{total_count}{CLR_RESET}", width))
 
 
# ── GPA summary ───────────────────────────────────────────────────────────────
 
def print_summary(rows: list[dict]) -> str:
    WIDTH       = 90
    output_lines = []
 
    def output(line):
        print(line)
        output_lines.append(line)
 
    def infer_semester(course_code: str, section: str, row: dict) -> str:
        pre = row.get("_sem", "").strip()
        if pre:
            return pre
        for key in ("Semester", "Sem", "Period", "Term", "semester"):
            val = row.get(key, "").strip()
            if val:
                return "Sem 1" if "1" in val else "Sem 2" if "2" in val else ""
        sec = section.lower()
        if re.search(r'sem(?:ester)?[\s\-_]*1|s1\b|\b1st\s*sem', sec): return "Sem 1"
        if re.search(r'sem(?:ester)?[\s\-_]*2|s2\b|\b2nd\s*sem', sec): return "Sem 2"
        code = course_code.strip().upper()
        nums = re.findall(r'\d+', code)
        if nums:
            n = nums[0]
            if len(n) >= 3:
                s = int(n[1])
                return "Sem 1" if s <= 1 else "Sem 2"
        return "Sem 1"
 
    levels        = defaultdict(lambda: defaultdict(list))
    resolved_rows = resolve_course_attempts(rows)
 
    for row in resolved_rows:
        code    = row.get("Course Unit", "")
        grade   = row.get("Grade", "")
        section = row.get("Section", "")
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
            gpv     = row["_gpv_override"] if row.get("_gpv_override") is not None else (
                      None if gpv_val in ("", None, "--") else float(gpv_val))
            if gpv is None:
                continue
            cred    = row["_credits_override"] if row.get("_credits_override") is not None else float(row.get("Credits", 0) or 0)
            level   = row.get("Level", "?")
            if cred > 0 or (grade.upper() == 'MC' and not row.get("_is_voided")):
                sem = infer_semester(code, section, row)
                levels[level][sem].append((gpv, cred))
        except (ValueError, TypeError):
            continue
 
    print()
    time.sleep(0.2)
    output(box_top(WIDTH))
    output(box_row(f"{CLR_PURPLE}{CLR_BOLD}💜  SIS SUMMARY  ·  University of Colombo{CLR_RESET}", WIDTH))
    output(box_mid(WIDTH))
 
    all_points_total = 0
    all_credits_total = 0
    level_bar_colors  = {"1": CLR_CYAN, "2": CLR_GREEN, "3": CLR_BLUE}
    txt_summary       = ["University of Colombo - SIS Summary", "=" * 35]
 
    for level_key in sorted(levels.keys()):
        sems    = levels[level_key]
        yr_pts  = sum(g * c for sem_data in sems.values() for g, c in sem_data)
        yr_cred = sum(c     for sem_data in sems.values() for _, c in sem_data)
        yr_gpa  = yr_pts / yr_cred if yr_cred else 0
 
        if yr_cred < 24:
            cred_color = CLR_RED;    status_tag = f" {CLR_RED}[Incomplete]{CLR_RESET}"
        elif yr_cred < 30:
            cred_color = CLR_YELLOW; status_tag = f" {CLR_YELLOW}[Incomplete]{CLR_RESET}"
        else:
            cred_color = CLR_GREEN;  status_tag = ""
 
        bar_color = level_bar_colors.get(level_key, CLR_WHITE)
        year_lbl  = f"{CLR_WHITE}{CLR_BOLD}Year / Level {level_key}{CLR_RESET}"
        cred_info = f"{cred_color}{int(yr_cred)} credits{CLR_RESET}{status_tag}"
        output(box_row_split(year_lbl, cred_info, WIDTH))
        txt_summary.append(f"\nYear / Level {level_key}: {int(yr_cred)} credits")
 
        for sem_key in sorted(sems.keys()):
            sem_data = sems[sem_key]
            s_pts    = sum(g * c for g, c in sem_data)
            s_cred   = sum(c     for _, c in sem_data)
            s_gpa    = s_pts / s_cred if s_cred else 0
            sem_content = (f"  {CLR_DIM}└─ {sem_key:<6}{CLR_RESET}  "
                           f"GPA {CLR_CYAN}{s_gpa:.2f}{CLR_RESET}  {CLR_DIM}({int(s_cred)} cr){CLR_RESET}")
            output(box_row_left(sem_content, WIDTH))
            txt_summary.append(f"  {sem_key} GPA: {s_gpa:.2f} ({int(s_cred)} cr)")
 
        bar_length = 16
        target     = max(0, min(bar_length, int(round((yr_gpa / 4.0) * bar_length))))
        yr_gpa_lbl = f"  {CLR_WHITE}Year {level_key} GPA{CLR_RESET}  "
        yr_gpa_val = f"{bar_color}{CLR_BOLD}{yr_gpa:.3f}{CLR_RESET}"
        line_content = ""
        for i in range(target + 1):
            filled       = f"{bar_color}{'█' * i}{CLR_RESET}"
            empty        = f"{CLR_SEPARATOR}{'░' * (bar_length - i)}{CLR_RESET}"
            bar_str      = f"{CLR_SEPARATOR}▕{CLR_RESET}{filled}{empty}{CLR_SEPARATOR}▏{CLR_RESET}"
            line_content = f"{yr_gpa_lbl}{yr_gpa_val}  {bar_str}"
            sys.stdout.write(f"\r{box_row_left(line_content, WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.03)
        print()
        output_lines.append(box_row_left(line_content, WIDTH))
        txt_summary.append(f"  Year {level_key} GPA: {yr_gpa:.3f}")
 
        all_points_total  += yr_pts
        all_credits_total += yr_cred
        output(box_mid(WIDTH))
        time.sleep(0.12)
 
    if all_credits_total:
        overall_gpa = all_points_total / all_credits_total
        ov_bar_len  = 16
        ov_target   = max(0, min(ov_bar_len, int(round((overall_gpa / 4.0) * ov_bar_len))))
        ov_lbl      = f"  {CLR_WHITE}{CLR_BOLD}Cumulative GPA{CLR_RESET}  "
        ov_val      = f"{CLR_YELLOW}{CLR_BOLD}{overall_gpa:.4f}{CLR_RESET}"
        line_content = ""
        for i in range(ov_target + 1):
            filled       = f"{CLR_YELLOW}{'█' * i}{CLR_RESET}"
            empty        = f"{CLR_SEPARATOR}{'░' * (ov_bar_len - i)}{CLR_RESET}"
            bar_str      = f"{CLR_SEPARATOR}▕{CLR_RESET}{filled}{empty}{CLR_SEPARATOR}▏{CLR_RESET}"
            line_content = f"{ov_lbl}{ov_val}  {bar_str}"
            sys.stdout.write(f"\r{box_row_left(line_content, WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.03)
        print()
        output_lines.append(box_row_left(line_content, WIDTH))
        output(box_row_left(f"  {CLR_DIM}Total: {int(all_credits_total)} credits{CLR_RESET}", WIDTH))
        txt_summary.extend([f"\nCumulative GPA: {overall_gpa:.4f}", f"Total: {int(all_credits_total)} credits"])
 
    # Enhancement courses
    enh_rows = [r for r in rows if 'enhancement' in r.get('Section', '').lower() or 'enchancement' in r.get('Section', '').lower()]
    if enh_rows:
        output(box_mid(WIDTH))
        output(box_row(f"{CLR_PURPLE}{CLR_BOLD}🎓  ENHANCEMENT COURSES{CLR_RESET}", WIDTH))
        output(box_mid(WIDTH))
        hdr = f"{CLR_DIM}{'Code':<10}  {'Title':<28}  {'Cr':>3}  {'Grade'}{CLR_RESET}"
        output(box_row_left(hdr, WIDTH))
        sep = f"{CLR_SEPARATOR}{'─'*10}  {'─'*28}  {'─'*3}  {'─'*6}{CLR_RESET}"
        output(box_row_left(sep, WIDTH))
        total_enh_cr = 0
        for er in enh_rows:
            ec  = er.get('Course Unit', '')
            et  = er.get('Course Title', '')
            eg  = er.get('Grade', '')
            try:   ecr = float(er.get('Credits', 0) or 0)
            except ValueError: ecr = 0
            total_enh_cr += ecr
            output(box_row_left(
                f"{CLR_CYAN}{ec:<10}{CLR_RESET}  {CLR_WHITE}{et[:28]:<28}{CLR_RESET}  "
                f"{CLR_DIM}{int(ecr):>3}{CLR_RESET}  {CLR_GREEN}{eg}{CLR_RESET}", WIDTH))
        output(box_mid(WIDTH))
        output(box_row_left(
            f"{CLR_WHITE}{CLR_BOLD}{len(enh_rows)} course(s){CLR_RESET}  "
            f"{CLR_SEPARATOR}·{CLR_RESET}  {CLR_YELLOW}{int(total_enh_cr)} enhancement credits earned{CLR_RESET}", WIDTH))
        txt_summary.append(f"\nEnhancement Courses: {len(enh_rows)} course(s), {int(total_enh_cr)} credits")
 
    time.sleep(0.2)
    return "\n".join(txt_summary) + "\n"
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
 
def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('-v', '--version', 'version'):
        print("Uniscore CLI V1.2")
        sys.exit(0)
 
    init_ansi()
    WIDTH           = 90
    use_interactive = HAS_MSVCRT
 
    while True:
        print()
        print_logo()
        print()
 
        # Welcome card
        print(box_top(WIDTH))
        print(box_row(f"{CLR_CYAN}{CLR_BOLD}Welcome to Uniscore CLI!{CLR_RESET}", WIDTH))
        print(box_row(f"{CLR_DIM}University of Colombo · Uniscore V1.2{CLR_RESET}", WIDTH))
        print(box_row(f"{CLR_DIM}Built by Kasun Vishvajith{CLR_RESET}", WIDTH))
        print(box_bot(WIDTH))
        print()
 
        # Faculty selector
        fac_idx = 0
        if use_interactive:
            def draw_faculty_selector(idx):
                selected_fac = FACULTIES[idx]
                color = hex_color(selected_fac["color"])
                sys.stdout.write(box_top(WIDTH, color) + "\n")
                sys.stdout.write(box_row(f"{color}{CLR_BOLD}🏫  SELECT YOUR FACULTY{CLR_RESET}", WIDTH, color) + "\n")
                sys.stdout.write(box_mid(WIDTH, color) + "\n")
                sys.stdout.write(box_row(f"{CLR_DIM}Use Up/Down Arrow keys to scroll. Press Enter to select.{CLR_RESET}", WIDTH, color) + "\n")
                sys.stdout.write(box_row("", WIDTH, color) + "\n")
                for i, fac in enumerate(FACULTIES):
                    fac_color = hex_color(fac["color"])
                    item_text = f"  {fac_color}❯  {CLR_BOLD}{fac['name']}{CLR_RESET}" if i == idx else f"     {CLR_DIM}{fac['name']}{CLR_RESET}"
                    sys.stdout.write(box_row_left(item_text, WIDTH, color) + "\n")
                sys.stdout.write(box_row("", WIDTH, color) + "\n")
                sys.stdout.write(box_bot(WIDTH, color) + "\n")
                sys.stdout.flush()
 
            draw_faculty_selector(fac_idx)
            while True:
                ch = msvcrt.getch()
                if ch in (b'\r', b'\n'):
                    break
                elif ch == b'\xe0':
                    ch2 = msvcrt.getch()
                    if ch2 in (b'H', b'K'): fac_idx = (fac_idx - 1) % len(FACULTIES)
                    elif ch2 in (b'P', b'M'): fac_idx = (fac_idx + 1) % len(FACULTIES)
                    sys.stdout.write("\033[16A")
                    draw_faculty_selector(fac_idx)
            selected_faculty = FACULTIES[fac_idx]
            update_faculty_urls(selected_faculty)
        else:
            print(box_top(WIDTH))
            print(box_row(f"{CLR_CYAN}{CLR_BOLD}🏫  SELECT YOUR FACULTY / CAMPUS{CLR_RESET}", WIDTH))
            print(box_mid(WIDTH))
            for idx, fac in enumerate(FACULTIES):
                print(box_row_left(f"  {CLR_CYAN}[{idx+1}]{CLR_RESET}  {CLR_WHITE}{fac['name']}{CLR_RESET}", WIDTH))
            print(box_mid(WIDTH))
            choice = ""
            while not choice.isdigit() or not (1 <= int(choice) <= len(FACULTIES)):
                choice = input(f"  {CLR_CYAN}❯ {CLR_RESET}{CLR_WHITE}Choose option (1-{len(FACULTIES)}), default 1: {CLR_RESET}").strip() or "1"
            fac_idx          = int(choice) - 1
            selected_faculty = FACULTIES[fac_idx]
            update_faculty_urls(selected_faculty)
            print(box_row(f"{CLR_GREEN}Selected: {selected_faculty['name']}{CLR_RESET}", WIDTH))
            print(box_bot(WIDTH))
        print()
 
        # Sign-in box
        print(box_top(WIDTH))
        print(box_row(f"{CLR_YELLOW}{CLR_BOLD}🔐  SIS PORTAL SIGN IN{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))
        print(box_row_left(f"{CLR_DIM}Please enter your SIS login credentials to authenticate{CLR_RESET}", WIDTH))
        print(box_row_left(f"{CLR_DIM}and securely download your course results.{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))
 
        reg_no = ""
        while not reg_no.strip():
            sys.stdout.write(f"{CLR_SEPARATOR}│{CLR_RESET}  {CLR_WHITE}Registration No.:{CLR_RESET} ")
            sys.stdout.flush()
            reg_no = input().strip()
            if not reg_no:
                sys.stdout.write("\033[A\r")
                print(box_row_left(f"{CLR_RED}⚠  Registration number cannot be empty.{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
                continue
            sys.stdout.write(f"\033[A\r{box_row_left(f'{CLR_WHITE}Registration No.:{CLR_RESET} {CLR_CYAN}{reg_no}{CLR_RESET}', WIDTH)}\n")
            sys.stdout.flush()
 
        username = reg_no if "@" in reg_no else f"{reg_no}@stu.cmb.ac.lk"
 
        password = ""
        while not password:
            password = get_masked_password(f"{CLR_SEPARATOR}│{CLR_RESET}  {CLR_WHITE}Password:{CLR_RESET} ")
            if not password:
                sys.stdout.write("\033[A\r")
                print(box_row_left(f"{CLR_RED}⚠  Password cannot be empty.{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
                continue
            pw_mask = "*" * len(password)
            sys.stdout.write(f"\033[A\r{box_row_left(f'{CLR_WHITE}Password:{CLR_RESET} {CLR_CYAN}{pw_mask}{CLR_RESET}', WIDTH)}\n")
            sys.stdout.flush()
 
        print(box_bot(WIDTH))
        print()
 
        # Gateway pipeline
        print(box_top(WIDTH))
        print(box_row(f"{CLR_CYAN}{CLR_BOLD}🌐  SYSTEM GATEWAY PIPELINE{CLR_RESET}", WIDTH))
        print(box_mid(WIDTH))
 
        session = requests.Session()
        try:
            sys.stdout.write(f"\r{box_row_left(f'{CLR_YELLOW}⚡{CLR_RESET}  Logging into SIS portal...', WIDTH)}")
            sys.stdout.flush()
            time.sleep(0.5)
 
            success, err_msg = login(session, username, password)
            if not success:
                sys.stdout.write(f"\r{box_row_left(f'{CLR_RED}❌  Login failed: {err_msg}{CLR_RESET}', WIDTH)}\n")
                print(box_bot(WIDTH))
                print()
                print(box_top(WIDTH))
                print(box_row(f"{CLR_RED}{CLR_BOLD}⚠️  CONNECTION FAILED{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
 
                loop_options = ["Retry / Sign in again", "Exit Uniscore"]
                loop_idx     = 0
                if use_interactive:
                    def draw_fail_menu(with_bot=True):
                        sys.stdout.write(box_row_left(f"{CLR_WHITE}Would you like to try again or exit?{CLR_RESET}", WIDTH) + "\n")
                        sys.stdout.write(box_row_left("", WIDTH) + "\n")
                        for idx, opt in enumerate(loop_options):
                            opt_str = f" {CLR_CYAN}❯{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}" if idx == loop_idx else f"   {CLR_DIM}{opt}{CLR_RESET}"
                            sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                        sys.stdout.write((box_bot(WIDTH) if with_bot else box_mid(WIDTH)) + "\n")
                        sys.stdout.flush()
 
                    draw_fail_menu(with_bot=True)
                    while True:
                        ch = msvcrt.getch()
                        if ch in (b'\r', b'\n'): break
                        elif ch == b'\xe0':
                            ch2 = msvcrt.getch()
                            if ch2 == b'H': loop_idx = (loop_idx - 1) % len(loop_options)
                            elif ch2 == b'P': loop_idx = (loop_idx + 1) % len(loop_options)
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
 
            sys.stdout.write(f"\r{box_row_left(f'{CLR_GREEN}✓{CLR_RESET}  Compiled database records successfully.', WIDTH)}\n")
            sys.stdout.flush()
            time.sleep(0.3)
 
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
 
        txt_summary_str = print_summary(rows)
 
        # Save menu
        print(box_mid(WIDTH))
        safe_reg_no_menu = re.sub(r'[\\/*?:"<>|]', "-", reg_no.strip())
        save_options = [
            f"Save as CSV database ({safe_reg_no_menu}.csv)",
            f"Save as TXT Summary report ({safe_reg_no_menu}.txt)",
            "Save both CSV & TXT Summary",
            "Do not save anything",
        ]
        selected_idx = 0
 
        if use_interactive:
            def draw_save_menu(with_bot=True):
                sys.stdout.write(box_row_left(f"{CLR_WHITE}How would you like to save the retrieved records?{CLR_RESET}", WIDTH) + "\n")
                sys.stdout.write(box_row_left("", WIDTH) + "\n")
                for idx, opt in enumerate(save_options):
                    opt_str = f" {CLR_CYAN}❯{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}" if idx == selected_idx else f"   {CLR_DIM}{opt}{CLR_RESET}"
                    sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                sys.stdout.write((box_bot(WIDTH) if with_bot else box_mid(WIDTH)) + "\n")
                sys.stdout.flush()
 
            draw_save_menu(with_bot=True)
            while True:
                ch = msvcrt.getch()
                if ch in (b'\r', b'\n'): break
                elif ch == b'\xe0':
                    ch2 = msvcrt.getch()
                    if ch2 == b'H': selected_idx = (selected_idx - 1) % len(save_options)
                    elif ch2 == b'P': selected_idx = (selected_idx + 1) % len(save_options)
                    sys.stdout.write("\033[7A")
                    draw_save_menu(with_bot=True)
            sys.stdout.write("\033[7A")
            draw_save_menu(with_bot=False)
            choice = str(selected_idx + 1)
        else:
            print(box_row_left(f"{CLR_WHITE}How would you like to save the retrieved records?{CLR_RESET}", WIDTH))
            print(box_row_left("", WIDTH))
            for idx, opt in enumerate(save_options):
                print(box_row_left(f"  {CLR_CYAN}[{idx+1}]{CLR_RESET}  {CLR_DIM}{opt}{CLR_RESET}", WIDTH))
            print(box_mid(WIDTH))
            choice = ""
            while choice not in ("1", "2", "3", "4"):
                choice = input(f"  {CLR_CYAN}❯ {CLR_RESET}{CLR_WHITE}Choose export option (1-4): {CLR_RESET}").strip()
 
        import os
        safe_reg_no   = re.sub(r'[\\/*?:"<>|]', "-", reg_no.strip())
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_dir):
            downloads_dir = os.getcwd()
        csv_filename = os.path.join(downloads_dir, f"{safe_reg_no}.csv")
        txt_filename = os.path.join(downloads_dir, f"{safe_reg_no}.txt")
 
        if choice in ("1", "3"):
            try:
                with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Saved course records to {CLR_ORANGE}{csv_filename}{CLR_RESET}", WIDTH))
            except Exception as e:
                print(box_row_left(f"{CLR_RED}⚠  Failed to save CSV: {e}{CLR_RESET}", WIDTH))
 
        if choice in ("2", "3"):
            try:
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(txt_summary_str)
                print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Saved clean text summary to {CLR_ORANGE}{txt_filename}{CLR_RESET}", WIDTH))
            except Exception as e:
                print(box_row_left(f"{CLR_RED}⚠  Failed to save text summary: {e}{CLR_RESET}", WIDTH))
 
        # Post-session loop menu
        print(box_mid(WIDTH))
        loop_options = [
            "View Repeated Courses",
            "View Medical Courses",
            "View Grade Distribution",
            "Sign in with a different account",
            "Visit Developer's Portfolio",
            "Exit Uniscore",
        ]
        _LOOP_LINES  = 9
        session_action = None
 
        while session_action is None:
            loop_idx = 0
 
            if use_interactive:
                def draw_loop_menu(with_bot=True):
                    sys.stdout.write(box_row_left(f"{CLR_WHITE}Session complete. What would you like to do next?{CLR_RESET}", WIDTH) + "\n")
                    sys.stdout.write(box_row_left("", WIDTH) + "\n")
                    for idx, opt in enumerate(loop_options):
                        opt_str = f" {CLR_CYAN}❯{CLR_RESET} {CLR_WHITE}{CLR_BOLD}{opt}{CLR_RESET}" if idx == loop_idx else f"   {CLR_DIM}{opt}{CLR_RESET}"
                        sys.stdout.write(box_row_left(opt_str, WIDTH) + "\n")
                    sys.stdout.write((box_bot(WIDTH) if with_bot else box_mid(WIDTH)) + "\n")
                    sys.stdout.flush()
 
                draw_loop_menu(with_bot=True)
                while True:
                    ch = msvcrt.getch()
                    if ch in (b'\r', b'\n'): break
                    elif ch == b'\xe0':
                        ch2 = msvcrt.getch()
                        if ch2 == b'H': loop_idx = (loop_idx - 1) % len(loop_options)
                        elif ch2 == b'P': loop_idx = (loop_idx + 1) % len(loop_options)
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
                while loop_choice not in ("1", "2", "3", "4", "5", "6"):
                    loop_choice = input(f"  {CLR_CYAN}❯ {CLR_RESET}{CLR_WHITE}Choose option (1-6): {CLR_RESET}").strip()
 
            # ── Handle choice ──────────────────────────────────────────────────
            if loop_choice == "1":
                rpt = find_repeated_courses(rows)
                print_repeated_table(rpt, WIDTH)
 
            elif loop_choice == "2":
                meds = find_medical_courses(rows)
                print_medical_table(meds, WIDTH)
 
            elif loop_choice == "3":
                print_grade_distribution(rows, WIDTH)
                print(box_mid(WIDTH))
 
            elif loop_choice == "4":
                session_action = "restart"
 
            elif loop_choice == "5":
                import webbrowser
                try:
                    webbrowser.open("https://kasun-vishvajith.github.io/Portfolio/")
                    print(box_row_left(f"{CLR_GREEN}✓{CLR_RESET}  Opening portfolio in your browser...", WIDTH))
                except Exception:
                    print(box_row_left(
                        f"{CLR_RED}⚠  Could not open browser. "
                        f"Link: https://kasun-vishvajith.github.io/Portfolio/{CLR_RESET}", WIDTH))
                print(box_mid(WIDTH))
 
            else:  # "6"
                session_action = "exit"
 
        if session_action == "exit":
            print(box_row(f"{CLR_GREEN}Done!{CLR_RESET} {CLR_DIM}Thank you for using Uniscore. Goodbye! 👋{CLR_RESET}", WIDTH))
            print(box_bot(WIDTH))
            print()
            safe_exit(0)
        else:
            print(box_row(f"{CLR_CYAN}Resetting console and starting new session...{CLR_RESET}", WIDTH))
            print(box_bot(WIDTH))
            print()
            time.sleep(0.8)
 
 
if __name__ == "__main__":
    main()
 
