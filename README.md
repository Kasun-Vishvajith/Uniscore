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