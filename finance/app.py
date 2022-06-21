import os

from unittest import result
from webbrowser import get
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
# con = sqlite3.connect("file:finance.db?mode=rw",uri=True, check_same_thread=False)
db = SQL("sqlite:///finance.db")
# Creates a cursor for the database
#cur = con.cursor()
# Creates the actual table
db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00)")
db.execute("CREATE TABLE purchases (id INTEGER, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL);")
# con.commit()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user = session["user_id"]
    total = 0

    # Summary of user's stocks
    owns = db.execute("SELECT symbol, SUM(shares) AS shares FROM purchases GROUP BY symbol HAVING user_id=? AND SUM(shares) > 0", user)

    # Get's user's current cash balance
    balance = db.execute("SELECT cash FROM users WHERE id=?",user)[0]["cash"]

    # Retrieves table elements
    for own in owns:
        result = lookup(own["symbol"])
        own["name"] = result["name"]
        own["price"] = result["price"]
        own["value"] = own["price"] * own["shares"]
        total += own["value"]
    total += balance

    # Returns the index page with the set values from the users profile
    return render_template("index.html", owns=owns, balance=usd(balance), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Infor for conditional statements
        symbol = request.form.get("symbol")
        result = lookup(symbol)
        shares = int(request.form.get("shares"))
        user = session["user_id"]
        balance = db.execute("SELECT cash FROM users WHERE id=?", user)[0]["cash"]
        price = result["price"]
        total = price * shares

        if not symbol:
            return apology("must prove symbol.", 400)
        
        if not result:
            return apology("Invalid symbol", 400)
        
        if shares < 1:
            return apology("Invalid number of shares.", 400)
        if balance < total:
            return apology("Insufficient funds.", 400)

        db.execute("INSERT INTO purchases (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", user, symbol, shares, total)
        db.execute("UPDATE users SET cash=? WHERE id=?", (balance -  total), user)

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user = session["user_id"]

    owns = db.execute("SELECT symbol, shares,price FROM purchases WHERE user_id=?", user)

    return render_template("history.html", owns=owns)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""


    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Request information
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username=?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)
        

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
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
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Request information
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # Check if user reached via POST method
    if request.method == "POST":
        # Check if username entered is blank
        if not username:
            return apology("Username cannot be black.", 400)
        # Check if password blank
        elif not password:
            return apology("Password cannot be blank.", 400)
        # Check to make sure the confirmed password matches the initial password input
        elif confirmation != password:
            return apology("Passwords must match.", 400)

        rows = db.execute("SELECT * FROM users WHERE username=?;", username)
        if len(rows) > 0:
            return apology("Username already exists", 400)
        else:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        return redirect("/")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")

