<<<<<<< ours
# 💜 Uniscore CLI

A professional command-line interface (CLI) academic dashboard and grade scraper for the **University of Colombo Student Information System (SIS)**.

---

## 🌟 Key Features

- **Multi-Faculty & Campus Support**: Support for all major UoC faculties and campuses:
  - Faculty of Science
  - Faculty of Arts
  - Faculty of Management and Finance
  - Faculty of Law
  - Sri Palee Campus
  - Faculty of Technology
  - Faculty of Nursing
  - Faculty of Education (Arts)
  - Faculty of Education (Direct Intake)
- **Interactive Faculty Selector**: Seamlessly select your faculty/campus on startup using Left/Right arrow keys, styled with the faculty's official brand colors.
- **Secure Portal Login**: Authenticate directly with the UoC SIS portal. Credentials are processed locally in memory.
- **Visual Academic Dashboard**: Rendered with custom 24-bit TrueColor ANSI frames and progress trackers.
- **Automated GPA Calculation**: Instantly parses level-by-level semester results and computes Cumulative GPA.
- **Academic Auditing & Analytics**:
  - Highlights repeated/resit courses and completion status.
  - Identifies unresolved medical (MC) course units.
  - Separate tracking for non-GPA enhancement courses.
  - Visualizes academic grade distributions via colored, gradient-styled horizontal bar charts.
- **Data Export**: Saves your raw results to `[Registration_No].csv` and a readable summary to `[Registration_No].txt` inside your Downloads folder.

---

## 📐 Academic Calculation Rules

Uniscore applies official University of Colombo academic regulations to calculate GPAs, map resits, and track course attempts:

### 1. Grading Scale & Classification
Courses are classified based on their grades:
*   **Passing Grades:** `A+`, `A`, `A-`, `B+`, `B`, `B-`, `C+`, `C` (along with non-GPA passes `S`, `H`, `M`).
*   **Failing Grades:** `C-`, `D+`, `D`, `E` (along with `AB` for Absent).
*   **Medical Certificate (MC):** Considered an approved medical attempt.
*   **GPV Mapping:** Grade Point Values (GPV) are parsed directly from the UoC SIS portal.

### 2. Repeat Conditions
When a course unit is repeated (due to an initial fail or absent grade, and not a medical):
*   **Active Attempt Only:** Only the final/latest attempt is considered active and contributes credits/GPA weights. All previous attempts are voided (assigned `0.0` credits/GPV) to avoid duplicate weighting.
*   **GPA Capping:** Standard repeated courses that achieve a passing grade are capped at a maximum GPV of **`2.0`** (equivalent to a grade of `C`), even if the subsequent attempt scored higher.

### 3. Medical Conditions
Special rules apply for courses with medical submissions:
*   **Outstanding Medical:** If the latest attempt is graded `MC` and not yet re-sat, the course is marked as *Outstanding Medical* with a temporary GPV of `0.0` (which does not count as a fail, but does not award passing credit).
*   **Resolved Medical:** If there is a subsequent attempt after an `MC`, the medical attempt is marked as *Resolved* (voided), and the subsequent attempt takes full credit and GPV **without** the standard `2.0` GPV capping rule.
*   **Resit Distinction:** Attempts following an initial `MC` grade are processed as medical resits rather than standard repeats.

---

## 📦 How to Run

### Standalone Executable (Windows)
1. Run **`uniscore v1.3.exe`** from the `dist/` directory.
2. *If flagged by Windows Smart App Control: Right-click `uniscore v1.3.exe` ➔ Properties ➔ Check **Unblock** ➔ Apply.*

### Run from Source
```bash
pip install requests beautifulsoup4
python uniscore.py
```
Or run **`Run-Uniscore.bat`**.

---

## 🔒 Privacy & Safety Guarantee
Your credentials and scraped grades are handled strictly locally and transmitted securely over SSL only to the official University of Colombo Student Information System portals (`https://sis.cmb.ac.lk/*`). No personal data is stored or sent to any third-party servers.

---

