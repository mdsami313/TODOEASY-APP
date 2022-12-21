from flask import Flask, render_template, request, redirect, flash, url_for
from flask_paginate import Pagination, get_page_args
from flask_login import UserMixin, LoginManager, login_required, logout_user, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

date = datetime.now()
hour = date.strftime("%I")
min = date.strftime("%M")
md = date.strftime("%p")


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mytodoapp'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    todo = db.relationship('Todo', backref='user')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(15), nullable=False)
    desc = db.Column(db.String(15), nullable=False)
    time = db.Column(db.String(15), default=f"{hour}:{min} {md}")
    current_usr_id = db.Column(db.Integer, db.ForeignKey('user.id'))


def get_users(offset=0, per_page=10):
    if current_user.is_authenticated:
        todo = Todo.query.filter_by(current_usr_id=current_user.id).all()
    return todo[offset: offset+per_page]

@app.route('/')
def dash():
    return render_template('dash.html')

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    todo = Todo.query.all()
    db.create_all()
    page, per_page, offset = get_page_args(page_parameter="page", per_page_parameter="per_page")

    total = len(todo)
    pagination_users = get_users(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    if request.method == "POST":
        title = request.form['title']
        desc = request.form['desc']

        # print(title)
        # print(desc)

        if title == "" and desc == "":
            flash("Title And Description Cannot Be Empty!")
        elif title == "":
            flash("Title Cannot Be Empty!")
        elif desc == "":
            flash("Description Cannot Be Empty!")
            print(desc)
        else:
            todo = Todo(title=title, desc=desc, current_usr_id=current_user.id)
            db.session.add(todo)
            db.session.commit()

        return redirect(url_for('home'))


    return render_template("index.html", todos=pagination_users, pagination=pagination, page=page, per_page=per_page, current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])    
def register():
    if request.method == "POST":
        email = request.form['email']
        pswd = request.form['password']
        conf_pswd = request.form['conf-password']
        user = User.query.filter_by(email=email).first()

        if email == "":
            flash("Email Field Cannot Be Empty!")

        if email != "":
            if user == None:
                pass
            elif user.email == email:
                flash("Please Enter Different email it already exists!")
        if pswd != "":
            if len(pswd) < 5:
                flash("Too Short Password! Try Different One.")
        else:
            if pswd == conf_pswd and len(pswd) > 5:
                hash_pass = generate_password_hash(password=pswd, method='pbkdf2:sha256')
                users = User(email=email, password=hash_pass)
                db.session.add(users)
                db.session.commit()
                db.session.close_all()
                print("Added Into Database")
                return redirect(url_for('login'))
            elif conf_pswd != pswd:
                flash("Confirm Password Must Be Same!")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])    
def login():
    if request.method == "POST":
        email = request.form['email']
        pswd = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if email != "":
            if user == None:
                flash("Email Does Not Exist, Register new account!")

        if user:
            if check_password_hash(user.password, pswd):
                login_user(user)
                # print("Looged in")
                # print(current_user.id)
                return redirect(url_for('home'))
            else:
                flash("Incorrect Password! Try Again")
    return render_template("login.html")

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    # print("Logged Out")
    return redirect(url_for('dash'))

@app.route("/edit/<int:sno>", methods=['GET', 'POST'])
@login_required
def edit(sno):
    todo = Todo.query.filter_by(id=sno).first()
    if request.method == 'POST':     
        title = request.form['title']
        desc = request.form['desc']
        if request.method == "POST":
            todo = Todo.query.filter_by(id=sno).first()
            todo.title = title
            todo.desc = desc
            db.session.add(todo)
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit.html', todo=todo)

@app.route("/delete/<int:sno>")
@login_required
def delete(sno):
    todo = Todo.query.filter_by(id=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))


if __name__=='__main__':
    app.run(debug=True, port=8080)