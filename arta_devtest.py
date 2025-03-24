import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Custom CSS (merged and adjusted for both analyzers)
st.markdown("""
    <style>
    .metric-tile, .metric-card {
        background-color: #1E2A44;
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 15px;
        width: 100%;
        min-height: 100px;
        animation: fadeIn 0.5s ease-in;
    }
    .metric-card {
        height: 250px;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-title {
        font-size: 18px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
        white-space: normal;
        word-wrap: break-word;
    }
    .metric-desc, .metric-note {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 120px;
        line-height: 1.4;
    }
    .metric-note {
        flex: 1;
        white-space: normal;
        overflow-wrap: break-word;
    }
    .red-text, .metric-value.red { color: #FF4D4D; }
    .green-text, .metric-value.green { color: #32CD32; }
    .yellow-text { color: #FFD700; }
    .neutral-text, .metric-value.neutral { color: #A9A9A9; }
    .risk-assessment {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
    }
    .risk-red { background-color: #FF4D4D; }
    .risk-yellow { background-color: #FFD700; }
    .risk-green { background-color: #32CD32; }
    .proj-table-container { overflow-x: auto; max-width: 100%; }
    .proj-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(to bottom, #1E2A44, #6A82FB);
    }
    .proj-table th, .proj-table td {
        padding: 12px;
        text-align: center;
        color: white;
        border: 1px solid #2A3555;
        font-size: 14px;
    }
    .proj-table th { background-color: #1E2A44; font-weight: bold; }
    .proj-table tr:nth-child(even) td { background: rgba(255, 255, 255, 0.05); }
    .proj-table tr:nth-child(odd) td { background: rgba(255, 255, 255, 0.1); }
    .proj-table tr:hover td { background: rgba(255, 255, 255, 0.2); transition: background 0.3s ease; }
    .disclaimer {
        border: 2px solid #FF4D4D;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
        font-style: italic;
    }
    .large-logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        max-width: 90%;
        padding-top: 20px;
        padding-bottom: 30px;
    }
    @media (max-width: 768px) {
        .metric-tile, .metric-card {
            flex-direction: column;
            align-items: flex-start;
        }
        .metric-title, .metric-value, .metric-desc {
            width: 100%;
            min-width: 0;
        }
        .metric-value { font-size: 20px; }
        .metric-desc { max-height: 150px; }
        .proj-table th, .proj-table td {
            font-size: 12px;
            padding: 8px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Logo Display
st.markdown(
    f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="large-logo" width="600"></div>',
    unsafe_allow_html=True
)

# Title and Introduction
st.title("Arta Crypto Valuations - Know the Price. Master the Risk.")
st.markdown("""
Whether you're trading, investing, or strategizing, Arta provides fast, accurate insights into token prices, profit margins, and portfolio risk—whether for individual assets or liquidity pools. Run scenarios, test your assumptions, and sharpen your edge—all in real time. **Arta: Know the Price. Master the Risk.**
""")
st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar for Analyzer Selection
st.sidebar.header("Choose Analyzer")
analyzer_choice = st.sidebar.selectbox("Select Analyzer", ["Asset Analyzer", "Pool Analyzer"])

# Tabs for the two analyzers
tab1, tab2 = st.tabs(["Asset Analyzer", "Pool Analyzer"])

# Shared Functions
def parse_market_value(value_str):
    try:
        value_str = value_str.replace(",", "").lower()
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

# Asset Analyzer Functions (simplified for brevity, include full versions from your code)
def run_monte_carlo_asset(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200):
    # Placeholder for Monte Carlo logic (copy from Asset Analyzer)
    simulations = np.random.normal(growth_rate / 100, volatility / 100, n_simulations)
    return simulations * initial_investment, [], []

# Pool Analyzer Functions (simplified for brevity, include full versions from your code)
def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount):
    # Placeholder for IL calculation (copy from Pool Analyzer)
    return 0.0

def calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2):
    # Placeholder (copy from Pool Analyzer)
    return investment_amount, 0.0

def calculate_future_value(investment_amount, apy, months, *args):
    # Placeholder (copy from Pool Analyzer)
    return investment_amount * (1 + apy / 100 / 12) ** months, 0.0

def check_exit_conditions(*args):
    # Placeholder (copy from Pool Analyzer)
    return 0, 1.0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0

# Asset Analyzer Tab
with tab1:
    if analyzer_choice == "Asset Analyzer":
        st.sidebar.header("Asset Analyzer Inputs")
        asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
        volatility = st.sidebar.number_input("Asset Volatility % (Annual)", min_value=0.0, max_value=100.0, value=0.0)
        certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
        fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0)
        growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
        market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
        fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
        circulating_supply_input = st.sidebar.text_input("Circulating Supply (Tokens)", value="")
        max_supply_input = st.sidebar.text_input("Max Supply (Tokens) [Optional]", value="")
        vol_mkt_cap = st.sidebar.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
        btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0)
        btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
        risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)
        investor_profile = st.sidebar.selectbox("Investor Profile", ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"])
        calculate_asset = st.sidebar.button("Calculate Asset")

        if calculate_asset:
            market_cap = parse_market_value(market_cap_input)
            fdv = parse_market_value(fdv_input)
            circulating_supply = parse_market_value(circulating_supply_input)
            max_supply = parse_market_value(max_supply_input)

            if asset_price == 0 or initial_investment == 0:
                st.error("Please enter valid values for Asset Price and Initial Investment.")
            elif market_cap == 0 and (circulating_supply == 0 or asset_price == 0):
                st.error("Please provide either Market Cap or both Circulating Supply and Asset Price.")
            else:
                # Perform calculations (copy full logic from Asset Analyzer)
                months = 12
                asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
                asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
                asset_values = [initial_investment * p / asset_price for p in asset_projections]
                simulations, _, _ = run_monte_carlo_asset(initial_investment, growth_rate, volatility, months, fear_and_greed)
                worst_case = np.percentile(simulations, 10)
                expected_case = np.mean(simulations)
                best_case = np.percentile(simulations, 90)

                st.subheader("Key Metrics")
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">💰 Investment Value (1 Year)</div>
                        <div class="metric-value">${asset_values[-1]:,.2f}</div>
                        <div class="metric-desc">Potential value in 12 months.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Monte Carlo Worst Case</div>
                        <div class="metric-value">${worst_case:,.2f}</div>
                        <div class="metric-desc">10th percentile from Monte Carlo.</div>
                    </div>
                """, unsafe_allow_html=True)

