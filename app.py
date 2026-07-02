import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required

# Configure application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///unireviews.db") 

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    selected_university = request.args.get('university')
    
    if selected_university:
        rows = db.execute("SELECT id, user_id, picked_university, title, review, rating, submission_time FROM reviews WHERE picked_university=? ORDER BY submission_time DESC", selected_university)
        if not rows:
            flash("No reviews for this university")
            return redirect("/")
    else:
        rows = db.execute("SELECT id, user_id, picked_university, title, review, rating, submission_time FROM reviews ORDER BY submission_time DESC")

    
    review_data = [] 
    
    if not rows:
        return render_template("index.html")

    for row in rows:
        id = row['id']
        user_id = row['user_id']
        picked_university = row['picked_university']
        title = row['title']
        review = row['review']
        rating = row['rating']
        time = row['submission_time']
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        repeats = db.execute("SELECT university FROM users WHERE id=?", user_id)
        
        for repeat in repeats:
            actual_university = repeat['university']
            if picked_university != actual_university:
                status = "Not a student at this university"
            else:
                status = "Student at this university"

                
        username = db.execute("SELECT username FROM users WHERE id=?", user_id)
        name = username[0]['username']
        
        selected_rating = rating

        review_data.append({
            'id': id,
            'title': title,
            'picked_university': picked_university,
            'review': review,
            'status': status,
            'name': name,
            'selected_rating': selected_rating,
            'submission_time': time,
        })

    return render_template("index.html", reviews=review_data,  selected_rating=selected_rating,selected_university=selected_university)


@app.route("/demo-login")
def demo_login():
    """Log straight into the seeded demo account, for the embedded portfolio preview."""
    session.clear()
    rows = db.execute("SELECT id FROM users WHERE username = ?", "demo")
    if rows:
        session["user_id"] = rows[0]["id"]
        flash("Logged in as demo")
    return index()


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("Invalid Username/Password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Logged in!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash('logged out!')
    return render_template("login.html")

@app.errorhandler(404)
def page_not_found(error):
    return apology("Page Not Found",404)


@app.route("/register", methods=["GET", "POST"])  
def register():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) > 0:
            flash("Username is taken", 'error')
            return render_template("register.html")
        
        password = request.form.get("password") 
        confirm_password = request.form.get("confirmation")
        hashed_password = generate_password_hash(password)
        university = request.form.get("uniselect")
        db.execute("INSERT INTO users (username, hash,university) VALUES(?,?,?)", username, hashed_password,university)
        
        new_user_id = db.execute("SELECT id FROM users WHERE username = :username", username=username)
        session["user_id"] = new_user_id[0]['id']
        flash("Registered!")
        return redirect("/")
    return render_template("register.html")

@app.route("/writeyourreview", methods=["GET","POST"])
@login_required
def writeyourreview():
    if request.method == "POST":
        picker = request.form.get("uniselectwrite")
        title= request.form.get("titlewrite")
        review = request.form.get("reviewwrite")
        if 'rating' in request.form:
            rating = request.form.get('rating')
        else:
            rating = 0
        current_time = datetime.now()
        db.execute("INSERT INTO reviews (user_id, picked_university, title, review, rating, submission_time) VALUES (?, ?, ?, ?, ?, ?)",session["user_id"], picker, title, review, rating,current_time)
        flash("Submitted")
        return redirect("/")
    return render_template("write_your_review.html")

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    if request.method == "POST":
        old_pw = db.execute("SELECT hash FROM users WHERE id=?", session["user_id"])
        old_pw = old_pw[0]['hash']
        old_pw_input = request.form.get("old_pw_input")
        new_pw = request.form.get("new_pw_input")
        new_pw_confirm = request.form.get("new_pw_input_confirm")
        if new_pw != new_pw_confirm:
            flash("The new passwords you entered do not match. Please try again.")
            return redirect("/settings")
        new_pw_hash = generate_password_hash(new_pw)
        if check_password_hash(old_pw,old_pw_input):
            db.execute("UPDATE users SET hash = ? WHERE id = ?", new_pw_hash, session["user_id"])
            flash("Password changed")
            return redirect("/")
        else:
            flash("Wrong old password")
            return redirect("/settings")
        
    return render_template("settings.html")