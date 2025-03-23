import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom CSS for dark-themed tiles
st.markdown("""
    <style>
    .metric-tile {
        background-color: #1E2A44;
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-desc {
        font-size: 12px;
        color: #A9A9A9;
    }
    .red-text {
        color: #FF4D4D;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar
st.sidebar.markdown("**Instructions**: To get started, visit coingecko.com to find your asset’s current price, market cap, fully diluted valuation (FDV), and Bitcoin’s price. Enter the values below and adjust growth rates as needed.")

st.sidebar.header("Input Parameters")

# Function to parse MCap and FDV inputs
def parse_market_value(value_str):
    try:
        # Remove commas and convert to lowercase
        value_str = value_str.replace(",", "").lower()
        # Handle suffixes (b, m, k)
        if value_str.endswith("b"):
            return float(value_str[:-1]) * 1_000_000_000
        elif value_str.endswith("m"):
            return float(value_str[:-1]) * 1_000_000
        elif value_str.endswith("k"):
            return float(value_str[:-1]) * 1_000
        else:
            return float(value_str)
    except:
        return 0.0

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=1.0)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=10.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="1000000")
market_cap = parse_market_value(market_cap_input)
st.sidebar.write(f"Parsed Market Cap: ${market_cap:,.2f}")
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="2000000")
fdv = parse_market_value(fdv_input)
st.sidebar.write(f"Parsed FDV: ${fdv:,.2f}")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=1000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=60000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=15.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=5.0)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Calculations
    months = 12
    asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
    btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
    rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
    
    # Price projections
    asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
    btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
    rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
    
    # Investment value projections
    asset_values = [initial_investment * p / asset_price for p in asset_projections]
    btc_values = [initial_investment * p / btc_price for p in btc_projections]
    
    # Monte Carlo Simulation
    n_simulations = 200
    simulations = []
    sim_paths = []
    for _ in range(n_simulations):
        monthly_returns = np.random.uniform(-0.5, 0.5, months)  # ±50% monthly variation
        sim_prices = [initial_investment]
        for i in range(months):
            sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
        simulations.append(sim_prices[-1])
        sim_paths.append(sim_prices)
    
    best_case = max(simulations)
    worst_case = min(simulations)
    expected_case = np.mean(simulations)
    
    # Max Drawdown on worst-case Monte Carlo scenario
    worst_path = sim_paths[np.argmin(simulations)]
    peak = np.maximum.accumulate(worst_path)
    drawdowns = (peak - worst_path) / peak
    max_drawdown = max(drawdowns) * 100

    # Dilution Risk (MCap/FDV ratio)
    if fdv > 0:
        dilution_ratio = (market_cap / fdv) * 100
        if dilution_ratio >= 80:
            dilution_text = "✓ Low dilution risk: Most tokens already circulating."
        elif dilution_ratio >= 50:
            dilution_text = "⚠ Moderate dilution risk: Significant unlocks possible."
        else:
            dilution_text = "⚠ High dilution risk: Major dilution ahead."
    else:
        dilution_ratio = 0
        dilution_text = "⚠ FDV not provided, cannot assess dilution risk."

    # MCap Growth Plausibility
    projected_price = asset_projections[-1]
    projected_mcap = market_cap * (projected_price / asset_price)
    btc_mcap = btc_price * 21_000_000  # Bitcoin's total supply
    mcap_vs_btc = (projected_mcap / btc_mcap) * 100
    if mcap_vs_btc <= 1:
        mcap_text = "✓ Plausible growth: Small market share needed."
    elif mcap_vs_btc <= 5:
        mcap_text = "⚠ Ambitious growth: Significant market share needed."
    else:
        mcap_text = "⚠ Very ambitious: Large market share required."

    # Key Metrics (2x2 grid)
    st.subheader("Key Metrics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💰 Investment Value (1 Year)</div>
                <div class="metric-value">${asset_values[-1]:,.2f}</div>
                <div class="metric-desc">Projected value of your ${initial_investment:,.2f} investment after 12 months.</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Max Drawdown</div>
                <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                <div class="metric-desc">Maximum peak-to-trough decline in the worst-case scenario over 12 months.</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">⚖️ Dilution Risk</div>
                <div class="metric-value {'red-text' if dilution_ratio < 50 else ''}">{dilution_ratio:.2f}%</div>
                <div class="metric-desc">{dilution_text}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 MCap Growth Plausibility</div>
                <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                <div class="metric-desc">{mcap_text}</div>
            </div>
        """, unsafe_allow_html=True)

    # Price Projections
    st.subheader("Projected Investment Value Over Time")
    st.markdown("**Note**: The projected value reflects the growth of your initial investment, adjusted for expected price changes.")
    
    # Table for months 0, 3, 6, 12
    proj_data = {
        "Time Period (Months)": [0, 3, 6, 12],
        "Projected Value ($)": [asset_values[i] for i in [0, 3, 6, 12]],
        "ROI (%)": [((asset_values[i] / initial_investment) - 1) * 100 for i in [0, 3, 6, 12]]
    }
    proj_df = pd.DataFrame(proj_data)
    st.table(proj_df)

    # Line Plot
    df_proj = pd.DataFrame({
        'Month': range(months + 1),
        'Asset Value': asset_values,
        'Bitcoin Value': btc_values,
        'Stablecoin Value': rf_projections
    })
    
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    sns.lineplot(data=df_proj, x='Month', y='Asset Value', label='Asset', color='teal', linewidth=2.5, marker='o')
    sns.lineplot(data=df_proj, x='Month', y='Bitcoin Value', label='Bitcoin', color='gold', linewidth=2.5, marker='o')
    sns.lineplot(data=df_proj, x='Month', y='Stablecoin Value', label='Stablecoin', color='gray', linewidth=2.5, marker='o')
    plt.axhline(y=initial_investment, color='red', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
    plt.fill_between(df_proj['Month'], initial_investment, df_proj['Asset Value'], where=(df_proj['Asset Value'] < initial_investment), color='red', alpha=0.1, label='Loss Zone')
    plt.title('Projected Investment Value Over 12 Months')
    plt.xlabel('Months')
    plt.ylabel('Value ($)')
    plt.legend()
    st.pyplot(plt)
    plt.clf()

    # Monte Carlo Results
    st.subheader("Monte Carlo Scenarios - 12 Month Investment Value")
    st.markdown("""
    - **Expected Case**: The result using your inputs (growth rate), with randomization.  
    - **Best Case**: The 90th percentile (20th highest of 200 runs)—a strong outcome, not the absolute best.  
    This gives you a practical snapshot of your investment’s potential over the next year.
    """)
    
    # Table with corrected styling
    mc_data = {
        "Scenario": ["Worst Case", "Expected Case", "Best Case"],
        "Projected Value ($)": [worst_case, expected_case, best_case],
        "ROI (%)": [((worst_case / initial_investment) - 1) * 100, ((expected_case / initial_investment) - 1) * 100, ((best_case / initial_investment) - 1) * 100]
    }
    mc_df = pd.DataFrame(mc_data)
    
    # Define a function to apply row-wise styling
    def highlight_rows(row):
        if row['Scenario'] == 'Worst Case':
            return ['background: #FF4D4D'] * len(row)
        elif row['Scenario'] == 'Expected Case':
            return ['background: #FFD700'] * len(row)
        else:
            return ['background: #32CD32'] * len(row)

    styled_mc_df = mc_df.style.apply(highlight_rows, axis=1)
    st.table(styled_mc_df)

    # Histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(simulations, bins=50, color='gray')
    plt.axvline(worst_case, color='red', label='Worst Case', linewidth=2)
    plt.axvline(expected_case, color='yellow', label='Expected Case', linewidth=2)
    plt.axvline(best_case, color='green', label='Best Case', linewidth=2)
    plt.axvline(initial_investment, color='black', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
    plt.title("Monte Carlo Scenarios - 12 Month Investment Value")
    plt.xlabel("Value ($)")
    plt.ylabel("Frequency")
    plt.legend()
    st.pyplot(plt)
    plt.clf()

    # Actionable Insights
    st.subheader("Actionable Insights")
    if asset_values[-1] > btc_values[-1] and asset_values[-1] > rf_projections[-1]:
        st.write("✓ Your asset is projected to outperform both Bitcoin and Stablecoin returns.")
    elif asset_values[-1] > rf_projections[-1]:
        st.write("✓ Your asset beats stablecoin returns but may underperform Bitcoin.")
    else:
        st.write("⚠ Your asset may underperform both Bitcoin and Stablecoin returns.")
        
    if max_drawdown > 50:
        st.write("⚠ High risk: Maximum drawdown exceeds 50% in the worst-case scenario.")
    elif max_drawdown > 30:
        st.write("⚠ Medium risk: Maximum drawdown between 30-50% in the worst-case scenario.")
    else:
        st.write("✓ Low risk: Maximum drawdown below 30% in the worst-case scenario.")
