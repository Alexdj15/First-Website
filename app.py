# Import everthing needed for the project
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
import pyqrcode
import shutil


app = Flask(__name__, instance_path=os.getcwd())

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Main.db'
db = SQLAlchemy(app)



qrcode_folder = os.path.join('static', 'qrcodes')  # Sets thefolder for QR codes
app.config['UPLOAD_FOLDER'] = qrcode_folder  
qr_file_path = os.path.join(qrcode_folder, 'QRCODE.png') # Sets the qrcode file path for future use

if os.path.exists(qr_file_path):  # Automatically deletes the QR code if it already exists on server start
    os.remove(qr_file_path)

app.secret_key = "secret_key"

class Signin(db.Model):  #  Sets up the signin database as a class
    # Each one of these columns corresponds to a column in the database and creates a seperate data point with each of these data points in columns
    id = db.Column(db.Integer, primary_key=True) # Gives each task a unique ID to make sure that tasks with the same name can be used
    email = db.Column(db.String(100), nullable=False) # Stores the username
    password = db.Column(db.String(200), nullable=False) # Stores the password

class Todo(db.Model):  #  Sets up the task manager database as a class
    # Each one of these columns corresponds to a column in the database and creates a seperate data point with each of these data points in columns
    id = db.Column(db.Integer, primary_key=True) # Gives each task a unique ID to make sure that tasks with the same name can be used
    content = db.Column(db.String(200), nullable=False) # Stores the content of the task
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc)) # Stores the date created

    def __repr__(self):
        return '<Task%r>' % self.id


@app.route("/" , methods=['POST', 'GET'])
def index():
    if request.method == 'POST': # Checks if the form has been submitted
        email = request.form["email"] # Gets the email of the user
        password = request.form["password"] # Gets the password of the user

        user = Signin.query.filter_by(email=email).first() # Checks if the user exists
        if user: # If the user exists
            if password == user.password: # Checks if the password matches
                session["signed_in"] = True
                return redirect('/home') # Redirects to the home page
            else: # If the password doesn't match
                return 'Invalid Password' # Returns an error message
        else: # If the user doesn't exist
            return 'Invalid Email' # Returns an error message

    return render_template("index.html", signed_in=session.get("signed_in", False)) # Renders the home/main page

@app.route("/taskmanager", methods=['POST', 'GET'])
def taskmanager():
    if request.method == 'POST': # Checks if the form has been submitted
        task_content = request.form["content"] # Gets the content of the task
        new_task = Todo(content=task_content) # Creates a new task

        try: # Attempts to add the task
            db.session.add(new_task) # Adds the task
            db.session.commit() # Commits the task
            return redirect('/taskmanager') # Redirects to the task manager page
        except:
            return 'There was an issue adding your task' # If there is a issue adding the task an error message will appear

    else:
        tasks = Todo.query.order_by(Todo.date_created).all() # Orders the tasks on the page by date created
        return render_template('taskmanager.html', tasks=tasks) # Renders the task manager page

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id) # Attempts to get the task for deletion

    try: # Attempts to delete the task
        db.session.delete(task_to_delete) # Deletes the task
        db.session.commit() # Commits the deletion
        return redirect('/taskmanager') # Redirects to the task manager
    except:
        return 'There was an issue deleting that task' # If there was an issue with deletion an error message will appear

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
    
@app.route('/QRcode', methods=['POST', 'GET'])
def qrcode():
    if not session.get("signed_in"):  # Check if user is signed in
        return redirect("/")  # Redirect to login page if not signed in
    if request.method == 'POST':
        qrcodestringhtml = request.form['qrstring']
        qrcodestring = request.form['qrstring'].strip()  # Get and clean the input by removing spaces incase the user pressed space and then entered a string of just spaces
        
        if qrcodestring != '':  # Checks if input is valid and deletes the existing QR code before creating a new one
            if os.path.exists(qr_file_path):
                os.remove(qr_file_path)

            qrcode = pyqrcode.create(qrcodestring)  # Generates the QR code
            temp_qr_path = 'QRCODE.png' # Saves the QR code as a PNG file
            qrcode.png(temp_qr_path, scale=10)  

            shutil.move(temp_qr_path, qr_file_path) # Moves the QR code to static/qrcodes

            return render_template('qrcode.html', user_qrcode=qr_file_path, qrcodestring=qrcodestringhtml)
        else:
            return render_template('qrcode.html', qrcodenotvalid="This QR Code is not valid")

    return render_template('qrcode.html', user_qrcode=None)

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

@app.route("/home")
def home():
    if not session.get("signed_in"):  # Check if user is signed in
        return redirect("/")  # Redirect to login page if not signed in
    return render_template("home.html")

@app.route("/logout")
def logout():
    session.pop("signed_in", None)  # Remove session variable
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)