# Pool Analyzer Tab
with tab2:
    if analyzer_choice == "Pool Analyzer":
        st.sidebar.header("Pool Analyzer Inputs")
        pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool"])
        is_new_pool = (pool_status == "New Pool")
        if is_new_pool:
            current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, value=90.00)
            current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, value=1.00)
            initial_price_asset1 = current_price_asset1
            initial_price_asset2 = current_price_asset2
        else:
            initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price ($)", min_value=0.01, value=88000.00)
            initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price ($)", min_value=0.01, value=1.00)
            current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price ($)", min_value=0.01, value=125000.00)
            current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price ($)", min_value=0.01, value=1.00)
        apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, value=1.00)
        trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, value=1)
        investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, value=2000.00)
        initial_tvl = st.sidebar.number_input("Initial TVL ($)", min_value=0.01, value=750000.00)
        current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, value=1000000.00)
        expected_price_change_asset1 = st.sidebar.number_input("Expected Price Change Asset 1 (%)", min_value=-100.0, value=-25.0)
        expected_price_change_asset2 = st.sidebar.number_input("Expected Price Change Asset 2 (%)", min_value=-100.0, value=-30.0)
        initial_btc_price = st.sidebar.number_input("Initial BTC Price ($)", min_value=0.0, value=84000.00)
        current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, value=84000.00)
        btc_growth_rate = st.sidebar.number_input("BTC Growth Rate (%)", min_value=-100.0, value=-25.0)
        risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0)
        calculate_pool = st.sidebar.button("Calculate Pool")

        if calculate_pool:
            il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
            pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
            future_value, future_il = calculate_future_value(investment_amount, apy, 12, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool)

            st.subheader("Core Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📉 Impermanent Loss</div>
                        <div class="metric-value">{il:.2f}%</div>
                        <div class="metric-note">Loss due to price divergence.</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📈 Pool Value (12 Months)</div>
                        <div class="metric-value">${future_value:,.2f}</div>
                        <div class="metric-note">Projected value after 12 months.</div>
                    </div>
                """, unsafe_allow_html=True)
