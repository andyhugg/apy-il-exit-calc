import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Custom CSS for styling (reused from Asset Analyzer, adapted for Pool Analyzer)
st.markdown("""
    <style>
    .metric-tile {
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
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 120px;
        line-height: 1.4;
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
    .neutral-text {
        color: #A9A9A9;
    }
    .risk-assessment {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
    }
    .risk-red {
        background-color: #FF4D4D;
    }
    .risk-yellow {
        background-color: #FFD700;
    }
    .risk-green {
        background-color: #32CD32;
    }
    .proj-table-container {
        overflow-x: auto;
        max-width: 100%;
    }
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
    .proj-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .proj-table tr:nth-child(even) td {
        background: rgba(255, 255, 255, 0.05);
    }
    .proj-table tr:nth-child(odd) td {
        background: rgba(255, 255, 255, 0.1);
    }
    .proj-table tr:hover td {
        background: rgba(255, 255, 255, 0.2);
        transition: background 0.3s ease;
    }
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
        .metric-tile {
            flex-direction: column;
            align-items: flex-start;
        }
        .metric-title, .metric-value, .metric-desc {
            width: 100%;
            min-width: 0;
        }
        .metric-value {
            font-size: 20px;
        }
        .metric-desc {
            max-height: 150px;
        }
        .proj-table th, .proj-table td {
            font-size: 12px;
            padding: 8px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Display the logo
st.markdown(
    f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="large-logo" width="600"></div>',
    unsafe_allow_html=True
)

# Title
st.title("Arta Crypto Valuations - Know the Price. Master the Risk.")

# Introduction and Disclaimer
st.markdown("""
Whether you're trading, investing, or strategizing, Arta gives you fast, accurate insights into token prices, profit margins, and portfolio risk. Run scenarios, test your assumptions, and sharpen your edge — all in real time. **Arta: Know the Price. Master the Risk.**
""")

st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar for Mode Selection and Inputs
st.sidebar.header("Analysis Mode")
analysis_mode = st.sidebar.selectbox("Select Analysis Mode", ["Asset Analyzer", "Pool Analyzer", "Combined Analysis"])

# Shared Inputs
st.sidebar.header("Shared Parameters")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=2000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=84000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=10.0)
investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
    index=0
)

# Asset Analyzer Functions (from the first code)
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

@st.cache_data
def run_monte_carlo_asset(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200):
    expected_annual_return = growth_rate / 100
    if volatility == 0:
        if fear_and_greed <= 24:
            volatility_value = 0.75
        elif fear_and_greed <= 49:
            volatility_value = 0.60
        elif fear_and_greed == 50:
            volatility_value = 0.40
        elif fear_and_greed <= 74:
            volatility_value = 0.50
        else:
            volatility_value = 0.70
    else:
        volatility_value = volatility / 100

    if fear_and_greed <= 49:
        volatility_adjustment = 1.2
    elif fear_and_greed > 50:
        volatility_adjustment = 1.1
    else:
        volatility_adjustment = 1.0
    adjusted_volatility = volatility_value * volatility_adjustment
    monthly_volatility = adjusted_volatility / np.sqrt(12) if adjusted_volatility > 0 else 0.1

    lower_bound = expected_annual_return - adjusted_volatility
    upper_bound = expected_annual_return + adjusted_volatility

    monthly_expected_return = (1 + expected_annual_return) ** (1/12) - 1
    simulations = []
    sim_paths = []
    all_monthly_returns = []

    for _ in range(n_simulations):
        if fear_and_greed <= 49:
            alpha, beta = 2, 5
        elif fear_and_greed > 50:
            alpha, beta = 5, 2
        else:
            alpha, beta = 2, 2

        raw_return = np.random.beta(alpha, beta)
        annual_return = lower_bound + (upper_bound - lower_bound) * raw_return

        monthly_base_return = (1 + annual_return) ** (1/12) - 1
        monthly_returns = np.random.normal(monthly_base_return, monthly_volatility/2, months)
        sim_prices = [initial_investment]
        for i in range(months):
            sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
        max_allowed_value = initial_investment * (1 + expected_annual_return + adjusted_volatility)
        sim_prices[-1] = min(sim_prices[-1], max_allowed_value)
        simulations.append(sim_prices[-1])
        sim_paths.append(sim_prices)
        all_monthly_returns.extend(monthly_returns)

    return simulations, sim_paths, all_monthly_returns

# Pool Analyzer Functions (from the second code)
def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment):
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    return round(il_percentage, 2) if il_percentage > 0.01 else il_percentage

def calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2):
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                          current_price_asset1, current_price_asset2, expected_price_change_asset1,
                          expected_price_change_asset2, is_new_pool=False):
    if months < 0:
        return initial_investment, 0.0

    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12

    if is_new_pool:
        starting_price_asset1 = current_price_asset1
        starting_price_asset2 = current_price_asset2
        initial_adjusted_price_asset1 = current_price_asset1
        initial_adjusted_price_asset2 = current_price_asset2
        initial_pool_value, _ = calculate_pool_value(initial_investment, starting_price_asset1, starting_price_asset2,
                                                    initial_adjusted_price_asset1, initial_adjusted_price_asset2)
        pool_value = initial_pool_value
    else:
        pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                            current_price_asset1, current_price_asset2)
        starting_price_asset1 = initial_price_asset1
        starting_price_asset2 = initial_price_asset2

    if months == 0:
        return round(pool_value, 2), calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)

    apy_compounded_value = pool_value * (1 + monthly_apy) ** months

    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)

    new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                           final_price_asset1, final_price_asset2)

    future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
    current_value = apy_compounded_value + (new_pool_value - pool_value)

    return round(current_value, 2), future_il

def calculate_break_even_months(apy, il, initial_pool_value, value_if_held):
    if apy <= 0 or initial_pool_value <= 0 or value_if_held <= initial_pool_value:
        return 0
    
    monthly_apy = (apy / 100) / 12
    months = 0
    current_value = initial_pool_value
    
    while current_value < value_if_held and months < 1000:
        current_value *= (1 + monthly_apy)
        months += 1
    
    return round(months, 2) if months < 1000 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
                                                  current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool=False):
    if apy <= 0:
        return float('inf')

    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    months = 0
    current_value = pool_value

    while current_value < value_if_held and months < 1000:
        months += 1
        final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                               final_price_asset1, final_price_asset2)
        current_value = pool_value * (1 + monthly_apy) ** months + (new_pool_value - pool_value)

    return round(months, 2) if months < 1000 else float('inf')

def calculate_tvl_decline(initial_tvl, current_tvl):
    if initial_tvl <= 0:
        return 0.0
    tvl_change = (current_tvl - initial_tvl) / initial_tvl * 100
    return round(tvl_change, 2)

def calculate_apy_margin_of_safety(initial_pool_value, value_if_held, current_apy, months=12):
    target_value = value_if_held * 1.02
    min_apy = ((target_value / initial_pool_value) ** (12 / months) - 1) * 100
    apy_mos = ((current_apy - min_apy) / current_apy) * 100 if current_apy > 0 else 0
    return max(0, min(apy_mos, 100))

def calculate_volatility_score(il_percentage, tvl_decline):
    il_factor = min(il_percentage / 5, 1.0)
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)
    volatility_score = (il_factor + tvl_factor) * 25
    final_score = min(volatility_score, 50)

    if final_score <= 25:
        message = f"✅ Volatility Score: Low ({final_score:.0f}%). Stable conditions with low IL and TVL decline."
    else:
        message = f"⚠️ Volatility Score: Moderate ({final_score:.0f}%). Moderate IL or TVL decline may impact returns."
    
    return final_score, message

def calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score):
    base_score = 0
    if apy < 10:
        base_score += 40
    elif apy <= 15:
        base_score += 20

    if tvl_decline < -50:
        base_score += 40
    elif tvl_decline < -30:
        base_score += 30
    elif tvl_decline < -15:
        base_score += 15

    if current_tvl < 50000:
        base_score += 40
    elif current_tvl <= 200000:
        base_score += 20
    
    base_score = min(base_score, 100)
    
    if trust_score == 1:
        adjusted_score = base_score * 1.5
    elif trust_score == 2:
        adjusted_score = base_score * 1.25
    elif trust_score == 3:
        adjusted_score = base_score * 0.9
    elif trust_score == 4:
        adjusted_score = base_score * 0.75
    else:
        adjusted_score = base_score * 0.5
    
    adjusted_score = min(adjusted_score, 100)
    
    risk_factors = []
    if apy < 10:
        risk_factors.append("low yield")
    elif apy <= 15:
        risk_factors.append("moderate yield")
    if tvl_decline < -50:
        risk_factors.append("major TVL decline")
    elif tvl_decline < -30:
        risk_factors.append("significant TVL decline")
    elif tvl_decline < -15:
        risk_factors.append("moderate TVL decline")
    if current_tvl < 50000:
        risk_factors.append("tiny pool size")
    elif current_tvl <= 200000:
        risk_factors.append("small pool size")
    
    category = None
    if adjusted_score > 75:
        category = "Critical"
    elif adjusted_score > 50:
        category = "High"
    elif trust_score in [1, 2]:
        category = "Advisory"
    elif adjusted_score > 25:
        category = "Advisory"
    else:
        category = "Low"
    
    if category == "Advisory" and trust_score >= 3 and adjusted_score <= 50 and tvl_decline >= -15 and current_tvl > 200000:
        category = "Low"

    if category == "Low":
        if trust_score >= 3:
            message = f"✅ Protocol Risk: Low ({adjusted_score:.0f}%). Minimal risk due to moderate/good/excellent trust score, stable TVL, and adequate yield."
        else:
            message = f"✅ Protocol Risk: Low ({adjusted_score:.0f}%). Minimal risk of protocol failure due to high yield, stable TVL, large pool size, or excellent trust score."
    elif category == "Advisory":
        if not risk_factors and trust_score in [1, 2]:
            message = f"⚠️ Protocol Risk: Advisory ({adjusted_score:.0f}%). Potential protocol risk due to low trust score."
        else:
            risk_message = " and ".join(risk_factors)
            message = f"⚠️ Protocol Risk: Advisory ({adjusted_score:.0f}%). Potential protocol risk due to {risk_message}"
            if trust_score in [1, 2]:
                message += " and low trust score"
            message += "."
    elif category == "High":
        risk_message = " and ".join(risk_factors)
        message = f"⚠️ Protocol Risk: High ({adjusted_score:.0f}%). Elevated risk of protocol failure due to {risk_message}"
        if trust_score in [1, 2]:
            message += " and low trust score"
        message += "."
    else:
        risk_message = " and ".join(risk_factors)
        message = f"⚠️ Protocol Risk: Critical ({adjusted_score:.0f}%). High risk of protocol failure due to {risk_message}"
        if trust_score in [1, 2]:
            message += " and low trust score"
        message += "."
    
    return adjusted_score, message, category

def simplified_monte_carlo_pool(initial_investment, apy, initial_price_asset1, initial_price_asset2,
                               current_price_asset1, current_price_asset2, expected_price_change_asset1,
                               expected_price_change_asset2, is_new_pool, num_simulations=200):
    apy_range = [max(apy * 0.5, 0), apy * 1.5]
    price_change_asset1_range = [expected_price_change_asset1 * 0.5, expected_price_change_asset1 * 1.5] if expected_price_change_asset1 >= 0 else [expected_price_change_asset1 * 1.5, expected_price_change_asset1 * 0.5]
    price_change_asset2_range = [expected_price_change_asset2 * 0.5, expected_price_change_asset2 * 1.5] if expected_price_change_asset2 >= 0 else [expected_price_change_asset2 * 1.5, expected_price_change_asset2 * 0.5]

    apy_samples = np.random.uniform(apy_range[0], apy_range[1], num_simulations)
    price_change_asset1_samples = np.random.uniform(price_change_asset1_range[0], price_change_asset1_range[1], num_simulations)
    price_change_asset2_samples = np.random.uniform(price_change_asset2_range[0], price_change_asset2_range[1], num_simulations)

    values = []
    ils = []
    for i in range(num_simulations):
        value, il = calculate_future_value(initial_investment, apy_samples[i], 12, initial_price_asset1, initial_price_asset2,
                                          current_price_asset1, current_price_asset2, price_change_asset1_samples[i],
                                          price_change_asset2_samples[i], is_new_pool)
        values.append(value)
        ils.append(il)
    
    worst_value, worst_il = sorted(zip(values, ils))[19]
    best_value, best_il = sorted(zip(values, ils))[179]
    expected_value, expected_il = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    
    return {
        "worst": {"value": worst_value, "il": worst_il},
        "expected": {"value": expected_value, "il": expected_il},
        "best": {"value": best_value, "il": best_il}
    }

# Asset Analyzer Inputs
if analysis_mode in ["Asset Analyzer", "Combined Analysis"]:
    st.sidebar.header("Asset Analyzer Parameters")
    st.sidebar.markdown("""
    **Instructions**: To get started, visit <a href="https://coinmarketcap.com" target="_blank">coinmarketcap.com</a> to find your asset’s current price, market cap, circulating supply, max supply, fully diluted valuation (FDV), 24h trading volume, Vol/Mkt Cap (24h) %, and Bitcoin’s price. Ensure these values are up-to-date, as they directly impact metrics like MCap Growth Plausibility and Liquidity. Visit <a href="https://certik.com" target="_blank">certik.com</a> for the asset’s CertiK security score. Enter the values below and adjust growth rates as needed.
    """, unsafe_allow_html=True)

    asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
    volatility = st.sidebar.number_input(
        "Asset Volatility % (Annual) [Optional]",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        help="Enter the asset's annual volatility (e.g., 50% for AVAX). Leave as 0 to derive volatility from the Fear and Greed Index."
    )
    certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
    fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0)
    growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
    market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
    market_cap = parse_market_value(market_cap_input)
    fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
    fdv = parse_market_value(fdv_input)
    circulating_supply_input = st.sidebar.text_input("Circulating Supply (Tokens)", value="")
    circulating_supply = parse_market_value(circulating_supply_input)
    max_supply_input = st.sidebar.text_input("Max Supply (Tokens) [Optional]", value="")
    max_supply = parse_market_value(max_supply_input)
    vol_mkt_cap = st.sidebar.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")

# Pool Analyzer Inputs
if analysis_mode in ["Pool Analyzer", "Combined Analysis"]:
    st.sidebar.header("Pool Analyzer Parameters")
    pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool"])
    is_new_pool = (pool_status == "New Pool")

    if is_new_pool:
        current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
        current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
        initial_price_asset1 = current_price_asset1
        initial_price_asset2 = current_price_asset2
    else:
        initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.01, step=0.01, value=88000.00, format="%.2f")
        initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
        current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.01, step=0.01, value=125000.00, format="%.2f")
        current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

    apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
    initial_tvl = st.sidebar.number_input("Initial TVL ($)", min_value=0.01, step=0.01, value=750000.00, format="%.2f")
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")
    expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")
    expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-30.0, format="%.2f")

# Calculate Button
calculate = st.sidebar.button("Calculate")

# Main Content
if calculate:
    if initial_investment == 0:
        st.error("Please enter a valid Initial Investment Amount (greater than 0).")
    else:
        # Asset Analyzer Logic
        if analysis_mode in ["Asset Analyzer", "Combined Analysis"]:
            if asset_price == 0:
                st.error("Please enter a valid Asset Price (greater than 0).")
            elif market_cap == 0 and (circulating_supply == 0 or asset_price == 0):
                st.error("Please provide either Market Cap or both Circulating Supply and Asset Price to calculate Market Cap.")
            else:
                st.subheader("Asset Analyzer Results")

                # Calculate Market Cap if not provided
                if market_cap == 0 and circulating_supply > 0 and asset_price > 0:
                    market_cap = circulating_supply * asset_price

                # Calculate Total Supply (Max Supply) if not provided
                if max_supply == 0 and fdv > 0 and asset_price > 0:
                    total_supply = fdv / asset_price
                else:
                    total_supply = max_supply

                # Calculate trading volume for Liquidity metric
                trading_volume = (vol_mkt_cap / 100) * market_cap if market_cap > 0 else 0

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
                simulations, sim_paths, all_monthly_returns = run_monte_carlo_asset(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200)

                worst_case = np.percentile(simulations, 10)
                expected_case = np.mean(simulations)
                best_case = np.percentile(simulations, 90)

                # Max Drawdown
                worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
                peak = np.maximum.accumulate(worst_path)
                drawdowns = (peak - worst_path) / peak
                max_drawdown = max(drawdowns) * 100

                # Dilution Risk
                if total_supply > 0 and circulating_supply > 0:
                    dilution_ratio = 100 * (1 - (circulating_supply / total_supply))
                    if dilution_ratio < 20:
                        dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
                    elif dilution_ratio < 50:
                        dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
                    else:
                        dilution_text = "⚠ High dilution risk: Significant token releases expected."
                else:
                    dilution_ratio = 0
                    dilution_text = "⚠ Circulating Supply or Max Supply/FDV not provided, cannot assess dilution risk."

                # Format supply values
                def format_supply(value):
                    if value >= 1_000_000_000:
                        return f"{value / 1_000_000_000:.2f}B"
                    elif value >= 1_000_000:
                        return f"{value / 1_000_000:.2f}M"
                    elif value >= 1_000:
                        return f"{value / 1_000:.2f}K"
                    else:
                        return f"{value:,.0f}"

                circulating_supply_display = format_supply(circulating_supply) if circulating_supply > 0 else "N/A"
                max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

                # Supply Concentration Risk
                if total_supply > 0 and circulating_supply > 0:
                    supply_ratio = (circulating_supply / total_supply) * 100
                    if supply_ratio < 20:
                        supply_concentration_text = "⚠ High risk: Very low circulating supply relative to max supply increases the risk of price manipulation by large holders."
                    elif supply_ratio < 50:
                        supply_concentration_text = "⚠ Moderate risk: A significant portion of tokens is not yet circulating, which may allow large holders to influence price."
                    else:
                        supply_concentration_text = "✓ Low risk: A large portion of tokens is circulating, reducing the risk of price manipulation by large holders."
                else:
                    supply_ratio = 0
                    supply_concentration_text = "⚠ Circulating Supply or Max Supply/FDV not provided, cannot assess supply concentration risk."

                # MCap Growth Plausibility
                projected_price = asset_projections[-1]
                projected_mcap = market_cap * (projected_price / asset_price)
                btc_mcap = btc_price * 21_000_000
                mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0
                if mcap_vs_btc <= 1:
                    mcap_text = "✓ Plausible growth: Small market share needed."
                elif mcap_vs_btc <= 5:
                    mcap_text = "⚠ Ambitious growth: Significant market share needed."
                else:
                    mcap_text = "⚠ Very ambitious: Large market share required."

                # Sharpe and Sortino Ratios
                annual_return = (asset_values[-1] / initial_investment - 1)
                rf_annual = risk_free_rate / 100
                std_dev = np.std(simulations) / initial_investment
                sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0

                negative_returns = [r for r in all_monthly_returns if r < 0]
                downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
                sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

                # Hurdle Rate vs. Bitcoin
                hurdle_rate = (risk_free_rate + 6) * 2
                asset_vs_hurdle = growth_rate - hurdle_rate

                if asset_vs_hurdle >= 20:
                    hurdle_label = "Strong Outperformance"
                    hurdle_color = "green-text"
                elif asset_vs_hurdle >= 0:
                    hurdle_label = "Moderate Outperformance"
                    hurdle_color = "yellow-text"
                else:
                    hurdle_label = "Below Hurdle"
                    hurdle_color = "red-text"

                # Composite Risk Score
                scores = {}
                if max_drawdown < 30:
                    scores['Max Drawdown'] = 100
                elif max_drawdown < 50:
                    scores['Max Drawdown'] = 50
                else:
                    scores['Max Drawdown'] = 0

                if dilution_ratio < 20:
                    scores['Dilution Risk'] = 100
                elif dilution_ratio < 50:
                    scores['Dilution Risk'] = 50
                else:
                    scores['Dilution Risk'] = 0

                if supply_ratio < 20:
                    scores['Supply Concentration'] = 0
                elif supply_ratio < 50:
                    scores['Supply Concentration'] = 50
                else:
                    scores['Supply Concentration'] = 100

                if mcap_vs_btc < 1:
                    scores['MCap Growth'] = 100
                elif mcap_vs_btc < 5:
                    scores['MCap Growth'] = 50
                else:
                    scores['MCap Growth'] = 0

                if sharpe_ratio > 1:
                    scores['Sharpe Ratio'] = 100
                elif sharpe_ratio > 0:
                    scores['Sharpe Ratio'] = 50
                else:
                    scores['Sharpe Ratio'] = 0

                if sortino_ratio > 1:
                    scores['Sortino Ratio'] = 100
                elif sortino_ratio > 0:
                    scores['Sortino Ratio'] = 50
                else:
                    scores['Sortino Ratio'] = 0

                certik_adjusted = 50 if certik_score == 0 else certik_score
                if certik_adjusted >= 70:
                    scores['CertiK Score'] = 100
                elif certik_adjusted >= 40:
                    scores['CertiK Score'] = 50
                else:
                    scores['CertiK Score'] = 0

                if market_cap >= 1_000_000_000:
                    scores['Market Cap'] = 100
                elif market_cap >= 10_000_000:
                    scores['Market Cap'] = 50
                else:
                    scores['Market Cap'] = 0

                if fear_and_greed <= 24:
                    scores['Fear and Greed'] = 100
                elif fear_and_greed <= 49:
                    scores['Fear and Greed'] = 75
                elif fear_and_greed == 50:
                    scores['Fear and Greed'] = 50
                elif fear_and_greed <= 74:
                    scores['Fear and Greed'] = 25
                else:
                    scores['Fear and Greed'] = 0

                if vol_mkt_cap < 1:
                    scores['Liquidity'] = 0
                elif vol_mkt_cap <= 5:
                    scores['Liquidity'] = 50
                else:
                    scores['Liquidity'] = 100

                composite_score = sum(scores.values()) / len(scores)

                # Risk-Adjusted Return Score
                return_to_hurdle_ratio = (growth_rate / hurdle_rate) if hurdle_rate > 0 else 1
                return_to_hurdle_ratio = min(return_to_hurdle_ratio, 3)
                risk_adjusted_score = composite_score * return_to_hurdle_ratio
                risk_adjusted_score = min(risk_adjusted_score, 100)

                # Composite Risk Score Assessment
                if composite_score >= 70:
                    bg_class = "risk-green"
                    insight = "Low risk profile."
                elif composite_score >= 40:
                    bg_class = "risk-yellow"
                    insight = "Moderate risk profile."
                else:
                    bg_class = "risk-red"
                    insight = "High risk profile."

                st.markdown(f"""
                    <div class="risk-assessment {bg_class}">
                        <div style="font-size: 20px; font-weight: bold; color: #333;">Composite Risk Score: <span style="color: #333;">{composite_score:.1f}</span></div>
                        <div style="font-size: 14px; margin-top: 5px; color: #333;">{insight}</div>
                    </div>
                """, unsafe_allow_html=True)

                # Key Metrics
                st.subheader("Key Metrics")
                roi = ((asset_values[-1] / initial_investment) - 1) * 100
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">💰 Investment Value (1 Year)</div>
                        <div class="metric-value">${asset_values[-1]:,.2f}</div>
                        <div class="metric-desc">Potential value in 12 months based on expected growth rate.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Max Drawdown</div>
                        <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                        <div class="metric-desc">Largest potential loss in a worst-case scenario over 12 months.</div>
                    </div>
                """, unsafe_allow_html=True)

                # Monte Carlo Analysis
                st.subheader("Simplified Monte Carlo Analysis")
                mc_data = {
                    "Scenario": ["Worst Case", "Expected Case", "Best Case"],
                    "Projected Value ($)": [worst_case, expected_case, best_case],
                    "ROI (%)": [((worst_case / initial_investment) - 1) * 100, ((expected_case / initial_investment) - 1) * 100, ((best_case / initial_investment) - 1) * 100]
                }
                mc_df = pd.DataFrame(mc_data)
                st.table(mc_df)

        # Pool Analyzer Logic
        if analysis_mode in ["Pool Analyzer", "Combined Analysis"]:
            st.subheader("Pool Analyzer Results")
            il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
            pool_value, il_impact = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
            value_if_held = (initial_investment / 2 / initial_price_asset1 * current_price_asset1) + (initial_investment / 2 / initial_price_asset2 * current_price_asset2)
            tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
            break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
            break_even_months_with_price = calculate_break_even_months_with_price_changes(
                initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
                current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
            )
            future_value, future_il = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                                            current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                            expected_price_change_asset2, is_new_pool)
            net_return = future_value / initial_investment if initial_investment > 0 else 0
            aril = ((future_value / initial_investment) - 1) * 100
            hurdle_rate = risk_free_rate + 6.0
            target_aril = hurdle_rate * 2
            pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0
            apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
            volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)
            protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

            # Core Metrics
            st.subheader("Core Metrics")
            col1, col2 = st.columns(2)
            with col1:
                if is_new_pool:
                    st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-title">📉 Initial Impermanent Loss</div>
                            <div class="metric-value green-text">0.00%</div>
                            <div class="metric-desc">No impermanent loss as it’s a new pool.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-title">📉 Impermanent Loss</div>
                            <div class="metric-value {'red-text' if il > 0 else 'green-text'}">{il:.2f}%</div>
                            <div class="metric-desc">Loss due to price divergence compared to holding assets.</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">⏳ Months to Breakeven</div>
                        <div class="metric-value {'green-text' if break_even_months <= 12 else 'red-text'}">{break_even_months} months</div>
                        <div class="metric-desc">Time to offset impermanent loss at current APY.</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 Net Return</div>
                        <div class="metric-value {'green-text' if net_return > 1 else 'red-text'}">{net_return:.2f}x</div>
                        <div class="metric-desc">Projected return after 12 months, including IL and price changes.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 ARIL</div>
                        <div class="metric-value {'green-text' if aril >= target_aril else 'red-text' if aril < hurdle_rate else 'neutral-text'}">{aril:.1f}%</div>
                        <div class="metric-desc">Annualized return after impermanent loss.</div>
                    </div>
                """, unsafe_allow_html=True)

            # Monte Carlo Analysis
            st.subheader("Simplified Monte Carlo Analysis")
            mc_results = simplified_monte_carlo_pool(
                initial_investment, apy, initial_price_asset1, initial_price_asset2,
                current_price_asset1, current_price_asset2, expected_price_change_asset1,
                expected_price_change_asset2, is_new_pool
            )
            df_monte_carlo = pd.DataFrame({
                "Scenario": ["Worst Case", "Expected Case", "Best Case"],
                "Projected Value ($)": [mc_results['worst']['value'], mc_results['expected']['value'], mc_results['best']['value']],
                "Impermanent Loss (%)": [mc_results['worst']['il'], mc_results['expected']['il'], mc_results['best']['il']]
            })
            st.table(df_monte_carlo)

        # Combined Analysis
        if analysis_mode == "Combined Analysis":
            st.subheader("Combined Analysis Summary")
            st.write("Comparing the potential returns and risks of investing in the asset versus providing liquidity in the pool.")

            # Asset Metrics
            asset_roi = ((asset_values[-1] / initial_investment) - 1) * 100
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">Asset ROI (1 Year)</div>
                    <div class="metric-value {'green-text' if asset_roi >= 0 else 'red-text'}">{asset_roi:.2f}%</div>
                    <div class="metric-desc">Return on investment if you hold the asset for 12 months.</div>
                </div>
            """, unsafe_allow_html=True)

            # Pool Metrics
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">Pool Net Return (1 Year)</div>
                    <div class="metric-value {'green-text' if net_return > 1 else 'red-text'}">{net_return:.2f}x</div>
                    <div class="metric-desc">Net return from the liquidity pool after 12 months, including IL.</div>
                </div>
            """, unsafe_allow_html=True)

            # Recommendation
            if asset_roi > aril:
                st.success("Recommendation: Holding the asset may yield better returns compared to the liquidity pool, based on your inputs.")
            else:
                st.success("Recommendation: Providing liquidity in the pool may yield better returns compared to holding the asset, based on your inputs.")

        # Portfolio Suggestion (shared across modes)
        st.subheader("Suggested Portfolio Structure")
        st.markdown(f"Based on your selected investor profile: **{investor_profile}**")
        portfolios = {
            "Conservative Investor": {
                "Stablecoin Liquidity Pools": 50.0,
                "BTC": 40.0,
                "Blue Chips": 8.0,
                "High Risk Assets": 2.0
            },
            "Growth Crypto Investor": {
                "Mixed Liquidity Pools": 30.0,
                "BTC": 30.0,
                "Blue Chips": 30.0,
                "High Risk Assets": 10.0
            },
            "Aggressive Crypto Investor": {
                "Mixed Liquidity Pools": 20.0,
                "BTC": 30.0,
                "Blue Chips": 30.0,
                "High Risk Assets": 20.0
            },
            "Bitcoin Strategist": {
                "Mixed Liquidity Pools": 10.0,
                "BTC": 80.0,
                "Blue Chips": 8.0,
                "High Risk Assets": 2.0
            }
        }
        labels = list(portfolios[investor_profile].keys())
        sizes = list(portfolios[investor_profile].values())
        colors = ['#4B5EAA', '#FFD700', '#32CD32', '#FF4D4D']
        explode = (0.05, 0, 0, 0)

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
        plt.title(f"Portfolio Allocation for {investor_profile}")
        st.pyplot(plt)
        plt.clf()
