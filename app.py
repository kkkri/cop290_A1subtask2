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

    
@app.route('/plot', methods=['POST'])
def plot():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    # print(from_date_str)
    to_date_str = request.form.get('toDate')
    # interval = request.form.get('interval')

    # Convert string dates to datetime objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    date_difference = to_date - from_date

    # Calculate the number of years
    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    # Filter data based on the user-specified date range
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    # Plotting code remains the same
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


# Daily plot route
@app.route('/plot/daily', methods=['POST'])
def plot_daily():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    # Convert string dates to datetime objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    # Calculate the number of years
    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    # Filter data based on the user-specified date range
    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    # Plotting code remains the same
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

# Weekly plot route
@app.route('/plot/weekly', methods=['POST'])
def plot_weekly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    # Convert string dates to datetime objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    # Calculate the number of years
    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    # Read the CSV file
    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    # Filter data based on the user-specified date range
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    # Extract every 7th entry starting from the 2nd row
    weekly_data = filtered_data.iloc[1::7]

    if weekly_data.empty:
        return render_template('single_graph.html')

    # Plotting code
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

# Monthly plot route
@app.route('/plot/monthly', methods=['POST'])
def plot_monthly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    # Convert string dates to datetime objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    # Calculate the number of years
    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    # Read the CSV file
    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    # Filter data based on the user-specified date range
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    # Extract every 30th entry starting from the 2nd row
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


# Yearly plot route
@app.route('/plot/yearly', methods=['POST'])
def plot_yearly():
    symbol = request.form.get('symbol')
    from_date_str = request.form.get('fromDate')
    to_date_str = request.form.get('toDate')

    # Convert string dates to datetime objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

    date_difference = to_date - from_date

    # Calculate the number of years
    years = ceil(date_difference.days / 365.25)

    subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    # Read the CSV file
    df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

    # Filter data based on the user-specified date range
    filtered_data = df[(df['DATE'] >= from_date) & (df['DATE'] <= to_date)]

    if filtered_data.empty:
        return render_template('single_graph.html')

    # Extract every date of the format yyyy-01-01
    yearly_data = filtered_data[filtered_data['DATE'].dt.month == 1 & (filtered_data['DATE'].dt.day == 1)]

    if yearly_data.empty:
        return render_template('single_graph.html')

    # Plotting code
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

# @app.route('/plot', methods=['POST', 'GET'])
# def plot():
#     symbol = request.form.get('symbol', None)
#     years = int(request.form.get('years', 0))
#     filter_type = request.args.get('filter', 'monthly')

#     try:
#         # Call main.py with the provided symbol and years
#         subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

#         # Read data from the CSV file
#         # df = pd.read_csv('stocks.csv', parse_dates=['DATE'])
#         df = pd.read_csv(f"{symbol}.csv", parse_dates=['DATE'])

#         # Filter data based on user input
#         filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years)]

#         if filtered_data.empty:
#             flash('No data available for the selected stock and years.', 'error')
#             return render_template('home2.html')

#         # Adjust time interval based on the filter parameter
#         if filter_type == 'monthly':
#             filtered_data = filtered_data.resample('M', on='DATE').mean()
#         elif filter_type == 'quarterly':
#             filtered_data = filtered_data.resample('Q', on='DATE').mean()
#         elif filter_type == 'yearly':
#             filtered_data = filtered_data.resample('Y', on='DATE').mean()

#         # Plot the data
#         plt.plot(filtered_data.index, filtered_data['CLOSE'], marker='o')
#         plt.title(f'Stock Prices for {symbol} ({filter_type.capitalize()} Avg.) over the last {years} years')
#         plt.xlabel('Date')
#         plt.ylabel('Average Closing Price')

#         # Customize date format on x-axis if needed
#         plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

#         # Save the plot to a BytesIO object
#         img = BytesIO()
#         plt.savefig(img, format='png')
#         img.seek(0)

#         # Embed the plot in the HTML template
#         plot_url = base64.b64encode(img.getvalue()).decode('utf8')
#         return render_template('home2.html', plot_url=plot_url)

#     except subprocess.CalledProcessError:
#         flash('Error: Failed to run main.py. Please check the command line arguments.', 'error')
#         return render_template('home2.html')
#     except pd.errors.EmptyDataError:
#         flash('Error: Empty data file. Please check if data is being generated.', 'error')
#         return render_template('home2.html')
    

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
    # Get stock symbols and years from the form
    symbols = [request.form.get(f'symbol{i}') for i in range(1, 4)]
    years = int(request.form.get('years'))

    # Generate CSV files for each stock symbol
    for symbol in symbols:
        subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

    # Plot the data using Matplotlib
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

    # Save the plot to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Send the image file directly to the client
    return send_file(img, mimetype='image/png')

