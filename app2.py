# app.py
from flask import Flask, render_template, request, flash
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure secret key

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/plot', methods=['POST', 'GET'])
def plot():
    symbol = request.form.get('symbol', None)
    years = int(request.form.get('years', 0))
    filter_type = request.args.get('filter', 'monthly')

    try:
        # Call main.py with the provided symbol and years
        subprocess.run(['python', 'main.py', symbol, str(years)], check=True)

        # Read data from the CSV file
        df = pd.read_csv('stocks.csv', parse_dates=['DATE'])

        # Filter data based on user input
        filtered_data = df[df['DATE'] >= pd.to_datetime('today') - pd.DateOffset(years=years)]

        if filtered_data.empty:
            flash('No data available for the selected stock and years.', 'error')
            return render_template('home.html')

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
        return render_template('home.html', plot_url=plot_url)

    except subprocess.CalledProcessError:
        flash('Error: Failed to run main.py. Please check the command line arguments.', 'error')
        return render_template('home.html')
    except pd.errors.EmptyDataError:
        flash('Error: Empty data file. Please check if data is being generated.', 'error')
        return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
