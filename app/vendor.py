from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Vendor, MenuItem
from app.forms import VendorForm, MenuItemForm
from functools import wraps

vendor_bp = Blueprint('vendor', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@vendor_bp.route('/vendors')
@login_required
@admin_required
def vendor_list():
    vendors = Vendor.query.all()
    return render_template('vendor/list.html', vendors=vendors)

@vendor_bp.route('/vendors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_vendor():
    form = VendorForm()
    if form.validate_on_submit():
        vendor = Vendor(
            name=form.name.data,
            contact_email=form.contact_email.data,
            phone=form.phone.data,
            cuisine_type=form.cuisine_type.data,
            order_deadline=form.order_deadline.data
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor added successfully!', 'success')
        return redirect(url_for('vendor.vendor_list'))
    return render_template('vendor/form.html', form=form, title='Add Vendor')

@vendor_bp.route('/vendors/<int:vendor_id>/toggle')
@login_required
@admin_required
def toggle_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.is_active = not vendor.is_active
    db.session.commit()
    status = 'activated' if vendor.is_active else 'deactivated'
    flash(f'{vendor.name} has been {status}.', 'success')
    return redirect(url_for('vendor.vendor_list'))

@vendor_bp.route('/vendors/<int:vendor_id>/menu', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_menu(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    form = MenuItemForm()
    if form.validate_on_submit():
        item = MenuItem(
            vendor_id=vendor.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            dietary_tag=form.dietary_tag.data,
            is_available=form.is_available.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Menu item added!', 'success')
        return redirect(url_for('vendor.manage_menu', vendor_id=vendor.id))
    items = MenuItem.query.filter_by(vendor_id=vendor.id).all()
    return render_template('vendor/menu.html', vendor=vendor, form=form, items=items)

@vendor_bp.route('/vendors/menu/<int:item_id>/toggle')
@login_required
@admin_required
def toggle_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    flash('Item updated.', 'success')
    return redirect(url_for('vendor.manage_menu', vendor_id=item.vendor_id))