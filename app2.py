# app.py
from flask import Flask, render_template, request, flash, session, redirect, url_for
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Initialize Database within Application Context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('login.html')

# @app.route('/')
# def home():
#     return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('index'))
    
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'],show_alert=True)
    
    else:
        return redirect(url_for('index'))

@app.route('/plot', methods=['POST', 'GET'])
def plot():
    symbol = request.form.get('symbol', None)
    years = int(request.form.get('years', 0))
    filter_type = request.args.get('filter', 'monthly')

    try:
        # Call main.py with the provided symbol and years
        subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

        # Read data from the CSV file
        # df = pd.read_csv('stocks.csv', parse_dates=['DATE'])
        df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

        # Filter data based on user input
        filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years)]

        if filtered_data.empty:
            flash('No data available for the selected stock and years.', 'error')
            return render_template('home2.html')

        # Adjust time interval based on the filter parameter
        if filter_type == 'monthly':
            filtered_data = filtered_data.resample('M', on='DATE').mean()
        elif filter_type == 'quarterly':
            filtered_data = filtered_data.resample('Q', on='DATE').mean()
        elif filter_type == 'yearly':
            filtered_data = filtered_data.resample('Y', on='DATE').mean()

        # Plot the data
        plt.plot(filtered_data.index, filtered_data['CLOSE'], marker='o')
        plt.title(f'Stock Prices for {symbol} ({filter_type.capitalize()} Avg.) over the last {years} years')
        plt.xlabel('Date')
        plt.ylabel('Average Closing Price')

        # Customize date format on x-axis if needed
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

        # Save the plot to a BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        # Embed the plot in the HTML template
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        return render_template('home2.html', plot_url=plot_url)

    except subprocess.CalledProcessError:
        flash('Error: Failed to run main.py. Please check the command line arguments.', 'error')
        return render_template('home2.html')
    except pd.errors.EmptyDataError:
        flash('Error: Empty data file. Please check if data is being generated.', 'error')
        return render_template('home2.html')
    

@app.route('/single_graph')
def single_graph():
    if 'user_id' in session:
        return render_template('home2.html', username=session['username'])
    else:
        return redirect(url_for('index'))
    

@app.route('/multiple_graph')
def multiple_graph():
    if 'user_id' in session:
        return render_template('multiple_graph.html', username=session['username'])
    else:
        return redirect(url_for('index'))
    

@app.route('/plot_multiple', methods=['GET', 'POST'])
def plot_multiple():
    try:
        symbols = ['symbol1', 'symbol2', 'symbol3']
        years = [int(request.form.get(f'years{i}', 0)) for i in range(1, 4)]
        filter_type = request.args.get('filter', 'monthly')

        for i, symbol in enumerate(symbols):
            try:
                # Run main.py for each stock symbol and years
                subprocess.run(['python', 'main.py', request.form.get(symbol), str(years[i])], check=True)
            except subprocess.CalledProcessError:
                flash(f'Error: Failed to run main.py for {request.form.get(symbol)}.', 'error')
                return render_template('multiple_graphs.html')

        plt.figure(figsize=(10, 6))

        for i, symbol in enumerate(symbols):
            # Read data from the CSV file
            df = pd.read_csv(f"{request.form.get(symbol)}.csv", parse_dates=['DATE'])

            # Filter data based on user input
        filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years[i])]

        if filtered_data.empty:
            flash(f'No data available for {request.form.get(symbol)} and {years[i]} years.', 'error')
            return render_template('multiple_graphs.html')

            # Adjust time interval based on the filter parameter
        if filter_type == 'monthly':
            filtered_data = filtered_data.resample('M', on='DATE').mean()
        elif filter_type == 'quarterly':
            filtered_data = filtered_data.resample('Q', on='DATE').mean()
        elif filter_type == 'yearly':
            filtered_data = filtered_data.resample('Y', on='DATE').mean()

            # Plot the data
        plt.bar(filtered_data.index, filtered_data['CLOSE'], label=f'Stock {i+1}')

        plt.title(f'Stock Prices Comparison over the last {max(years)} years')
        plt.xlabel('Date')
        plt.ylabel('Average Closing Price')
        plt.legend()

        # Customize date format on x-axis if needed
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

        # Save the plot to a BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        # Embed the plot in the HTML template
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        return render_template('multiple_graphs.html', plot_url=plot_url)

    except pd.errors.EmptyDataError:
        flash('Error: Empty data file. Please check if data is being generated.', 'error')
        return render_template('multiple_graphs.html')

@app.route('/list_stocks')
def list_stocks():
    if 'user_id' in session:
        return render_template('list.html', username=session['username'])
    else:
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
