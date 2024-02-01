# app.py
from flask import Flask, render_template, request, flash, session, redirect, url_for, send_file, send_from_directory
import subprocess
import pandas as pd
from datetime import date, datetime, timedelta
from jugaad_data.nse import bhavcopy_save
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from math import ceil

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('login.html')

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

    
@app.route('/plot', methods=['POST'])
def plot():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    date_difference = to_date - from_date

    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    plt.figure(figsize=(10, 6))
    plt.plot(filtered_data['DATE'], filtered_data['CLOSE'], marker='o', label='Closing Price')

    plt.title(f'Stock Prices for {symbol} from {from_date_str} to {to_date_str}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')



@app.route('/plot/daily', methods=['POST'])
def plot_daily():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    plt.figure(figsize=(10, 6))
    plt.plot(filtered_data['DATE'], filtered_data['CLOSE'], marker='o', label='Closing Price')

    plt.title(f'Stock Prices for {symbol} from {from_date_str} to {to_date_str} (Daily)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.xlim(from_date, to_date)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')


@app.route('/plot/weekly', methods=['POST'])
def plot_weekly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    weekly_data = filtered_data.iloc[1::7]

    if weekly_data.empty:
        return render_template('single_graph.html')

    plt.figure(figsize=(10, 6))
    plt.plot(weekly_data['DATE'], weekly_data['CLOSE'], marker='o', label='Closing Price')

    plt.title(f'Stock Prices for {symbol} from {from_date_str} to {to_date_str} (Weekly)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.xlim(from_date, to_date)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')



@app.route('/plot/monthly', methods=['POST'])
def plot_monthly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    monthly_data = filtered_data.iloc[1::30]

    if monthly_data.empty:
        return render_template('single_graph.html')

    # Plotting code
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_data['DATE'], monthly_data['CLOSE'], marker='o', label='Closing Price')

    plt.title(f'Stock Prices for {symbol} from {from_date_str} to {to_date_str} (Monthly)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.xlim(from_date, to_date)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')



@app.route('/plot/yearly', methods=['POST'])
def plot_yearly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)


    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    yearly_data = filtered_data[filtered_data['DATE'].dt.month == 1 & (filtered_data['DATE'].dt.day == 1)]

    if yearly_data.empty:
        return render_template('single_graph.html')

    plt.figure(figsize=(10, 6))
    plt.plot(yearly_data['DATE'], yearly_data['CLOSE'], marker='o', label='Closing Price')

    plt.title(f'Stock Prices for {symbol} from {from_date_str} to {to_date_str} (Yearly)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.xlim(from_date, to_date)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')
    


@app.route('/about_us')
def about_us():
    if 'user_id' in session:
        return render_template('about.html', username=session['username'],show_alert=True)
    
    else:
        return redirect(url_for('index'))
    

@app.route('/single_graph')
def single_graph():
    if 'user_id' in session:
        return render_template('single_graph.html', username=session['username'])
    else:
        return redirect(url_for('index'))
    

@app.route('/multiple_graph')
def multiple_graph():
    if 'user_id' in session:
        return render_template('multiple_graph.html', username=session['username'])
    else:
        return redirect(url_for('index'))
    

@app.route('/multiple_plot', methods=['POST'])
def multiple_plot():
    symbols = [request.form.get(f'symbol{i}') for i in range(1, 4)]
    years = int(request.form.get('years'))

    for symbol in symbols:
        subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    plt.figure(figsize=(12, 8))

    for symbol in symbols:
        df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])
        filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years)]
        plt.plot(filtered_data['DATE'], filtered_data['CLOSE'], marker='o', label=symbol)

    plt.title(f'Stock Prices for Multiple Symbols over the last {years} years')
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')


def get_filtered_companies(apply_filters=False):
    input_csv_file = bhavcopy_save(date(2024,1,25), "./")
    input2 = 'ind_nifty50list.csv'

    df = pd.read_csv(input_csv_file)
    df2 = pd.read_csv(input2)
    output_csv_file = 'allstocks.csv'
    output2 = 'allstocks2.csv'

    selected_columns = ['SYMBOL', 'SERIES', 'CLOSE']
    selected_columns2 = ['Symbol', 'Company Name']
    selected_data = df[selected_columns]
    selected_data2 = df2[selected_columns2]

    selected_data = selected_data[selected_data['SERIES'] == 'EQ']
    selected_data.to_csv(output_csv_file, index=False)
    selected_data2.to_csv(output2, index=False)

    allstocks_df = pd.read_csv('allstocks.csv')
    allstocks2_df = pd.read_csv('allstocks2.csv')

    filtered_allstocks_df = allstocks_df[allstocks_df['SYMBOL'].isin(allstocks2_df['Symbol'])]

    if apply_filters:
        average_close = filtered_allstocks_df['CLOSE'].mean()
        
        filtered_companies = filtered_allstocks_df[filtered_allstocks_df['CLOSE'] > average_close]['SYMBOL'].tolist()
        return filtered_companies
    else:
        all_companies = allstocks2_df['Symbol'].tolist()
        return all_companies
    

