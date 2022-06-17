import os
import sqlite3
from unittest import result

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime, timezone

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
con = sqlite3.connect("file:finance.db?mode=rw",uri=True, check_same_thread=False)
# Creates a cursor for the database
cur = con.cursor()
# Creates the actual table
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00)")
cur.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, timestamp TEXT, PRIMARY KEY(id), FOREIGN KEY(user_id) REFERENCES users(id))")
con.commit()

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
    
    owned = shares_owned()
    total = 0
    # Iterate over the symbols and shares
    for symbol, shares in owned.items():
        result = lookup(symbol)
        name = result["name"]
        price = result["price"]
        stock_value = shares * price
        total += stock_value
        owned[symbol] = (name, shares, usd(price), usd(stock_value))

    cash = cur.execute("SELECT cash FROM users WHERE id=?", session["user_id"][0]["cash"])
    
    return render_template("index.html", owned=owned, cash=usd(cash, total=usd(total)))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    returnusername = request.form.get("username")
    password =  apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = cur.execute("SELECT * FROM users WHERE username=?;", [username])

        # Ensure username exists and password is correct
        if not rows.fetchall() or not check_password_hash(rows[0]["hash"], {"hash": password}):
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

        rows = cur.execute("SELECT * FROM users WHERE username=?;", [username])
        if rows.fetchone() != None:
            return apology("Username already exists", 400)
        else:
            new_user = cur.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": username, "hash": generate_password_hash(password)})
            con.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")

def shares_owned():
    user_id = session["user_id"]
    owned = {}
    query = cur.execute("SELECT symbol, shares, FROM orders WHERE user_id=?", [user_id])
    for q in query:
        symbol,shares = q["symbol"], q["shares"]
        owned["symbol"] = owned.setdefault(symbol, 0) + shares
    
    # Filter zero-share stocks
    owned = {k: v for k,v in owned.items() if v != 0}

    return owned

def timenow():
    now_utc = datetime.now(timezone.utc)

    return str(now_utc.date()) + " @time " + now_utc.time().strftime("%H:%M:%S")