*Built with 💜 by **[Kasun Vishvajith](https://kasun-vishvajith.github.io/Portfolio/)***
||||||| ancestor
# 💜 Uniscore CLI

A professional, feature-rich command-line dashboard and result scraper for the **University of Colombo Student Information System (SIS)**. Built to pull academic transcript data, calculate Cumulative GPA, and track course records securely and locally.

---

## 🚀 Features

- **Secure Local Authentication**: Log in directly to the UoC Student Information System. Credentials are processed fully in memory and never sent to external servers.
- **Academic Dashboard**: Beautiful 24-bit TrueColor terminal design with animated GPA charts and stylized information cards.
- **Comprehensive Grade Scraper**: Extracts results across all academic levels, semesters, and enhancement courses.
- **Data Export Options**: Save your results database as a standardized `.csv` file and export a clean `.txt` summary report.
- **Academic Audit Tools**:
  - Track **repeated/resit** attempts and see completion status.
  - Highlight **outstanding medical (MC)** grades that require resolution.
- **One-Click Browser Actions**: Launch the developer's portfolio website directly from the CLI options menu.

---

## 🛠️ Technology Stack

- **Language**: Python 3.x
- **Key Libraries**:
  - `requests`: Handles secure session management and AJAX-based login pipeline to the UoC portal.
  - `beautifulsoup4`: Parses HTML structures to clean academic records.
  - `msvcrt` (Windows): Captures dynamic keypress inputs for high-performance terminal UI menus.
  - `webbrowser`: Direct integration to launch system browsers.
- **Graphics/UI**: Raw ANSI escape sequence engine mapping customized HSL/hex palettes for border frames, animations, and loading states.

---

## 📦 How to Run

### Option 1: Direct Double-Click (Compiled Executable)
No Python installation is required. Run the standalone package built with PyInstaller:
📁 **`dist/Uniscore.exe`**

*Note: If Windows Smart App Control flags the executable as unsigned, right-click `Uniscore.exe` -> select **Properties** -> check **Unblock** -> click **Apply**.*

### Option 2: Script execution with Python
If you prefer running from source code, make sure you have the dependencies installed:
```bash
pip install requests beautifulsoup4 pillow
```
Run using the python file or the provided batch file:
- Run the python file: `python uniscore_v1.0.py`
- Or double-click the helper batch file: **`Run-Uniscore.bat`**

---

## 🔒 Security & Privacy Disclaimer

> [!WARNING]
> **Educational Purposes Only**
>
> Uniscore is an independent third-party tool designed strictly for personal, educational, and convenience purposes. It is **not** affiliated with, endorsed by, or officially associated with the University of Colombo.

- **Data Privacy**: Your registration number and password are sent directly to the official UoC SIS login gateway (`https://sis.cmb.ac.lk/sci`). No credentials or scraped grades are uploaded, stored, or processed on any third-party servers. All data processing is strictly local.
- **Use with Caution**: Always use this tool responsibly. Excessive scraping requests can load university servers. Use this tool only to retrieve your personal academic summaries.
- **Warranty**: This software is provided "as is", without warranty of any kind, express or implied.
=======
# 💜 Uniscore CLI

A professional command-line interface (CLI) academic dashboard and grade scraper for the **University of Colombo Student Information System (SIS)**.

---

## 🌟 Key Features

- **Multi-Faculty & Campus Support**: Support for all major UoC faculties and campuses:
  - Faculty of Science
  - Faculty of Arts
  - Faculty of Management and Finance
  - Faculty of Law
  - Sri Palee Campus
  - Faculty of Technology
  - Faculty of Nursing
  - Faculty of Education (Arts)
  - Faculty of Education (Direct Intake)
- **Interactive Faculty Selector**: Seamlessly select your faculty/campus on startup using Left/Right arrow keys, styled with the faculty's official brand colors.
- **Secure Portal Login**: Authenticate directly with the UoC SIS portal. Credentials are processed locally in memory.
- **Visual Academic Dashboard**: Rendered with custom 24-bit TrueColor ANSI frames and progress trackers.
- **Automated GPA Calculation**: Instantly parses level-by-level semester results and computes Cumulative GPA.
- **Academic Auditing & Analytics**:
  - Highlights repeated/resit courses and completion status.
  - Identifies unresolved medical (MC) course units.
  - Separate tracking for non-GPA enhancement courses.
  - Visualizes academic grade distributions via colored, gradient-styled horizontal bar charts.
- **Data Export**: Saves your raw results to `[Registration_No].csv` and a readable summary to `[Registration_No].txt` inside your Downloads folder.

---

## 📐 Academic Calculation Rules

Uniscore applies official University of Colombo academic regulations to calculate GPAs, map resits, and track course attempts:

### 1. Grading Scale & Classification
Courses are classified based on their grades:
*   **Passing Grades:** `A+`, `A`, `A-`, `B+`, `B`, `B-`, `C+`, `C` (along with non-GPA passes `S`, `H`, `M`).
*   **Failing Grades:** `C-`, `D+`, `D`, `E` (along with `AB` for Absent).
*   **Medical Certificate (MC):** Considered an approved medical attempt.
*   **GPV Mapping:** Grade Point Values (GPV) are parsed directly from the UoC SIS portal.

### 2. Repeat Conditions
When a course unit is repeated (due to an initial fail or absent grade, and not a medical):
*   **Active Attempt Only:** Only the final/latest attempt is considered active and contributes credits/GPA weights. All previous attempts are voided (assigned `0.0` credits/GPV) to avoid duplicate weighting.
*   **GPA Capping:** Standard repeated courses that achieve a passing grade are capped at a maximum GPV of **`2.0`** (equivalent to a grade of `C`), even if the subsequent attempt scored higher.

### 3. Medical Conditions
Special rules apply for courses with medical submissions:
*   **Outstanding Medical:** If the latest attempt is graded `MC` and not yet re-sat, the course is marked as *Outstanding Medical* with a temporary GPV of `0.0` (which does not count as a fail, but does not award passing credit).
*   **Resolved Medical:** If there is a subsequent attempt after an `MC`, the medical attempt is marked as *Resolved* (voided), and the subsequent attempt takes full credit and GPV **without** the standard `2.0` GPV capping rule.
*   **Resit Distinction:** Attempts following an initial `MC` grade are processed as medical resits rather than standard repeats.

---

## 📦 How to Run

### Standalone Executable (Windows)
1. Run **`uniscore v1.3.exe`** from the `dist/` directory.
2. *If flagged by Windows Smart App Control: Right-click `uniscore v1.3.exe` ➔ Properties ➔ Check **Unblock** ➔ Apply.*

### Run from Source
```bash
pip install requests beautifulsoup4
python uniscore.py
```
Or run **`Run-Uniscore.bat`**.

---

## 🔒 Privacy & Safety Guarantee
Your credentials and scraped grades are handled strictly locally and transmitted securely over SSL only to the official University of Colombo Student Information System portals (`https://sis.cmb.ac.lk/*`). No personal data is stored or sent to any third-party servers.

---

*Built with 💜 by **[Kasun Vishvajith](https://kasun-vishvajith.github.io/Portfolio/)***
>>>>>>> theirs