def get_filtered_companies2(apply_filters=False):
    input_csv_file = bhavcopy_save(date(2024,1,25), "./")
    input2 = 'ind_nifty50list.csv'

    df = pd.read_csv(input_csv_file)
    df2 = pd.read_csv(input2)
    output_csv_file = 'allstocks.csv'
    output2 = 'allstocks2.csv'

    selected_columns = ['SYMBOL', 'SERIES', 'CLOSE']
    selected_columns2 = ['Symbol', 'Company Name']
    selected_data = df[selected_columns]
    selected_data2 = df2[selected_columns2]

    selected_data = selected_data[selected_data['SERIES'] == 'EQ']
    selected_data.to_csv(output_csv_file, index=False)
    selected_data2.to_csv(output2, index=False)

    allstocks_df = pd.read_csv('allstocks.csv')
    allstocks2_df = pd.read_csv('allstocks2.csv')
  
    filtered_allstocks_df = allstocks_df[allstocks_df['SYMBOL'].isin(allstocks2_df['Symbol'])]
    filtered_allstocks_df.to_csv('stocks3.csv', index=False)
    stocks3_df = pd.read_csv('stocks3.csv')
    top10_companies_df = stocks3_df.nlargest(10, 'CLOSE')
    top10_companies = top10_companies_df['SYMBOL'].tolist()
    return top10_companies


def filter_companies_by_range(csv_file_path, from_value, to_value):
    filtered_companies = []
    with open(csv_file_path, 'r') as file:
        headers = next(file).strip().split(',')
        symbol_index = headers.index('SYMBOL')
        close_price_index = headers.index('CLOSE')

        for line in file:
            values = line.strip().split(',')
            symbol = values[symbol_index]
            close_price = float(values[close_price_index]) 
            if from_value <= close_price <= to_value:
                filtered_companies.append(symbol)
    return filtered_companies


def range1(apply_filters=None):
    input_csv_file = bhavcopy_save(date(2024, 1, 25), "./")
    input2 = 'ind_nifty50list.csv'

    df = pd.read_csv(input_csv_file)
    df2 = pd.read_csv(input2)
    output_csv_file = 'allstocks.csv'
    output2 = 'allstocks2.csv'

    selected_columns = ['SYMBOL', 'SERIES', 'CLOSE']
    selected_columns2 = ['Symbol', 'Company Name']
    selected_data = df[selected_columns]
    selected_data2 = df2[selected_columns2]

    selected_data = selected_data[selected_data['SERIES'] == 'EQ']
    selected_data.to_csv(output_csv_file, index=False)
    selected_data2.to_csv(output2, index=False)

    allstocks_df = pd.read_csv('allstocks.csv')
    allstocks2_df = pd.read_csv('allstocks2.csv')

    from_value = request.form.get('from')
    to_value = request.form.get('to')

    if from_value == '' or to_value == '':
        raise ValueError("Please enter values in both 'from' and 'to' fields.")

    if from_value is not None and to_value is not None:
        from_value = int(from_value)
        to_value = int(to_value)
        filtered_allstocks_df = allstocks_df[
            (allstocks_df['SYMBOL'].isin(allstocks2_df['Symbol'])) &
            (allstocks_df['CLOSE'] >= from_value) &
            (allstocks_df['CLOSE'] <= to_value)
        ]
    else:
        filtered_allstocks_df = allstocks_df[allstocks_df['SYMBOL'].isin(allstocks2_df['Symbol'])]

    filtered_allstocks_df.to_csv('stocks3.csv', index=False)

    return filtered_allstocks_df

    
@app.route('/apply_filters1', methods=['POST'])
def apply_filters1():
    apply_filters = 'average_price' in request.form
    companies = get_filtered_companies(apply_filters)
    return render_template('list.html', companies=companies)


@app.route('/apply_filters2', methods=['POST'])
def apply_filters2():
    apply_filters = 'top_10' in request.form
    companies = get_filtered_companies2(apply_filters)
    return render_template('list.html', companies=companies)

@app.route('/apply_filters3', methods=['POST'])
def apply_filters3():
    try:
        apply_filters = 'range' in request.form
        companies = range1(apply_filters)
    except ValueError as e:
        return render_template('list.html', error=str(e))
    return render_template('list.html', companies=companies)

@app.route('/list_stocks')
def list_stocks():
    if 'user_id' in session:
        companies = get_filtered_companies()
        return render_template('list.html', username=session['username'], companies=companies)
    else:
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/open_pdf')
def open_pdf():
    pdf_path = 'report.pdf'
    return send_from_directory('.', pdf_path, as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)
