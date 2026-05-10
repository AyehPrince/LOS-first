from flask import Blueprint, render_template, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Invoice, Order, OrderItem, Vendor
from app.vendor import admin_required
from datetime import date, datetime
import csv
import io

invoices_bp = Blueprint('invoices', __name__)

def calculate_vendor_total(vendor_id, start_date, end_date):
    orders = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= datetime.combine(start_date, datetime.min.time()),
        Order.created_at <= datetime.combine(end_date, datetime.max.time())
    ).all()
    total = 0
    for order in orders:
        for item in order.items:
            total += item.menu_item.price * item.quantity
    return round(total, 2)

@invoices_bp.route('/invoices')
@login_required
@admin_required
def invoice_list():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    vendors = Vendor.query.filter_by(is_active=True).all()
    return render_template('invoices/list.html', invoices=invoices, vendors=vendors)

@invoices_bp.route('/invoices/generate', methods=['POST'])
@login_required
@admin_required
def generate_invoice():
    from flask import request
    vendor_id = request.form.get('vendor_id')
    period_start = request.form.get('period_start')
    period_end = request.form.get('period_end')

    if not vendor_id or not period_start or not period_end:
        flash('Please fill in all fields.', 'danger')
        return redirect(url_for('invoices.invoice_list'))

    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)

    if end < start:
        flash('End date cannot be before start date.', 'danger')
        return redirect(url_for('invoices.invoice_list'))

    total = calculate_vendor_total(int(vendor_id), start, end)

    invoice = Invoice(
        vendor_id=int(vendor_id),
        period_start=start,
        period_end=end,
        total_amount=total,
        status='unpaid'
    )
    db.session.add(invoice)
    db.session.commit()
    flash('Invoice generated successfully!', 'success')
    return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<int:invoice_id>')
@login_required
@admin_required
def invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    orders = Order.query.filter(
        Order.vendor_id == invoice.vendor_id,
        Order.created_at >= datetime.combine(invoice.period_start, datetime.min.time()),
        Order.created_at <= datetime.combine(invoice.period_end, datetime.max.time())
    ).all()
    return render_template('invoices/detail.html', invoice=invoice, orders=orders)

@invoices_bp.route('/invoices/<int:invoice_id>/mark-paid')
@login_required
@admin_required
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'paid'
    db.session.commit()
    flash('Invoice marked as paid.', 'success')
    return redirect(url_for('invoices.invoice_list'))

@invoices_bp.route('/invoices/<int:invoice_id>/export')
@login_required
@admin_required
def export_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    orders = Order.query.filter(
        Order.vendor_id == invoice.vendor_id,
        Order.created_at >= datetime.combine(invoice.period_start, datetime.min.time()),
        Order.created_at <= datetime.combine(invoice.period_end, datetime.max.time())
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Invoice ID', invoice.id])
    writer.writerow(['Vendor', invoice.vendor.name])
    writer.writerow(['Period', '{} to {}'.format(invoice.period_start, invoice.period_end)])
    writer.writerow(['Status', invoice.status.upper()])
    writer.writerow(['Total Amount', 'GHS {:.2f}'.format(invoice.total_amount)])
    writer.writerow([])
    writer.writerow(['Order ID', 'Employee', 'Item', 'Qty', 'Unit Price', 'Subtotal', 'Date'])

    for order in orders:
        for oi in order.items:
            writer.writerow([
                order.id,
                order.employee.name,
                oi.menu_item.name,
                oi.quantity,
                'GHS {:.2f}'.format(oi.menu_item.price),
                'GHS {:.2f}'.format(oi.menu_item.price * oi.quantity),
                order.created_at.strftime('%d %b %Y %I:%M %p')
            ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=invoice_{}.csv'.format(invoice.id)
    response.headers['Content-Type'] = 'text/csv'
    return response