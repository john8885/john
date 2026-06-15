"""FastAPI CRM 라우터"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from crm.database import get_db
from crm.models import Customer, Inquiry, Response, InquiryStatus, InquiryChannel

router = APIRouter()
templates = Jinja2Templates(directory="crm/templates")


# ─── 대시보드 ────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_customers = db.query(func.count(Customer.id)).scalar()
    total_inquiries = db.query(func.count(Inquiry.id)).scalar()
    open_inquiries = db.query(func.count(Inquiry.id)).filter(
        Inquiry.status == InquiryStatus.open
    ).scalar()
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_this_week = db.query(func.count(Inquiry.id)).filter(
        Inquiry.created_at >= week_ago
    ).scalar()
    recent = (
        db.query(Inquiry)
        .join(Customer)
        .order_by(desc(Inquiry.created_at))
        .limit(10)
        .all()
    )
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_customers": total_customers,
        "total_inquiries": total_inquiries,
        "open_inquiries": open_inquiries,
        "new_this_week": new_this_week,
        "recent_inquiries": recent,
    })


# ─── 고객 ────────────────────────────────────────────────────────────────────

@router.get("/customers", response_class=HTMLResponse)
def list_customers(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Customer)
    if q:
        query = query.filter(
            Customer.name.ilike(f"%{q}%") | Customer.email.ilike(f"%{q}%")
        )
    customers = query.order_by(desc(Customer.created_at)).all()
    return templates.TemplateResponse("customers.html", {
        "request": request, "customers": customers, "q": q
    })


@router.get("/customers/new", response_class=HTMLResponse)
def new_customer_form(request: Request):
    return templates.TemplateResponse("customer_form.html", {"request": request, "customer": None})


@router.post("/customers/new")
def create_customer(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    instagram_id: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
    c = Customer(name=name, email=email or None, phone=phone, instagram_id=instagram_id, memo=memo)
    db.add(c)
    db.commit()
    return RedirectResponse("/customers", status_code=303)


@router.get("/customers/{customer_id}", response_class=HTMLResponse)
def customer_detail(customer_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(404)
    return templates.TemplateResponse("customer_detail.html", {"request": request, "customer": c})


@router.post("/customers/{customer_id}/edit")
def edit_customer(
    customer_id: int,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    instagram_id: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(404)
    c.name, c.email, c.phone, c.instagram_id, c.memo = name, email or None, phone, instagram_id, memo
    c.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/customers/{customer_id}", status_code=303)


# ─── 문의 ────────────────────────────────────────────────────────────────────

@router.get("/inquiries", response_class=HTMLResponse)
def list_inquiries(
    request: Request,
    status: str = "",
    channel: str = "",
    q: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(Inquiry).join(Customer)
    if status:
        query = query.filter(Inquiry.status == status)
    if channel:
        query = query.filter(Inquiry.channel == channel)
    if q:
        query = query.filter(
            Inquiry.subject.ilike(f"%{q}%") | Inquiry.content.ilike(f"%{q}%")
            | Customer.name.ilike(f"%{q}%")
        )
    inquiries = query.order_by(desc(Inquiry.created_at)).all()
    return templates.TemplateResponse("inquiries.html", {
        "request": request,
        "inquiries": inquiries,
        "status_filter": status,
        "channel_filter": channel,
        "q": q,
        "statuses": [s.value for s in InquiryStatus],
        "channels": [c.value for c in InquiryChannel],
    })


@router.get("/inquiries/new", response_class=HTMLResponse)
def new_inquiry_form(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.name).all()
    return templates.TemplateResponse("inquiry_form.html", {
        "request": request,
        "customers": customers,
        "channels": [c.value for c in InquiryChannel],
    })


@router.post("/inquiries/new")
def create_inquiry(
    customer_id: int = Form(...),
    channel: str = Form("direct"),
    subject: str = Form(""),
    content: str = Form(...),
    assigned_to: str = Form(""),
    db: Session = Depends(get_db),
):
    inq = Inquiry(
        customer_id=customer_id,
        channel=channel,
        subject=subject,
        content=content,
        assigned_to=assigned_to,
    )
    db.add(inq)
    db.commit()
    return RedirectResponse(f"/inquiries/{inq.id}", status_code=303)


@router.get("/inquiries/{inquiry_id}", response_class=HTMLResponse)
def inquiry_detail(inquiry_id: int, request: Request, db: Session = Depends(get_db)):
    inq = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inq:
        raise HTTPException(404)
    return templates.TemplateResponse("inquiry_detail.html", {"request": request, "inquiry": inq})


@router.post("/inquiries/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    inq = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inq:
        raise HTTPException(404)
    inq.status = status
    inq.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/inquiries/{inquiry_id}", status_code=303)


@router.post("/inquiries/{inquiry_id}/respond")
def add_response(
    inquiry_id: int,
    author: str = Form(...),
    content: str = Form(...),
    is_internal: bool = Form(False),
    db: Session = Depends(get_db),
):
    inq = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inq:
        raise HTTPException(404)
    resp = Response(inquiry_id=inquiry_id, author=author, content=content, is_internal=is_internal)
    db.add(resp)
    if inq.status == InquiryStatus.open:
        inq.status = InquiryStatus.in_progress
    inq.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/inquiries/{inquiry_id}", status_code=303)
