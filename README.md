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

## 📦 How to Run

### Standalone Executable (Windows)
1. Run **`Uniscore.exe`** directly from the project directory.
2. *If flagged by Windows Smart App Control: Right-click `Uniscore.exe` ➔ Properties ➔ Check **Unblock** ➔ Apply.*

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
