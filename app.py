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

# Task Manager Model
class Todo(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    content = db.Column(db.String(200), nullable=False)  
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))  

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
                return redirect('/home')  
            else:
                return 'Invalid Password'
        else:
            return 'Invalid Email'

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
    if request.method == 'POST':  
        task_content = request.form["content"]
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/taskmanager')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('taskmanager.html', tasks=tasks)

# Delete Task Route
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/taskmanager')
    except:
        return 'There was an issue deleting that task'

# Update Task Route
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

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