# @app.route('/plot_multiple', methods=['GET', 'POST'])
# def plot_multiple():
#     try:
#         symbols = ['symbol1', 'symbol2', 'symbol3']
#         years = [int(request.form.get(f'years{i}', 0)) for i in range(1, 4)]
#         filter_type = request.args.get('filter', 'monthly')

#         for i, symbol in enumerate(symbols):
#             try:
#                 # Run main.py for each stock symbol and years
#                 subprocess.run(['python', 'main.py', request.form.get(symbol), str(years[i])], check=True)
#             except subprocess.CalledProcessError:
#                 flash(f'Error: Failed to run main.py for {request.form.get(symbol)}.', 'error')
#                 return render_template('multiple_graphs.html')

#         plt.figure(figsize=(10, 6))

#         for i, symbol in enumerate(symbols):
#             # Read data from the CSV file
#             df = pd.read_csv(f"{request.form.get(symbol)}.csv", parse_dates=['DATE'])

#             # Filter data based on user input
#         filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years[i])]

#         if filtered_data.empty:
#             flash(f'No data available for {request.form.get(symbol)} and {years[i]} years.', 'error')
#             return render_template('multiple_graphs.html')

#             # Adjust time interval based on the filter parameter
#         if filter_type == 'monthly':
#             filtered_data = filtered_data.resample('M', on='DATE').mean()
#         elif filter_type == 'quarterly':
#             filtered_data = filtered_data.resample('Q', on='DATE').mean()
#         elif filter_type == 'yearly':
#             filtered_data = filtered_data.resample('Y', on='DATE').mean()

#             # Plot the data
#         plt.bar(filtered_data.index, filtered_data['CLOSE'], label=f'Stock {i+1}')

#         plt.title(f'Stock Prices Comparison over the last {max(years)} years')
#         plt.xlabel('Date')
#         plt.ylabel('Average Closing Price')
#         plt.legend()

#         # Customize date format on x-axis if needed
#         plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

#         # Save the plot to a BytesIO object
#         img = BytesIO()
#         plt.savefig(img, format='png')
#         img.seek(0)

#         # Embed the plot in the HTML template
#         plot_url = base64.b64encode(img.getvalue()).decode('utf8')
#         return render_template('multiple_graphs.html', plot_url=plot_url)

#     except pd.errors.EmptyDataError:
#         flash('Error: Empty data file. Please check if data is being generated.', 'error')
#         return render_template('multiple_graphs.html')

# @app.route('/list_stocks')
# def list_stocks():
#     if 'user_id' in session:
#         return render_template('list.html', username=session['username'])
#     else:
#         return redirect(url_for('index'))
    
def get_filtered_companies(apply_filters=False):
    # current_date = datetime.now().date()
    # three_days_ago = current_date - timedelta(days=3)
    input_csv_file = bhavcopy_save(date(2024,2,1), "./")
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

    # if apply_filters:
    #     if filter_type == 'average_price':
    #         # Filter based on average price
    #         average_close = filtered_allstocks_df['CLOSE'].mean()
    #         filtered_companies = filtered_allstocks_df[filtered_allstocks_df['CLOSE'] > average_close]['SYMBOL'].tolist()
    #         return filtered_companies
        # elif filter_type == 'top10':
        #     # Filter based on top 10 companies with the highest closing price
        #     # filtered_allstocks_df['CLOSE'] = pd.to_numeric(filtered_allstocks_df['CLOSE'], errors='coerce')
        #     filtered_companies = filtered_allstocks_df.nlargest(10, 'CLOSE')['SYMBOL'].tolist()
        #     return filtered_companies
    #     else:
    #         # Default behavior if no filter type specified
    #         filtered_companies = []
    # else:
    #     # Default behavior without applying filters
    #     filtered_companies = allstocks2_df['Symbol'].tolist()
    #     return filtered_companies
    

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
    # Extract the top 10 companies with the highest closing prices
    top10_companies_df = stocks3_df.nlargest(10, 'CLOSE')
    # if apply_filters:
    top10_companies = top10_companies_df['SYMBOL'].tolist()
    return top10_companies

def filter_companies_by_range(csv_file_path, from_value, to_value):
    # Logic to read CSV file and filter companies based on closing price range
    # Replace 'Symbol' and 'Close_Price' with actual column names in your CSV file
    # that represent the company symbol and closing price.
    # Also, ensure to convert 'from_value' and 'to_value' to integers before comparison.

    filtered_companies = []
    with open(csv_file_path, 'r') as file:
        # Assuming CSV file has headers, if not adjust the logic accordingly
        headers = next(file).strip().split(',')
        symbol_index = headers.index('SYMBOL')
        close_price_index = headers.index('CLOSE')

        for line in file:
            values = line.strip().split(',')
            symbol = values[symbol_index]
            close_price = float(values[close_price_index])  # Assuming close price is a floating-point number

            if from_value <= close_price <= to_value:
                filtered_companies.append(symbol)

    return filtered_companies

