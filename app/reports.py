from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from app.models import Order, OrderItem, Employee, Vendor
from app.vendor import admin_required
from datetime import datetime, date
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@admin_required
def dashboard():
    # Filters
    vendor_id = request.args.get('vendor_id', type=int)
    employee_id = request.args.get('employee_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Order.query

    if vendor_id:
        query = query.filter(Order.vendor_id == vendor_id)
    if employee_id:
        query = query.filter(Order.employee_id == employee_id)
    if start_date:
        query = query.filter(Order.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Order.created_at <= datetime.combine(
            date.fromisoformat(end_date), datetime.max.time()
        ))

    orders = query.order_by(Order.created_at.desc()).all()

    # Summary stats
    total_orders = len(orders)
    total_spend = 0
    for order in orders:
        for item in order.items:
            total_spend += item.menu_item.price * item.quantity
    total_spend = round(total_spend, 2)

    # Per vendor breakdown
    vendor_totals = {}
    for order in orders:
        vname = order.vendor.name
        if vname not in vendor_totals:
            vendor_totals[vname] = {'orders': 0, 'spend': 0}
        vendor_totals[vname]['orders'] += 1
        for item in order.items:
            vendor_totals[vname]['spend'] += item.menu_item.price * item.quantity

    # Per employee breakdown
    employee_totals = {}
    for order in orders:
        ename = order.employee.name
        if ename not in employee_totals:
            employee_totals[ename] = {'orders': 0, 'spend': 0}
        employee_totals[ename]['orders'] += 1
        for item in order.items:
            employee_totals[ename]['spend'] += item.menu_item.price * item.quantity

    vendors = Vendor.query.all()
    employees = Employee.query.all()

    return render_template('reports/dashboard.html',
        orders=orders,
        total_orders=total_orders,
        total_spend=total_spend,
        vendor_totals=vendor_totals,
        employee_totals=employee_totals,
        vendors=vendors,
        employees=employees,
        selected_vendor=vendor_id,
        selected_employee=employee_id,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/reports/export')
@login_required
@admin_required
def export_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Order ID', 'Employee', 'Vendor', 'Item', 'Qty', 'Unit Price', 'Subtotal', 'Status', 'Date'])

    for order in orders:
        for oi in order.items:
            writer.writerow([
                order.id,
                order.employee.name,
                order.vendor.name,
                oi.menu_item.name,
                oi.quantity,
                'GHS {:.2f}'.format(oi.menu_item.price),
                'GHS {:.2f}'.format(oi.menu_item.price * oi.quantity),
                order.status.capitalize(),
                order.created_at.strftime('%d %b %Y %I:%M %p')
            ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=orders_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@reports_bp.route('/reports/orders/<int:order_id>/status/<string:status>')
@login_required
@admin_required
def update_order_status(order_id, status):
    from flask import redirect, url_for, flash
    from app import db
    allowed = ['pending', 'confirmed', 'delivered', 'cancelled']
    if status not in allowed:
        flash('Invalid status.', 'danger')
        return redirect(url_for('reports.dashboard'))
    from app.models import Order
    order = Order.query.get_or_404(order_id)
    order.status = status
    db.session.commit()
    flash('Order #{} marked as {}.'.format(order.id, status.capitalize()), 'success')
    return redirect(url_for('reports.dashboard'))