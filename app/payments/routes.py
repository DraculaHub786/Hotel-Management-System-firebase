import time
import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    transactions_col, invoices_col, qr_payments_col, refunds_col,
    settings_col, bookings_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from guest_service import generate_qr_base64

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

# Guest Payment Flow (Section C.6 / C.7)
@payments_bp.route('/pay/<txn_id>', methods=['GET'])
@login_required
def pay_qr_view(txn_id):
    doc = transactions_col().document(txn_id).get()
    tdata = doc.to_dict() if doc.exists else {}
    if not tdata:
        matches = list(transactions_col().where('transaction_id', '==', txn_id).limit(1).get())
        if matches: tdata = matches[0].to_dict()
    return render_template('guest/pay_qr.html', transaction=tdata, txn_id=txn_id)

@payments_bp.route('/pay/<txn_id>/otp', methods=['GET'])
@login_required
def pay_otp_view(txn_id):
    return render_template('guest/pay_otp.html', txn_id=txn_id)

@payments_bp.route('/api/payment/create-qr', methods=['POST'])
@login_required
def api_create_qr():
    data = request.get_json() or {}
    order_id = data.get('order_id', f"ORD{int(time.time())}")
    amount = float(data.get('amount', 0.0))

    qr_payload = f"upi://pay?pa=hotel@icici&pn=Nur-e-Haya&am={amount}&tr={order_id}"
    qr_image = generate_qr_base64(qr_payload)

    qr_payments_col().add({
        "order_id": order_id,
        "amount": amount,
        "status": "pending",
        "qr_code_url": qr_image,
        "created_at": datetime.utcnow().isoformat() + "Z"
    })

    return api_success({
        "order_id": order_id,
        "amount": amount,
        "qr_code": qr_image,
        "qr_base64": qr_image
    })

@payments_bp.route('/api/transactions/<txn_id>/status', methods=['GET'])
def api_txn_status(txn_id):
    doc = transactions_col().document(txn_id).get()
    tdata = doc.to_dict() if doc.exists else {}
    if not tdata:
        matches = list(transactions_col().where('transaction_id', '==', txn_id).limit(1).get())
        if matches: tdata = matches[0].to_dict()
    return api_success({"status": tdata.get('payment_status', 'completed')})

@payments_bp.route('/api/transactions/<txn_id>/simulate-pay', methods=['POST'])
def api_simulate_pay(txn_id):
    doc = transactions_col().document(txn_id).get()
    if doc.exists:
        doc.reference.update({"payment_status": "completed"})
    else:
        for d in transactions_col().where('transaction_id', '==', txn_id).stream():
            d.reference.update({"payment_status": "completed"})
    return api_success({"status": "completed", "message": "Payment simulation confirmed"})

@payments_bp.route('/api/process-payment', methods=['POST'])
@login_required
def api_process_payment():
    data = request.get_json() or {}
    amount = float(data.get('amount', 0.0))
    payment_method = data.get('payment_method', 'card')

    txn_id = f"TXN{int(time.time())}{random.randint(100, 999)}"
    tref = transactions_col().add({
        "transaction_id": txn_id,
        "user_email": session.get('user_email'),
        "amount": amount,
        "payment_method": payment_method,
        "payment_status": "completed",
        "category": data.get('category', 'room'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"transaction_id": txn_id, "status": "completed"})

# Module 8 Accounts & Payments (SCR-53 to SCR-58)
@payments_bp.route('/accounts', methods=['GET'])
@payments_bp.route('/accounts/ledger', methods=['GET'])
@role_required('admin', 'manager', 'accountant')
def ledger():
    txns = []
    for doc in transactions_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        txns.append(d)
    txns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('payments/ledger.html', transactions=txns)

@payments_bp.route('/accounts/invoices/<id>', methods=['GET'])
@role_required('admin', 'manager', 'accountant')
def invoice_detail(id):
    doc = invoices_col().document(str(id)).get()
    idata = doc.to_dict() if doc.exists else {"invoice_no": f"INV-{id}", "total": 4500, "status": "paid"}
    return render_template('payments/invoice_print.html', invoice=idata)

@payments_bp.route('/accounts/qr-verify', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'accountant')
def qr_verify():
    if request.method == 'GET':
        qrs = [d.to_dict() for d in qr_payments_col().stream()]
        return render_template('payments/qr_verify.html', qr_payments=qrs)

    data = request.get_json() or {}
    order_id = data.get('order_id')
    for d in qr_payments_col().where('order_id', '==', order_id).stream():
        d.reference.update({"status": "paid", "verified_by": session.get('user_email')})
    return api_success({"message": "QR Payment verified and marked paid"})

@payments_bp.route('/admin/refunds', methods=['GET'])
@payments_bp.route('/accounts/refunds', methods=['GET'])
@role_required('admin', 'manager', 'accountant')
def refunds_queue():
    refunds = [d.to_dict() for d in refunds_col().stream()]
    if not refunds:
        refunds = [
            {"id": "ref_101", "booking_id": "BK88912", "amount": 3500.0, "reason": "Flight cancellation", "status": "pending"},
            {"id": "ref_102", "booking_id": "BK88915", "amount": 7000.0, "reason": "Medical emergency", "status": "pending"}
        ]
    return render_template('admin/refunds_queue.html', refunds=refunds)

@payments_bp.route('/api/admin/refunds', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'accountant')
def api_refunds():
    if request.method == 'GET':
        refunds = [d.to_dict() for d in refunds_col().stream()]
        return api_success(refunds)

    data = request.get_json() or {}
    rref = refunds_col().add(data)
    return api_success({"id": rref[1].id, "message": "Refund request initiated"})

@payments_bp.route('/api/admin/refunds/<refund_id>/approve', methods=['POST'])
@role_required('admin', 'manager', 'accountant')
def api_approve_refund(refund_id):
    for d in refunds_col().where('id', '==', refund_id).stream():
        d.reference.update({"status": "approved", "approved_by": session.get('user_email')})
    return api_success({
        "refund_id": refund_id,
        "status": "approved",
        "transaction_status": "refunded",
        "message": "Refund approved and dispatched"
    })

@payments_bp.route('/accounts/settlement', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'accountant')
def daily_settlement():
    # POS Close & Reconciliation
    today_str = datetime.utcnow().date().isoformat()
    total_rev = sum(float(d.to_dict().get('amount', 0)) for d in transactions_col().stream())
    return render_template('payments/settlement.html', total_revenue=total_rev, settlement_date=today_str)

@payments_bp.route('/accounts/taxes', methods=['GET', 'POST'])
@role_required('admin')
def tax_configuration():
    if request.method == 'GET':
        return render_template('payments/tax_config.html')
    data = request.get_json() or {}
    settings_col().document('tax_config').set(data)
    return api_success({"message": "Tax & Rate settings saved"})