def range1(apply_filters=None):
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

    from_value = int(request.form.get('from'))
    to_value = int(request.form.get('to'))
    # stocks3_df = pd.read_csv('stocks3.csv')
    filtered_companies = filter_companies_by_range('stocks3.csv', from_value, to_value)
    return filtered_companies
    # return render_template('list.html', companies=filtered_companies

    


    # if apply_filters:
    #     average_close = filtered_allstocks_df['CLOSE'].mean()
        
    #     filtered_companies = filtered_allstocks_df[filtered_allstocks_df['CLOSE'] > average_close]['SYMBOL'].tolist()
    #     return filtered_companies
    # else:
    #     all_companies = allstocks2_df['Symbol'].tolist()
    #     return all_companies


# @app.route('/apply_filters', methods=['POST'])
# def apply_filters():
#     apply_average_price = 'average_price' in request.form
#     apply_top10 = 'top10' in request.form

#     filter_type = None
#     if apply_average_price:
#         filter_type = 'average_price'
#     elif apply_top10:
#         filter_type = 'top10'

#     companies = get_filtered_companies(apply_filters=apply_average_price, filter_type=filter_type)

#     return render_template('list.html', companies=companies)


# @app.route('/apply_filters', methods=['POST'])
# def apply_filters():
#     apply_average_price = 'average_price' in request.form
#     apply_top10 = 'top10' in request.form
#     # filter_type=None
#     if apply_average_price:
#         companies = get_filtered_companies(apply_average_price)
#         return render_template('list.html', companies=companies)
#     elif apply_top10:
#         companies = get_filtered_companies(apply_top10)
#         return render_template('list.html', companies=companies)
#     else:
#         return render_template('list.html', companies=companies)
    
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
    apply_filters = 'range' in request.form
    companies = range1(apply_filters)
    return render_template('list.html', companies=companies)
# def get_filtered_companies(apply_filters=False):
#     # current_date = datetime.now().date()
#     # three_days_ago = current_date - timedelta(days=3)
#     # three_days_ago = '2024-01-25
#     input_csv_file = bhavcopy_save(date(2024,1,25), "./")
#     input2 = 'ind_nifty50list.csv'

#     df = pd.read_csv(input_csv_file)
#     df2 = pd.read_csv(input2)
#     output_csv_file = 'allstocks.csv'
#     output2 = 'allstocks2.csv'

#     selected_columns = ['SYMBOL', 'SERIES', 'CLOSE']
#     selected_columns2 = ['Symbol', 'Company Name']
#     selected_data = df[selected_columns]
#     selected_data2 = df2[selected_columns2]

#     selected_data = selected_data[selected_data['SERIES'] == 'EQ']
#     selected_data.to_csv(output_csv_file, index=False)
#     selected_data2.to_csv(output2, index=False)

#     allstocks_df = pd.read_csv('allstocks.csv')
#     allstocks2_df = pd.read_csv('allstocks2.csv')

#     # Filter rows in allstocks.csv based on symbols present in allstocks2.csv
#     filtered_allstocks_df = allstocks_df[allstocks_df['SYMBOL'].isin(allstocks2_df['Symbol'])]

#     if apply_filters:
#         average_close = filtered_allstocks_df['CLOSE'].mean()
#         # Filter companies based on average close price
#         filtered_companies = filtered_allstocks_df[filtered_allstocks_df['CLOSE'] > average_close]['SYMBOL'].tolist()
#         return filtered_companies
#     else:
#         all_companies = allstocks2_df['Symbol'].tolist()
#         return all_companies

@app.route('/list_stocks')
def list_stocks():
    if 'user_id' in session:
        companies = get_filtered_companies()
        return render_template('list.html', username=session['username'], companies=companies)
    else:
        return redirect(url_for('index'))
    # companies = get_filtered_companies()
    # return render_template('list.html', companies=companies)

# @app.route('/apply_filters', methods=['POST'])
# def apply_filters():
#     apply_filters = 'average_price' in request.form
#     companies = get_filtered_companies(apply_filters)
#     return render_template('list.html', companies=companies)
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/open_pdf')
def open_pdf():
    # Replace 'path/to/your/file.pdf' with the actual path to your PDF file.
    pdf_path = 'samplepdf.pdf'

    # Send the PDF file as an attachment with the option to open in a new tab
    # return send_file(pdf_path, as_attachment=True, download_name='file.pdf')
    # return send_file(pdf_path, mimetype='application/pdf')
    return send_from_directory('.', pdf_path, as_attachment=False)
    # return render_template('open_pdf.html', pdf_path=pdf_path)

if __name__ == '__main__':
    app.run(debug=True)
