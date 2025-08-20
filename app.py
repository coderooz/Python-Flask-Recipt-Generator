from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
import os

# ---------- Config ----------
DB_URL = os.getenv("DATABASE_URL", "sqlite:///receipts.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

# ---------- Database ----------
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Receipt(Base):
    __tablename__ = "receipts"
    id = Column(Integer, primary_key=True)
    org_name = Column(String(120), nullable=False)
    org_address = Column(Text, nullable=True)
    org_phone = Column(String(50), nullable=True)
    org_email = Column(String(120), nullable=True)

    reg_no = Column(String(50), nullable=True)
    patient_name = Column(String(120), nullable=False)
    guardian_name = Column(String(120), nullable=True)
    address = Column(Text, nullable=True)
    gender_age = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    consultant = Column(String(120), nullable=True)

    item_desc = Column(String(200), default="Consultation Fees")
    amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# ---------- Routes ----------


@app.get("/")
def index():
    db = SessionLocal()
    receipts = db.query(Receipt).order_by(Receipt.created_at.desc()).limit(10).all()
    db.close()
    return render_template("index.html", receipts=receipts)


@app.post("/create")
def create():
    form = request.form
    r = Receipt(
        org_name=form.get("org_name", "Your Clinic"),
        org_address=form.get("org_address"),
        org_phone=form.get("org_phone"),
        org_email=form.get("org_email"),
        reg_no=form.get("reg_no"),
        patient_name=form["patient_name"],
        guardian_name=form.get("guardian_name"),
        address=form.get("address"),
        gender_age=form.get("gender_age"),
        phone=form.get("phone"),
        consultant=form.get("consultant"),
        item_desc=form.get("item_desc", "Consultation Fees"),
        amount=float(form.get("amount", 0) or 0),
        paid_amount=float(form.get("paid_amount", 0) or 0),
    )
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
        flash("Receipt not found", "error")
        return redirect(url_for("index"))
    return render_template("receipt.html", r=r)


@app.get("/receipt/<int:rid>/pdf")
def receipt_pdf(rid: int):
    db = SessionLocal()
    r = db.get(Receipt, rid)
    db.close()
    if not r:
        flash("Receipt not found", "error")
        return redirect(url_for("index"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elems = []

    # Header
    elems.append(Paragraph(f"<b>{r.org_name}</b>", styles["Title"]))
    meta_lines = []
    if r.org_address:
        meta_lines.append(r.org_address.replace("\n", "<br/>"))
    contact = " ".join(
        x for x in [r.org_phone or '', r.org_email or ''] if x).strip()
    if contact:
        meta_lines.append(contact)
    elems += [Paragraph("<br/>".join(meta_lines), styles["Normal"]), Spacer(1, 6)]

    # Info Table
    info = [
        ["Receipt Date", r.created_at.strftime("%Y-%m-%d %H:%M")],
        ["Registration No.", r.reg_no or "-"],
        ["Patient Name", r.patient_name],
        ["Guardian Name", r.guardian_name or "-"],
        ["Address", r.address or "-"],
        ["Gender/Age", r.gender_age or "-"],
        ["Phone", r.phone or "-"],
        ["Consultant", r.consultant or "-"],
    ]
    t1 = Table(info, colWidths=[40*mm, None])
    t1.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elems += [Spacer(1, 6), t1, Spacer(1, 12)]

    # Line Items
    items = [["Sl. No", "Particulars", "Amount (INR)"],["1", r.item_desc, f"{r.amount:,.2f}"]]
    t2 = Table(items, colWidths=[20*mm, None, 40*mm])
    t2.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
    ]))
    elems += [t2, Spacer(1, 6)]

    # Totals
    totals = [["Paid Amount", f"INR {r.paid_amount:,.2f}"]]
    t3 = Table(totals, colWidths=[None, 50*mm])
    t3.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
    ]))
    elems += [t3, Spacer(1, 12)]
    elems.append(Paragraph("This is a computer generated receipt.", styles["Italic"]))

    doc.build(elems)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"receipt_{r.id}.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
