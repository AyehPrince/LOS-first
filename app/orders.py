from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from app.models import Vendor, MenuItem, Order, OrderItem
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/browse')
@login_required
def browse():
    vendors = Vendor.query.filter_by(is_active=True).all()
    return render_template('orders/browse.html', vendors=vendors)

@orders_bp.route('/browse/<int:vendor_id>')
@login_required
def view_menu(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if not vendor.is_active:
        flash('This vendor is not currently available.', 'danger')
        return redirect(url_for('orders.browse'))
    items = MenuItem.query.filter_by(vendor_id=vendor_id, is_available=True).all()
    cart = session.get('cart', {})
    return render_template('orders/menu.html', vendor=vendor, items=items, cart=cart)

@orders_bp.route('/cart/add/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item = MenuItem.query.get_or_404(item_id)
    vendor = Vendor.query.get(item.vendor_id)

    if vendor.order_deadline and datetime.now().time() > vendor.order_deadline:
        flash('Sorry, ordering is closed for {} today.'.format(vendor.name), 'danger')
        return redirect(url_for('orders.view_menu', vendor_id=vendor.id))

    cart = session.get('cart', {})

    if cart and str(item.vendor_id) != str(list(cart.values())[0].get('vendor_id')):
        flash('You can only order from one vendor at a time. Clear your cart first.', 'warning')
        return redirect(url_for('orders.view_menu', vendor_id=vendor.id))

    key = str(item_id)
    if key in cart:
        cart[key]['quantity'] += 1
    else:
        cart[key] = {
            'name': item.name,
            'price': item.price,
            'quantity': 1,
            'vendor_id': item.vendor_id,
            'vendor_name': vendor.name
        }

    session['cart'] = cart
    flash('{} added to cart!'.format(item.name), 'success')
    return redirect(url_for('orders.view_menu', vendor_id=vendor.id))

@orders_bp.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    key = str(item_id)
    if key in cart:
        del cart[key]
        session['cart'] = cart
        flash('Item removed from cart.', 'info')
    return redirect(url_for('orders.cart'))

@orders_bp.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    total = sum(i['price'] * i['quantity'] for i in cart.values())
    return render_template('orders/cart.html', cart=cart, total=total)

@orders_bp.route('/cart/clear')
@login_required
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared.', 'info')
    return redirect(url_for('orders.browse'))

@orders_bp.route('/order/submit', methods=['POST'])
@login_required
def submit_order():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('orders.browse'))

    first_item = list(cart.values())[0]
    vendor_id = first_item['vendor_id']
    vendor = Vendor.query.get(vendor_id)

    if vendor.order_deadline and datetime.now().time() > vendor.order_deadline:
        flash('Sorry, the order deadline has passed for {}.'.format(vendor.name), 'danger')
        return redirect(url_for('orders.cart'))

    order = Order(
        employee_id=current_user.id,
        vendor_id=vendor_id,
        status='pending'
    )
    db.session.add(order)
    db.session.flush()

    for item_id, details in cart.items():
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=int(item_id),
            quantity=details['quantity']
        )
        db.session.add(order_item)

    db.session.commit()
    session.pop('cart', None)
    flash('Order placed successfully! 🎉', 'success')
    return redirect(url_for('orders.my_orders'))

@orders_bp.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(employee_id=current_user.id)\
                        .order_by(Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)