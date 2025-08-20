# 🧾 Python Flask Receipt Generator

A simple yet powerful **Receipt Generator** built with **Python (Flask)**, **SQLite**, and **ReportLab**.  
This tool allows you to create receipts through a clean web UI, store them locally, and export professional **PDF receipts**.

---

## 📂 Repository
[GitHub: coderooz/Python-Flask-Recipt-Generator](https://github.com/coderooz/Python-Flask-Recipt-Generator)

---

## 🚀 Features
- Web-based UI for creating receipts
- Local storage using **SQLite**
- Professional **A4 PDF receipts** via ReportLab
- Clean dark-themed interface
- Two versions available:
  - **Version 1**: Basic form with all fields (organization details must be entered every time)
  - **Version 2**: Improved UI + persistent organization setup (saved once in `config.json`)

---

## 📦 Requirements
- Python 3.9+
- Virtual environment recommended

Install dependencies:

```bash
pip install -r requirements.txt
````

---

## ▶️ Running the Project

```bash
python app.py
```

Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📖 Versions

### 🔹 Version 1 (Basic)

* Organization details are entered **with each receipt**.
* Simple UI for quick setup.
* Good for quick demos or one-off use.

<details>
<summary>Click to view details</summary>

**Main files:**

* `app.py`
* `templates/base.html`
* `templates/index.html`
* `templates/receipt.html`

**Flow:**

1. User fills **organization + patient details** together.
2. Data is saved in **SQLite**.
3. Receipts can be **previewed** and **downloaded as PDF**.

</details>

---

### 🔹 Version 2 (Improved)

* Organization details set **once at startup** via `/setup` (saved to `config.json`).
* Receipts auto-include org info from config.
* Cleaner UI with:

  * Separate **Gender** and **Age** fields
  * More generic labels (`Name`, `Guardian`, `Consultant`, etc.)
  * Modern card/grid-based design
* Flash messages for better feedback
* Polished PDF export

<details>
<summary>Click to view details</summary>

**Main additions:**

* `setup.html` – one-time org setup page
* `static/style.css` – global modern styling
* `config.json` – auto-saved org settings

**Flow:**

1. First run → redirected to `/setup`.
2. Save org/clinic info.
3. Create receipts with **only client details**.
4. Preview receipt and **Download PDF**.

</details>

---

## 📷 Screenshots

### Version 1

*Form + Receipt Preview*
![Version 1 Screenshot](https://github.com/coderooz/Python-Flask-Recipt-Generator/blob/main/screenshots/Receipt-Maker%20-%20Home.png)

### Version 2

*Setup + Modernized UI*
![Version 2 Screenshot](https://github.com/coderooz/Python-Flask-Recipt-Generator/blob/main/screenshots/Recipt-Home Page(Receipt-Maker V2).png)

---

## 🛠️ Tech Stack

* **Backend:** Flask
* **Database:** SQLite (via SQLAlchemy ORM)
* **PDF:** ReportLab
* **Frontend:** Jinja2 templates + custom CSS (dark theme)

---

## 📌 Roadmap

* [ ] Add MongoDB option
* [ ] Add multiple line items per receipt
* [ ] Export receipts history
* [ ] Deployable via Docker

---

## 📜 License

[MIT License](/LICENSE) © [coderooz](https://github.com/coderooz)

---
