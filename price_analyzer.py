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
        max-width: 300px;
        min-height: 150px;
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
    .green-text {
        color: #32CD32;
    }
    .yellow-text {
        color: #FFD700;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar
st.sidebar.markdown("**Instructions**: To get started, visit coingecko.com to find your asset’s current price, market cap, fully diluted valuation (FDV), and Bitcoin’s price. Visit certik.com for the asset’s CertiK security score. Enter the values below and adjust growth rates as needed.")

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

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=1.0, step=0.0001, format="%.4f")
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=10.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="1000000")
market_cap = parse_market_value(market_cap_input)
st.sidebar.write(f"Parsed Market Cap: ${market_cap:,.2f}")
st.sidebar.markdown("**Note**: Enter values as shorthand (e.g., 67b for 67 billion, 500m for 500 million, 1.5k for 1,500) or full numbers (e.g., 67,000,000,000). Commas are optional.")
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="2000000")
fdv = parse_market_value(fdv_input)
st.sidebar.write(f"Parsed FDV: ${fdv:,.2f}")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=1000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=60000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=15.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=5.0)
volatility = st.sidebar.number_input("Volatility % (Annual)", min_value=0.0, max_value=100.0, value=50.0)
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=50.0)
st.sidebar.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")

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
    
    # Monte Carlo Simulation with Normal Distribution
    n_simulations = 200
    monthly_volatility = volatility / 100 / np.sqrt(12)  # Annual volatility to monthly
    monthly_expected_return = asset_monthly_rate
    simulations = []
    sim_paths = []
    all_monthly_returns = []
    
    for _ in range(n_simulations):
        monthly_returns = np.random.normal(monthly_expected_return, monthly_volatility, months)
        sim_prices = [initial_investment]
        for i in range(months):
            sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
        simulations.append(sim_prices[-1])
        sim_paths.append(sim_prices)
        all_monthly_returns.extend(monthly_returns)
    
    # Use percentiles for worst, expected, and best cases
    worst_case = np.percentile(simulations, 10)  # 10th percentile
    expected_case = np.mean(simulations)
    best_case = np.percentile(simulations, 90)  # 90th percentile
    
    # Max Drawdown on worst-case Monte Carlo scenario
    worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
    peak = np.maximum.accumulate(worst_path)
    drawdowns = (peak - worst_path) / peak
    max_drawdown = max(drawdowns) * 100

    # Dilution Risk (remaining dilution percentage)
    if fdv > 0:
        dilution_ratio = 100 - (market_cap / fdv) * 100
        if dilution_ratio < 20:
            dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
        elif dilution_ratio < 50:
            dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
        else:
            dilution_text = "⚠ High dilution risk: Significant token releases expected."
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

    # Sharpe and Sortino Ratios
    annual_return = (asset_values[-1] / initial_investment - 1)  # 12-month return
    rf_annual = risk_free_rate / 100
    std_dev = np.std(simulations) / initial_investment  # Standard deviation of final values
    sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0

    # Downside standard deviation for Sortino
    negative_returns = [r for r in all_monthly_returns if r < 0]
    downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
    sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

    # Composite Risk Score
    scores = {}
    # Max Drawdown
    if max_drawdown < 30:
        scores['Max Drawdown'] = 100
    elif max_drawdown < 50:
        scores['Max Drawdown'] = 50
    else:
        scores['Max Drawdown'] = 0
    
    # Dilution Risk
    if dilution_ratio < 20:
        scores['Dilution Risk'] = 100
    elif dilution_ratio < 50:
        scores['Dilution Risk'] = 50
    else:
        scores['Dilution Risk'] = 0
    
    # MCap Growth Plausibility
    if mcap_vs_btc < 1:
        scores['MCap Growth'] = 100
    elif mcap_vs_btc < 5:
        scores['MCap Growth'] = 50
    else:
        scores['MCap Growth'] = 0
    
    # Sharpe Ratio
    if sharpe_ratio > 1:
        scores['Sharpe Ratio'] = 100
    elif sharpe_ratio > 0:
        scores['Sharpe Ratio'] = 50
    else:
        scores['Sharpe Ratio'] = 0
    
    # Sortino Ratio
    if sortino_ratio > 1:
        scores['Sortino Ratio'] = 100
    elif sortino_ratio > 0:
        scores['Sortino Ratio'] = 50
    else:
        scores['Sortino Ratio'] = 0
    
    # CertiK Score
    certik_adjusted = 50 if certik_score == 0 else certik_score
    if certik_adjusted >= 70:
        scores['CertiK Score'] = 100
    elif certik_adjusted >= 40:
        scores['CertiK Score'] = 50
    else:
        scores['CertiK Score'] = 0
    
    # Market Cap
    if market_cap >= 1_000_000_000:
        scores['Market Cap'] = 100
    elif market_cap >= 10_000_000:
        scores['Market Cap'] = 50
    else:
        scores['Market Cap'] = 0

    composite_score = sum(scores.values()) / len(scores)
    if composite_score >= 70:
        color_class = "green-text"
        insight = "Low overall risk: This asset appears to be a relatively safe investment with strong risk-adjusted returns and low dilution risk."
    elif composite_score >= 40:
        color_class = "yellow-text"
        insight = "Moderate overall risk: Consider the specific risks (e.g., drawdown, dilution) before investing. Diversification may help."
    else:
        color_class = "red-text"
        insight = "High overall risk: This asset carries significant risks. Proceed with caution or explore safer alternatives."

    # Composite Risk Score
    st.subheader("Composite Risk Assessment")
    st.markdown(f"""
        <div>
            <div style="font-size: 20px; font-weight: bold;">Composite Risk Score: <span class="{color_class}">{composite_score:.1f}</span></div>
            <div style="font-size: 14px; margin-top: 5px;">{insight}</div>
        </div>
    """, unsafe_allow_html=True)

    # Key Metrics (3x2 grid)
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
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📊 Sharpe Ratio</div>
                <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                <div class="metric-desc">Risk-adjusted return. >1 indicates good performance relative to risk.</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">⚖️ Dilution Risk</div>
                <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
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
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Sortino Ratio</div>
                <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                <div class="metric-desc">Downside risk-adjusted return. >1 indicates good performance relative to downside risk.</div>
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
    
    # Table
    mc_data = {
        "Scenario": ["Worst Case", "Expected Case", "Best Case"],
        "Projected Value ($)": [worst_case, expected_case, best_case],
        "ROI (%)": [((worst_case / initial_investment) - 1) * 100, ((expected_case / initial_investment) - 1) * 100, ((best_case / initial_investment) - 1) * 100]
    }
    mc_df = pd.DataFrame(mc_data)
    
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
