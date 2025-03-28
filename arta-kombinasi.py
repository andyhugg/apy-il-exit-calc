import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

app = Flask(__name__)

# Set up directories
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# Store PDF buffer globally
app.config['PDF_BUFFER'] = None

# Helper Functions
def calculate_impermanent_loss(initial_price1, initial_price2, current_price1, current_price2):
    initial_ratio = initial_price1 / initial_price2
    current_ratio = current_price1 / current_price2
    price_ratio = current_ratio / initial_ratio
    if price_ratio == 1:
        return 0
    il = 2 * (np.sqrt(price_ratio) / (1 + price_ratio)) - 1
    return il

def run_simulation(initial_price1, initial_price2, current_price1, current_price2, investment, apy,
                   price_change1, price_change2, months=12):
    monthly_apy = apy / 12 / 100
    monthly_price_change1 = price_change1 / 12 / 100
    monthly_price_change2 = price_change2 / 12 / 100

    data = []
    portfolio_value = investment
    cumulative_profit = 0

    for month in range(1, months + 1):
        # Update prices
        new_price1 = current_price1 * (1 + monthly_price_change1 * month)
        new_price2 = current_price2 * (1 + monthly_price_change2 * month)

        # Calculate IL
        il = calculate_impermanent_loss(initial_price1, initial_price2, new_price1, new_price2)
        il_value = il * portfolio_value

        # Calculate APY gains
        apy_gain = portfolio_value * monthly_apy

        # Update portfolio value
        portfolio_value += apy_gain - il_value
        net_profit = portfolio_value - investment

        data.append({
            'Month': month,
            'Asset 1 Price ($)': round(new_price1, 2),
            'Asset 2 Price ($)': round(new_price2, 2),
            'IL ($)': round(-il_value, 2),
            'APY Gain ($)': round(apy_gain, 2),
            'Net Profit ($)': round(net_profit, 2)
        })

    return pd.DataFrame(data)

def calculate_max_drawdown(portfolio_values, confidence_level=0.9):
    # Simulate 1000 price paths with volatility
    n_simulations = 1000
    monthly_volatility = 0.05  # 5% monthly volatility
    drawdowns = []

    for _ in range(n_simulations):
        simulated_values = []
        current_value = portfolio_values[0]
        for i in range(len(portfolio_values)):
            noise = np.random.normal(0, monthly_volatility)
            current_value = portfolio_values[i] * (1 + noise)
            simulated_values.append(current_value)

        # Calculate max drawdown for this path
        peak = np.maximum.accumulate(simulated_values)
        drawdown = (peak - simulated_values) / peak
        max_drawdown = np.max(drawdown)
        drawdowns.append(max_drawdown)

    # Return the 90th percentile drawdown
    return np.percentile(drawdowns, confidence_level * 100)

def generate_graphs(df, investment):
    sns.set_style("darkgrid")
    plt.rcParams['figure.figsize'] = (10, 6)

    # Graph 1: Profit Over Time
    plt.figure()
    sns.lineplot(x='Month', y='Net Profit ($)', data=df, marker='o', color='green')
    plt.title('Profit Over Time')
    plt.xlabel('Month')
    plt.ylabel('Net Profit ($)')
    plt.savefig('static/images/profit_over_time.png')
    plt.close()

    # Graph 2: IL vs APY Contribution
    plt.figure()
    plt.fill_between(df['Month'], df['IL ($)'], color='red', alpha=0.5, label='Impermanent Loss')
    plt.fill_between(df['Month'], df['APY Gain ($)'], color='blue', alpha=0.5, label='APY Gain')
    plt.title('Impermanent Loss vs APY Contribution')
    plt.xlabel('Month')
    plt.ylabel('Value ($)')
    plt.legend()
    plt.savefig('static/images/il_vs_apy.png')
    plt.close()

    # Graph 3: Max Drawdown (Simplified for static graph)
    portfolio_values = investment + df['Net Profit ($)']
    plt.figure()
    sns.lineplot(x='Month', y=portfolio_values, marker='o', color='purple')
    plt.title('Portfolio Value with Max Drawdown')
    plt.xlabel('Month')
    plt.ylabel('Portfolio Value ($)')
    plt.savefig('static/images/max_drawdown.png')
    plt.close()

