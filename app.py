from flask import Flask, jsonify, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = 'rate_history.db'

@app.route('/')
def index():
    # Render the main page template
    return render_template('index.html')

@app.route('/current_rate')
def current_rate():
    # Fetch the current rate from the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT datetime, weighted_avg_price, percentage_change FROM exchange_rates
        ORDER BY datetime DESC LIMIT 1
    ''')
    result = cursor.fetchone()
    conn.close()
    # Return the result as a JSON object
    return jsonify({'datetime': result[0], 'weighted_avg_price': result[1], 'percentage_change': result[2]})

@app.route('/historical_rates/<period>')
def historical_rates(period):
    # Fetch historical rates based on the period specified
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if period == '24h':
        cursor.execute('''
            SELECT datetime, weighted_avg_price FROM exchange_rates
            WHERE datetime >= datetime('now', '-1 day')
            ORDER BY datetime ASC
        ''')
    elif period == 'week':
        cursor.execute('''
            SELECT datetime, weighted_avg_price FROM exchange_rates
            WHERE datetime >= datetime('now', '-7 day')
            ORDER BY datetime ASC
        ''')
    elif period == 'month':
        cursor.execute('''
            SELECT datetime, weighted_avg_price FROM exchange_rates
            WHERE datetime >= datetime('now', '-1 month')
            ORDER BY datetime ASC
        ''')
    results = cursor.fetchall()
    conn.close()
    # Return the results as a JSON array
    return jsonify([{'datetime': row[0], 'weighted_avg_price': row[1]} for row in results])

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
