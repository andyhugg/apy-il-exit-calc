import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Core Calculation Functions from Pool Analyzer
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float, initial_investment: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    return round(il_percentage, 2) if il_percentage > 0.01 else il_percentage

def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                        current_price_asset1: float, current_price_asset2: float) -> tuple[float, float]:
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(initial_investment: float, apy: float, months: int, initial_price_asset1: float, initial_price_asset2: float,
                          current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                          expected_price_change_asset2: float, is_new_pool: bool = False) -> tuple[float, float]:
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

def calculate_break_even_months(apy: float, il: float, initial_pool_value: float, value_if_held: float) -> float:
    if apy <= 0 or initial_pool_value <= 0 or value_if_held <= initial_pool_value:
        return 0
    monthly_apy = (apy / 100) / 12
    months = 0
    current_value = initial_pool_value
    while current_value < value_if_held and months < 1000:
        current_value *= (1 + monthly_apy)
        months += 1
    return round(months, 2) if months < 1000 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment: float, apy: float, pool_value: float,
                                                  initial_price_asset1: float, initial_price_asset2: float,
                                                  current_price_asset1: float, current_price_asset2: float,
                                                  expected_price_change_asset1: float, expected_price_change_asset2: float,
                                                  value_if_held: float, is_new_pool: bool = False) -> float:
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

def simplified_monte_carlo_analysis(initial_investment: float, apy: float, initial_price_asset1: float, initial_price_asset2: float,
                                   current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                                   expected_price_change_asset2: float, is_new_pool: bool, num_simulations: int = 200) -> dict:
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
    worst_value, worst_il = sorted(zip(values, ils))[19]  # 10th percentile
    best_value, best_il = sorted(zip(values, ils))[179]   # 90th percentile
    expected_value, expected_il = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    return {
        "worst": {"value": worst_value, "il": worst_il},
        "expected": {"value": expected_value, "il": expected_il},
        "best": {"value": best_value, "il": best_il}
    }

def calculate_composite_risk_score(tvl: float, platform_trust_score: float, apy: float) -> float:
    normalized_tvl = min(tvl / 1000000, 1.0)
    normalized_platform_score = platform_trust_score / 5.0
    normalized_apy = min(apy / 50.0, 1.0)
    if apy > 300:
        normalized_apy *= 0.5
    composite_score = (0.4 * normalized_tvl + 0.3 * normalized_platform_score + 0.3 * normalized_apy) * 100
    return round(composite_score, 1)

def get_composite_score_context(composite_score: float) -> tuple[str, str]:
    if composite_score <= 20:
        category = "Very High Risk"
        description = "This pool has very high risk factors."
    elif composite_score <= 40:
        category = "High Risk"
        description = "This pool has high risk factors."
    elif composite_score <= 60:
        category = "Moderate Risk"
        description = "This pool has moderate risk factors."
    elif composite_score <= 80:
        category = "Low Risk"
        description = "This pool has low risk factors."
    else:
        category = "Very Low Risk"
        description = "This pool has very low risk factors."
    return category, description