def generate_pdf(df, metrics):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CryptoPool Valuator Report")

    # Table
    c.setFont("Helvetica", 10)
    y = height - 100
    for _, row in df.iterrows():
        c.drawString(50, y, f"Month {int(row['Month'])}: Profit ${row['Net Profit ($)']}, IL ${row['IL ($)']}")
        y -= 20

    # Metrics
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Key Metrics:")
    y -= 20
    c.setFont("Helvetica", 10)
    for key, value in metrics.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20

    # Graphs
    y -= 20
    for img_path in ['static/images/profit_over_time.png', 'static/images/il_vs_apy.png', 'static/images/max_drawdown.png']:
        img = ImageReader(img_path)
        c.drawImage(img, 50, y - 150, width=500, height=150)
        y -= 170

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form inputs
        pool_status = request.form['pool_status']
        initial_price1 = float(request.form['initial_price1'])
        initial_price2 = float(request.form['initial_price2'])
        current_price1 = float(request.form['current_price1'])
        current_price2 = float(request.form['current_price2'])
        investment = float(request.form['investment'])
        apy = float(request.form['apy'])
        price_change1 = float(request.form['price_change1'])
        price_change2 = float(request.form['price_change2'])
        tvl = float(request.form['tvl']) if pool_status == 'existing' else 0
        trust_score = int(request.form['trust_score'])
        btc_price = float(request.form['btc_price'])
        btc_growth = float(request.form['btc_growth'])
        risk_free_rate = float(request.form['risk_free_rate'])

        # Run simulation
        df = run_simulation(initial_price1, initial_price2, current_price1, current_price2, investment, apy,
                            price_change1, price_change2)

        # Calculate key metrics
        total_profit = df['Net Profit ($)'].iloc[-1]
        total_il = df['IL ($)'].sum()
        total_apy = df['APY Gain ($)'].sum()
        break_even = df[df['Net Profit ($)'] > 0]['Month'].iloc[0] if (df['Net Profit ($)'] > 0).any() else "N/A"
        portfolio_values = investment + df['Net Profit ($)']
        max_drawdown = calculate_max_drawdown(portfolio_values) * investment
        recovery_percent = (max_drawdown / (portfolio_values.min() - max_drawdown)) * 100 if portfolio_values.min() != max_drawdown else 0

        metrics = {
            "Total Projected Profit ($)": f"${round(total_profit, 2)}",
            "Impermanent Loss Impact ($)": f"${round(total_il, 2)}",
            "APY Contribution ($)": f"${round(total_apy, 2)}",
            "Break-Even Point (Months)": break_even,
            "Max Drawdown (90%) ($)": f"${round(max_drawdown, 2)}",
            "Recovery % Required": f"{round(recovery_percent, 2)}%"
        }

        # Generate graphs
        generate_graphs(df, investment)

        # Generate PDF and store in app.config
        app.config['PDF_BUFFER'] = generate_pdf(df, metrics)

        return render_template('index.html', table=df.to_html(), metrics=metrics,
                               profit_graph='static/images/profit_over_time.png',
                               il_apy_graph='static/images/il_vs_apy.png',
                               drawdown_graph='static/images/max_drawdown.png')

    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    pdf_buffer = app.config['PDF_BUFFER']
    if pdf_buffer is None:
        return "No PDF available. Please run an analysis first.", 400
    return send_file(pdf_buffer, as_attachment=True, download_name='CryptoPool_Valuator_Report.pdf')

if __name__ == '__main__':
    app.run(debug=True)
