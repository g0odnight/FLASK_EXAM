from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('groups', lazy=True))

    def __init__(self, name, description, user_id):
        self.name = name
        self.description = description
        self.user_id = user_id
        
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship('Group', backref=db.backref('bills', lazy=True))

    def __init__(self, description, date, amount, group_id):
        self.description = description
        self.date = date
        self.amount = amount
        self.group_id = group_id

with app.app_context():
     db.create_all()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['password2']
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already in use')
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('groups'))
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html', current_user=current_user)

@app.route('/groups', methods=['GET', 'POST'])
def groups():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        group = Group(name=name, description=description, user_id=session['user_id'])
        db.session.add(group)
        db.session.commit()
    groups = Group.query.all()
    return render_template('groups.html', groups=groups)

@app.template_filter('date')
def format_date(date, format='%Y-%m-%d'):
    return datetime.strftime(date, format)

@app.route('/groups/<int:group_id>/bills', methods=['GET', 'POST'])
def bills(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        amount = float(request.form['amount'])
        bill = Bill(description=description, date=date, amount=amount, group_id=group_id)
        db.session.add(bill)
        db.session.commit()
    group = Group.query.get_or_404(group_id)
    bills = Bill.query.filter_by(group_id=group_id).all()
    return render_template('bills.html', group=group, bills=bills)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