def generate_pdf_report(il, net_return, future_value, break_even_months, break_even_months_with_price, 
                        drawdown_initial, drawdown_12_months, current_tvl, platform_trust_score, composite_score, 
                        hurdle_rate, hurdle_value_12_months, risk_messages):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Liquidity Pool Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Key Insights", styles['Heading2']))
    story.append(Paragraph(f"Current Impermanent Loss: {il:.2f}%", styles['BodyText']))
    story.append(Paragraph(f"12-Month Outlook: ${future_value:,.0f} ({net_return:.2f}x return)", styles['BodyText']))
    story.append(Paragraph(f"Current TVL: ${current_tvl:,.0f}", styles['BodyText']))
    story.append(Paragraph(f"Breakeven Time: Against IL: {break_even_months} months, With Price Changes: {break_even_months_with_price} months", styles['BodyText']))
    story.append(Paragraph(f"Worst-Case Drawdown (90%): Initial: ${drawdown_initial:,.0f}, After 12 Months: ${drawdown_12_months:,.0f}", styles['BodyText']))
    story.append(Paragraph(f"Hurdle Rate: {hurdle_rate:.1f}% (${hurdle_value_12_months:,.0f} after 12 months)", styles['BodyText']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Summary", styles['Heading2']))
    if risk_messages:
        story.append(Paragraph(f"High Risk: {', '.join(risk_messages)}", styles['BodyText']))
    else:
        story.append(Paragraph("Low Risk: Profitable with manageable IL", styles['BodyText']))
    story.append(Paragraph(f"Platform Trust Score: {platform_trust_score} (1-5)", styles['BodyText']))
    category, description = get_composite_score_context(composite_score)
    story.append(Paragraph(f"Composite Risk Score: {composite_score:.1f} ({category}) - {description}", styles['BodyText']))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

# Functions from Crypto Valuations
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
def run_monte_carlo(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200):
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

# Combined CSS
st.markdown("""
    <style>
    /* Pool Analyzer Styles */
    .pool-metric-card {
        background-color: #f0f0f0;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .pool-metric-label {
        font-size: 14px;
        color: #333;
        font-weight: bold;
    }
    .pool-metric-value {
        font-size: 16px;
        color: #000;
    }
    .pool-metric-note {
        font-size: 12px;
        color: #666;
        font-style: italic;
    }
    /* Arta Crypto Valuations Styles */
    .arta-metric-tile {
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
    .arta-metric-title {
        font-size: 18px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
    }
    .arta-metric-value {
        font-size: 24px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
        white-space: normal;
        word-wrap: break-word;
    }
    .arta-metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 120px;
        line-height: 1.4;
    }
    .arta-red-text { color: #FF4D4D; }
    .arta-green-text { color: #32CD32; }
    .arta-yellow-text { color: #FFD700; }
    .arta-neutral-text { color: #A9A9A9; }
    .arta-risk-assessment {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
    }
    .arta-risk-red { background-color: #FF4D4D; }
    .arta-risk-yellow { background-color: #FFD700; }
    .arta-risk-green { background-color: #32CD32; }
    .arta-proj-table-container {
        overflow-x: auto;
        max-width: 100%;
    }
    .arta-proj-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(to bottom, #1E2A44, #6A82FB);
    }
    .arta-proj-table th, .arta-proj-table td {
        padding: 12px;
        text-align: center;
        color: white;
        border: 1px solid #2A3555;
        font-size: 14px;
    }
    .arta-proj-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .arta-disclaimer {
        border: 2px solid #FF4D4D;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
        font-style: italic;
    }
    .arta-large-logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        max-width: 90%;
        padding-top: 20px;
        padding-bottom: 30px;
    }
    @media (max-width: 768px) {
        .arta-metric-tile {
            flex-direction: column;
            align-items: flex-start;
        }
        .arta-metric-title, .arta-metric-value, .arta-metric-desc {
            width: 100%;
            min-width: 0;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Main App
st.title("Crypto Analysis Suite")

# Tabs
tab1, tab2 = st.tabs(["Simple Pool Analyzer", "Arta Crypto Valuations"])

# Sidebar Inputs
with st.sidebar:
    st.header("Analysis Settings")
    tab_choice = st.radio("Select Tool", ["Pool Analyzer", "Crypto Valuations"], index=0)

    if tab_choice == "Pool Analyzer":
        st.subheader("Pool Analyzer Inputs")
        pool_status = st.selectbox("Pool Status", ["Existing Pool", "New Pool"])
        is_new_pool = (pool_status == "New Pool")
        if is_new_pool:
            current_price_asset1 = st.number_input("Asset 1 Price (Today) ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_current_price_asset1")
            current_price_asset2 = st.number_input("Asset 2 Price (Today) ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_current_price_asset2")
            initial_price_asset1 = current_price_asset1
            initial_price_asset2 = current_price_asset2
        else:
            initial_price_asset1 = st.number_input("Initial Asset 1 Price ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_initial_price_asset1")
            initial_price_asset2 = st.number_input("Initial Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_initial_price_asset2")
            current_price_asset1 = st.number_input("Current Asset 1 Price ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_current_price_asset1")
            current_price_asset2 = st.number_input("Current Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_current_price_asset2")
        investment_amount = st.number_input("Investment ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_investment")
        apy = st.number_input("APY (%)", min_value=0.01, value=25.00, format="%.2f", key="pool_apy")
        expected_price_change_asset1 = st.number_input("Expected Price Change Asset 1 (%)", min_value=-100.0, value=1.0, format="%.2f", key="pool_price_change_asset1")
        expected_price_change_asset2 = st.number_input("Expected Price Change Asset 2 (%)", min_value=-100.0, value=1.0, format="%.2f", key="pool_price_change_asset2")
        current_tvl = st.number_input("Current TVL ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_tvl")
        platform_trust_score = st.selectbox(
            "Platform Trust Score (1-5)",
            options=[(1, "1 - Unknown"), (2, "2 - Poor"), (3, "3 - Moderate"), (4, "4 - Good"), (5, "5 - Excellent")],
            format_func=lambda x: x[1],
            index=0,
            key="pool_trust_score"
        )[0]
        current_btc_price = st.number_input("Current BTC Price ($)", min_value=0.01, value=1.00, format="%.2f", key="pool_btc_price")
        btc_growth_rate = st.number_input("Expected BTC Growth Rate (%)", min_value=-100.0, value=1.0, format="%.2f", key="pool_btc_growth")
        risk_free_rate = st.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, format="%.2f", key="pool_risk_free")
        pool_calculate = st.button("Calculate Pool", key="pool_calculate")

    else:
        st.subheader("Crypto Valuations Inputs")
        asset_price = st.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f", key="arta_asset_price")
        volatility = st.number_input("Asset Volatility % (Annual)", min_value=0.0, max_value=100.0, value=0.0, key="arta_volatility")
        certik_score = st.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0, key="arta_certik")
        fear_and_greed = st.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0, key="arta_fear_greed")
        growth_rate = st.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0, key="arta_growth")
        market_cap_input = st.text_input("Current Market Cap ($)", value="", key="arta_market_cap")
        fdv_input = st.text_input("Fully Diluted Valuation (FDV) ($)", value="", key="arta_fdv")
        circulating_supply_input = st.text_input("Circulating Supply (Tokens)", value="", key="arta_circ_supply")
        max_supply_input = st.text_input("Max Supply (Tokens)", value="", key="arta_max_supply")
        vol_mkt_cap = st.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="arta_vol_mkt")
        initial_investment = st.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0, key="arta_investment")
        btc_price = st.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0, key="arta_btc_price")
        btc_growth = st.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0, key="arta_btc_growth")
        risk_free_rate = st.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0, key="arta_risk_free")
        investor_profile = st.selectbox(
            "Investor Profile",
            ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
            index=0,
            key="arta_investor_profile"
        )
        arta_calculate = st.button("Calculate Valuations", key="arta_calculate")

# Pool Analyzer Logic
def run_pool_analyzer():
    st.write("Evaluate your liquidity pool with key insights and minimal clutter.")
    st.image("https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/dm-pools.png", use_container_width=True)
    
    if 'pool_calculate' in st.session_state and st.session_state.pool_calculate:
        with st.spinner("Calculating..."):
            result = check_exit_conditions(
                investment_amount, apy, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                current_tvl, risk_free_rate, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, platform_trust_score
            )
            (il, net_return, future_value, break_even_months, break_even_months_with_price, 
             drawdown_initial, drawdown_12_months, hurdle_rate, hurdle_value_12_months, composite_score, risk_messages) = result

            st.subheader("Projected Pool Value Over Time")
            time_periods = [0, 3, 6, 12]
            future_values = []
            for months in time_periods:
                value, _ = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                 current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                 expected_price_change_asset2, is_new_pool)
                future_values.append(value)
            hurdle_rate_chart = 0.16
            hurdle_values = [investment_amount * (1 + hurdle_rate_chart * (months / 12)) for months in time_periods]
            sns.set_theme()
            plt.figure(figsize=(10, 6))
            plt.plot(time_periods, future_values, marker='o', color='#1f77b4', label="Pool Value")
            plt.plot(time_periods, hurdle_values, linestyle='--', color='green', label="Hurdle Rate (16%)")
            plt.axhline(y=investment_amount, color='#ff3333', linestyle='--', label=f"Initial Investment (${investment_amount:,.0f})")
            plt.title("Projected Pool Value Over Time")
            plt.xlabel("Months")
            plt.ylabel("Value ($)")
            plt.legend()
            st.pyplot(plt)

            # Add other outputs (tables, Monte Carlo, etc.) similarly...

def check_exit_conditions(initial_investment, apy, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl, risk_free_rate, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, platform_trust_score):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                        current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    value_if_held = (initial_investment / 2 / initial_price_asset1 * current_price_asset1) + (initial_investment / 2 / initial_price_asset2 * current_price_asset2)
    future_value, _ = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                            current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                            expected_price_change_asset2, is_new_pool)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    drawdown_initial = initial_investment * 0.1
    drawdown_12_months = future_value * 0.1
    hurdle_rate = risk_free_rate + 6.0
    hurdle_value_12_months = initial_investment * (1 + hurdle_rate / 100)

    st.subheader("Key Insights")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="pool-metric-card">
            <div class="pool-metric-label">Current Impermanent Loss</div>
            <div class="pool-metric-value">{il:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    # Add other metrics similarly...

    st.subheader("Risk Summary")
    risk_messages = []
    if net_return < 1.0:
        risk_messages.append("Loss projected")
    if il > 5.0:
        risk_messages.append("High IL")
    composite_score = calculate_composite_risk_score(current_tvl, platform_trust_score, apy)
    category, description = get_composite_score_context(composite_score)
    if risk_messages:
        st.error(f"⚠️ High Risk: {', '.join(risk_messages)}")
    else:
        st.success("✅ Low Risk: Profitable with manageable IL")
    st.markdown(f"**Composite Risk Score**: {composite_score} ({category}) - {description}")

    return (il, net_return, future_value, break_even_months, break_even_months_with_price, 
            drawdown_initial, drawdown_12_months, hurdle_rate, hurdle_value_12_months, composite_score, risk_messages)

# Crypto Valuations Logic
def run_crypto_valuations():
    st.markdown(
        f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="arta-large-logo" width="600"></div>',
        unsafe_allow_html=True
    )
    st.write("Arta Crypto Valuations - Know the Price. Master the Risk.")
    
    if 'arta_calculate' in st.session_state and st.session_state.arta_calculate:
        market_cap = parse_market_value(market_cap_input)
        fdv = parse_market_value(fdv_input)
        circulating_supply = parse_market_value(circulating_supply_input)
        max_supply = parse_market_value(max_supply_input)
        
        if asset_price == 0 or initial_investment == 0:
            st.error("Please enter valid values for Asset Price and Initial Investment.")
        elif market_cap == 0 and (circulating_supply == 0 or asset_price == 0):
            st.error("Please provide either Market Cap or both Circulating Supply and Asset Price.")
        else:
            if market_cap == 0 and circulating_supply > 0 and asset_price > 0:
                market_cap = circulating_supply * asset_price
            if max_supply == 0 and fdv > 0 and asset_price > 0:
                total_supply = fdv / asset_price
            else:
                total_supply = max_supply

            months = 12
            asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
            asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
            asset_values = [initial_investment * p / asset_price for p in asset_projections]
            
            simulations, sim_paths, all_monthly_returns = run_monte_carlo(initial_investment, growth_rate, volatility, months, fear_and_greed)
            worst_case = np.percentile(simulations, 10)
            expected_case = np.mean(simulations)
            best_case = np.percentile(simulations, 90)
            
            st.subheader("Key Metrics")
            st.markdown(f"""
                <div class="arta-metric-tile">
                    <div class="arta-metric-title">💰 Investment Value (1 Year)</div>
                    <div class="arta-metric-value">${asset_values[-1]:,.2f}</div>
                    <div class="arta-metric-desc">Potential value in 12 months.</div>
                </div>
            """, unsafe_allow_html=True)
            # Add other metrics similarly...

# Execute based on tab
with tab1:
    run_pool_analyzer()
with tab2:
    run_crypto_valuations()
