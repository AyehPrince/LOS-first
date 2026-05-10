from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models import Employee
from app.forms import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = Employee.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        hashed_pw = generate_password_hash(form.password.data)
        new_employee = Employee(
            name=form.name.data,
            email=form.email.data,
            password=hashed_pw
        )
        db.session.add(new_employee)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(email=form.email.data).first()
        if employee and check_password_hash(employee.password, form.password.data):
            login_user(employee, remember=form.remember.data)
            flash('Welcome back, {}!'.format(employee.name), 'success')
            return redirect(url_for('main.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))