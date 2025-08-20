from datetime import datetime
from io import BytesIO
import json
import os

from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, flash
)
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, Text
)
from sqlalchemy.orm import sessionmaker, declarative_base

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate
)
from reportlab.lib.styles import getSampleStyleSheet

# ------------------ Config ------------------
DB_URL = os.getenv("DATABASE_URL", "sqlite:///receipts.db")
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ------------------ App ------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

# ------------------ Database ------------------
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Receipt(Base):
    __tablename__ = "receipts"
    id = Column(Integer, primary_key=True)

    # Organization (snapshotted onto each receipt)
    org_name = Column(String(120), nullable=False)
    org_address = Column(Text, nullable=True)
    org_phone = Column(String(50), nullable=True)
    org_email = Column(String(120), nullable=True)

    # Receipt / client details
    registration_no = Column(String(50), nullable=True)
    name = Column(String(120), nullable=False)
    guardian = Column(String(120), nullable=True)
    address = Column(Text, nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(50), nullable=True)
    consultant = Column(String(120), nullable=True)

    # Line item
    item_desc = Column(String(200), default="Consultation Fees")
    amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ------------------ Guards ------------------
@app.before_request
def ensure_config():
    # Allow access to setup, static, and favicon even if not configured yet
    if request.endpoint in {"setup_get", "setup_post", "static"}:
        return
    cfg = load_config()
    if not cfg:
        return redirect(url_for("setup_get"))

# ------------------ Routes ------------------
@app.get("/setup")
def setup_get():
    cfg = load_config()
    return render_template("setup.html", cfg=cfg)

@app.post("/setup")
def setup_post():
    form = request.form
    cfg = {
        "org_name": form.get("org_name", "").strip(),
        "org_address": form.get("org_address", "").strip(),
        "org_phone": form.get("org_phone", "").strip(),
        "org_email": form.get("org_email", "").strip(),
    }
    if not cfg["org_name"]:
        flash("Organization/Clinic name is required.", "error")
        return redirect(url_for("setup_get"))
    save_config(cfg)
    flash("Organization settings saved.", "success")
    return redirect(url_for("index"))

@app.get("/")
def index():
    db = SessionLocal()
    receipts = db.query(Receipt).order_by(Receipt.created_at.desc()).limit(12).all()
    db.close()
    cfg = load_config()
    return render_template("index.html", receipts=receipts, cfg=cfg)

@app.post("/create")
def create():
    cfg = load_config()
    if not cfg:
        return redirect(url_for("setup_get"))

    form = request.form
    # Parse numeric fields safely
    def to_float(v, default=0.0):
        try: return float(v)
        except: return default
    def to_int(v, default=None):
        try: return int(v)
        except: return default

    r = Receipt(
        # Snapshot org info at time of creation
        org_name=cfg.get("org_name", ""),
        org_address=cfg.get("org_address"),
        org_phone=cfg.get("org_phone"),
        org_email=cfg.get("org_email"),

        # Client / receipt details
        registration_no=form.get("registration_no"),
        name=form.get("name", "").strip(),
        guardian=form.get("guardian"),
        address=form.get("address"),
        gender=form.get("gender"),
        age=to_int(form.get("age")),
        phone=form.get("phone"),
        consultant=form.get("consultant"),

        # Line item
        item_desc=form.get("item_desc", "Consultation Fees"),
        amount=to_float(form.get("amount", 0)),
        paid_amount=to_float(form.get("paid_amount", 0)),
    )
    if not r.name:
        flash("Name is required.", "error")
        return redirect(url_for("index"))

    db = SessionLocal()
    db.add(r)
    db.commit()
    rid = r.id
    db.close()
    flash("Receipt saved.", "success")
    return redirect(url_for("preview", rid=rid))

@app.get("/receipt/<int:rid>")
def preview(rid: int):
    db = SessionLocal()
    r = db.get(Receipt, rid)
    db.close()
    if not r:
        flash("Receipt not found.", "error")
        return redirect(url_for("index"))
    return render_template("receipt.html", r=r)

@app.get("/receipt/<int:rid>/pdf")
def receipt_pdf(rid: int):
    db = SessionLocal()
    r = db.get(Receipt, rid)
    db.close()
    if not r:
        flash("Receipt not found.", "error")
        return redirect(url_for("index"))

    # ---- Generate PDF ----
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()
    elems = []

    # Header (Org)
    elems.append(Paragraph(f"<b>{r.org_name}</b>", styles["Title"]))
    meta = []
    if r.org_address: meta.append(r.org_address.replace("\n", "<br/>"))
    contact = " ".join(x for x in [r.org_phone or "", r.org_email or ""] if x).strip()
    if contact: meta.append(contact)
    if meta:
        elems.append(Paragraph("<br/>".join(meta), styles["Normal"]))
    elems.append(Spacer(1, 8))

    # Meta table (date / reg no)
    meta_table = [
        ["Receipt Date", r.created_at.strftime("%Y-%m-%d %H:%M")],
        ["Registration No.", r.registration_no or "-"],
    ]
    t_meta = Table(meta_table, colWidths=[40*mm, None])
    t_meta.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elems += [t_meta, Spacer(1, 10)]

    # Client table
    info = [
        ["Name", r.name],
        ["Guardian", r.guardian or "-"],
        ["Gender", r.gender or "-"],
        ["Age", str(r.age) if r.age is not None else "-"],
        ["Address", r.address or "-"],
        ["Phone", r.phone or "-"],
        ["Consultant", r.consultant or "-"],
    ]
    t1 = Table(info, colWidths=[35*mm, None])
    t1.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 0.5, colors.black),("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),("VALIGN", (0,0), (-1,-1), "TOP"),]))
    elems += [t1, Spacer(1, 12)]

    # Line item table
    items = [["Sl. No", "Particulars", "Amount (INR)"],
             ["1", r.item_desc, f"{r.amount:,.2f}"]]
    t2 = Table(items, colWidths=[20*mm, None, 40*mm])
    t2.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 0.7, colors.black),("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),("BACKGROUND", (0,0), (-1,0), colors.lightgrey),("ALIGN", (2,1), (2,-1), "RIGHT"),]))
    elems += [t2, Spacer(1, 6)]

    # Totals
    totals = [["Paid Amount", f"INR {r.paid_amount:,.2f}"]]
    t3 = Table(totals, colWidths=[None, 55*mm])
    t3.setStyle(TableStyle([("ALIGN", (1,0), (1,-1), "RIGHT"),("FONTSIZE", (0,0), (-1,-1), 12),]))
    elems += [t3, Spacer(1, 14)]
    elems.append(Paragraph("This is a computer generated receipt.", styles["Italic"]))

    doc.build(elems)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"receipt_{r.id}.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
