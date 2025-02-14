# Import everything needed for the project
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
import pyqrcode
import shutil

app = Flask(__name__, instance_path=os.getcwd())

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Main.db'
db = SQLAlchemy(app)

# QR Code Storage Configuration
qrcode_folder = os.path.join('static', 'qrcodes')
app.config['UPLOAD_FOLDER'] = qrcode_folder  
qr_file_path = os.path.join(qrcode_folder, 'QRCODE.png')

if os.path.exists(qr_file_path):
    os.remove(qr_file_path)

app.secret_key = "secret_key"

# User Model
class Signin(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    email = db.Column(db.String(100), nullable=False, unique=True)  
    password = db.Column(db.String(200), nullable=False)  

    tasks = db.relationship('Todo', backref='signin', lazy=True, cascade="all, delete-orphan")

# Task Manager Model
class Todo(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    content = db.Column(db.String(200), nullable=False)  
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))  
    user_id = db.Column(db.Integer, db.ForeignKey('signin.id'), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

# Login Route
@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':  
        email = request.form["email"]
        password = request.form["password"]

        user = Signin.query.filter_by(email=email).first()
        if user:
            if password == user.password:  
                session["signed_in"] = True
                session["user_id"] = user.id  # Store the user ID in session
                return redirect('/')  
            else:
                return render_template("index.html", error_message="Wrong password", email=email)
        else:
            return redirect("/signup")

    return render_template("index.html", signed_in=session.get("signed_in", False))

# Home Route
@app.route("/home")
def home():
    if not session.get("signed_in"):
        return redirect("/")
    return render_template("home.html")

# Task Manager Route
@app.route("/taskmanager", methods=['POST', 'GET'])
def taskmanager():
    if not session.get("signed_in"):
        return redirect("/") 
     
    if request.method == 'POST':  
        task_content = request.form["content"]
        user_id = session["user_id"]

        new_task = Todo(content=task_content, user_id=user_id)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/taskmanager')
        except:
            return 'There was an issue adding your task'
    else:
        user_id = session["user_id"]
        tasks = Todo.query.filter_by(user_id=user_id).order_by(Todo.date_created).all()
        return render_template('taskmanager.html', tasks=tasks)

# Delete Task Route
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get("signed_in"):
        return redirect("/")  

    task_to_delete = Todo.query.get_or_404(id)
    
    if task_to_delete.user_id != session["user_id"]:
        return "You do not have permision to delete this task."

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/taskmanager')
    except:
        return 'There was an issue deleting that task'

# Update Task Route
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if not session.get("signed_in"):
        return redirect("/")  

    task = Todo.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "You do not have permision to update this task."

    if request.method == 'POST':
        task.content = request.form["content"]
        try:
            db.session.commit()
            return redirect('/taskmanager')
        except:
            return "There was an issue updating your task"
    else:
        return render_template("update.html", task=task)

# QR Code Generator Route
@app.route('/QRcode', methods=['POST', 'GET'])
def qrcode():
    if not session.get("signed_in"):
        return redirect("/")  
    
    if request.method == 'POST':
        qrcodestring = request.form['qrstring'].strip()
        
        if qrcodestring:
            if os.path.exists(qr_file_path):
                os.remove(qr_file_path)

            qrcode = pyqrcode.create(qrcodestring)
            temp_qr_path = 'QRCODE.png'
            qrcode.png(temp_qr_path, scale=10)  

            shutil.move(temp_qr_path, qr_file_path)
            return render_template('qrcode.html', user_qrcode=qr_file_path, qrcodestring=qrcodestring)
        else:
            return render_template('qrcode.html', qrcodenotvalid="This QR Code is not valid")

    return render_template('qrcode.html', user_qrcode=None)

# Signup Route
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists in the database
        existing_user = Signin.query.filter_by(email=email).first()
        if existing_user:
            return render_template('signup.html', error_message="Email address already in use.")

        # If the email doesn't exist, create a new user
        new_user = Signin(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/')

    return render_template('signup.html')


# Logout Route
@app.route("/logout")
def logout():
    session.pop("signed_in", None)
    session.pop("user_id", None)
    return redirect("/")

# Delete Account Route
@app.route("/delete_account")
def delete_account():
    if "user_id" not in session:
        return redirect("/")
    
    user_id = session["user_id"]
    login_detes = Signin.query.get_or_404(user_id)
    
    try:
        db.session.delete(login_detes)
        db.session.commit()
        session.pop("user_id", None)
        session.pop("signed_in", None)
        return redirect('/')
    except:
        return 'There was an issue deleting your account'

if __name__ == "__main__":
    app.run(debug=True)    