from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import TextAreaField, FloatField, SelectField, TimeField, TelField
from wtforms.validators import Optional

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class VendorForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired(), Length(max=100)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone Number', validators=[DataRequired()])
    cuisine_type = SelectField('Cuisine Type', choices=[
        ('local', 'Local Ghanaian'),
        ('continental', 'Continental'),
        ('fastfood', 'Fast Food'),
        ('chinese', 'Chinese'),
        ('other', 'Other')
    ])
    order_deadline = TimeField('Order Deadline', validators=[Optional()])
    submit = SubmitField('Save Vendor')

class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    price = FloatField('Price (GHS)', validators=[DataRequired()])
    dietary_tag = SelectField('Dietary Tag', choices=[
        ('', 'None'),
        ('vegetarian', 'Vegetarian'),
        ('halal', 'Halal'),
        ('gluten-free', 'Gluten Free'),
        ('vegan', 'Vegan')
    ])
    is_available = BooleanField('Available today', default=True)
    submit = SubmitField('Save Item')
