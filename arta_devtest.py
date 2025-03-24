import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Custom CSS (merged and unified for both analyzers)
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

# Asset Analyzer Functions
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

def format_supply(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return f"{value:,.0f}"

# Pool Analyzer Functions
def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount):
    initial_value = investment_amount
    initial_amount_asset1 = (initial_value / 2) / initial_price_asset1
    initial_amount_asset2 = (initial_value / 2) / initial_price_asset2
    current_value_pool = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    il = ((value_if_held - current_value_pool) / value_if_held) * 100 if value_if_held > 0 else 0
    return max(il, 0)

def calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2):
    initial_amount_asset1 = (investment_amount / 2) / initial_price_asset1
    initial_amount_asset2 = (investment_amount / 2) / initial_price_asset2
    k = initial_amount_asset1 * initial_amount_asset2
    current_amount_asset1 = np.sqrt(k * (current_price_asset2 / current_price_asset1))
    current_amount_asset2 = k / current_amount_asset1
    pool_value = (current_amount_asset1 * current_price_asset1) + (current_amount_asset2 * current_price_asset2)
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    il_impact = value_if_held - pool_value
    return pool_value, il_impact

def calculate_tvl_decline(initial_tvl, current_tvl):
    if initial_tvl > 0:
        return ((current_tvl - initial_tvl) / initial_tvl) * 100
    return 0

def calculate_break_even_months(apy, il, pool_value, value_if_held):
    if il <= 0 or apy <= 0 or pool_value >= value_if_held:
        return 0
    monthly_apy = (apy / 100) / 12
    loss_to_recover = value_if_held - pool_value
    months = np.log(1 + (loss_to_recover / pool_value)) / np.log(1 + monthly_apy)
    return round(months, 2) if months > 0 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool):
    monthly_apy = (apy / 100) / 12
    months = 12
    future_price_asset1 = current_price_asset1 * (1 + expected_price_change_asset1 / 100)
    future_price_asset2 = current_price_asset2 * (1 + expected_price_change_asset2 / 100)
    future_value, _ = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool)
    future_value_if_held = (initial_investment / 2 / initial_price_asset1 * future_price_asset1) + (initial_investment / 2 / initial_price_asset2 * future_price_asset2)
    if future_value >= future_value_if_held:
        return 0
    loss_to_recover = future_value_if_held - future_value
    if monthly_apy <= 0 or loss_to_recover <= 0:
        return float('inf')
    break_even_months = np.log(1 + (loss_to_recover / future_value)) / np.log(1 + monthly_apy)
    return round(break_even_months, 2) if break_even_months > 0 else float('inf')

def calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool):
    monthly_apy = (apy / 100) / 12
    time_fraction = months / 12
    future_price_asset1 = current_price_asset1 * (1 + (expected_price_change_asset1 / 100) * time_fraction)
    future_price_asset2 = current_price_asset2 * (1 + (expected_price_change_asset2 / 100) * time_fraction)
    initial_amount_asset1 = (investment_amount / 2) / initial_price_asset1
    initial_amount_asset2 = (investment_amount / 2) / initial_price_asset2
    k = initial_amount_asset1 * initial_amount_asset2
    future_amount_asset1 = np.sqrt(k * (future_price_asset2 / future_price_asset1))
    future_amount_asset2 = k / future_amount_asset1
    future_pool_value = (future_amount_asset1 * future_price_asset1) + (future_amount_asset2 * future_price_asset2)
    future_value_with_yield = future_pool_value * (1 + monthly_apy) ** months
    value_if_held = (initial_amount_asset1 * future_price_asset1) + (initial_amount_asset2 * future_price_asset2)
    future_il = ((value_if_held - future_pool_value) / value_if_held) * 100 if value_if_held > 0 else 0
    return future_value_with_yield, max(future_il, 0)

def calculate_apy_margin_of_safety(pool_value, value_if_held, apy):
    if pool_value >= value_if_held or apy <= 0:
        return 100.0
    loss_to_recover = value_if_held - pool_value
    monthly_apy = (apy / 100) / 12
    break_even_months = np.log(1 + (loss_to_recover / pool_value)) / np.log(1 + monthly_apy)
    if break_even_months <= 12:
        target_monthly_apy = np.exp(np.log(1 + (loss_to_recover / pool_value)) / 12) - 1
        min_apy = target_monthly_apy * 12 * 100
        return apy - min_apy
    return 0.0

def calculate_volatility_score(il, tvl_decline):
    volatility = il + abs(tvl_decline)
    if volatility > 50:
        return volatility, f"⚠️ Volatility Score: {volatility:.0f}% - High volatility due to significant IL and TVL changes."
    return volatility, f"✅ Volatility Score: {volatility:.0f}% - Low to moderate volatility."

def calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score):
    risk_score = 0
    if apy > 50:
        risk_score += 30
    if tvl_decline < -30:
        risk_score += 30
    if current_tvl < 100000:
        risk_score += 20
    risk_score += (5 - trust_score) * 10
    if risk_score >= 75:
        return risk_score, f"⚠️ Protocol Risk: {risk_score}% - Critical risk due to high APY, TVL decline, or low trust.", "Critical"
    elif risk_score >= 50:
        return risk_score, f"⚠️ Protocol Risk: {risk_score}% - High risk; proceed with caution.", "High"
    elif risk_score >= 25:
        return risk_score, f"⚠️ Protocol Risk: {risk_score}% - Advisory; monitor closely.", "Advisory"
    return risk_score, f"✅ Protocol Risk: {risk_score}% - Low risk; protocol appears stable.", "Low"

def check_exit_conditions(investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, current_tvl, risk_free_rate, trust_score, months, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, btc_growth_rate):
    pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
    future_value, future_il = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool)
    net_return = future_value / investment_amount
    aril = ((future_value / investment_amount) - 1) * 100
    hurdle_rate = risk_free_rate + 6.0
    target_aril = hurdle_rate * 2
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (investment_amount / current_tvl) * 100 if current_tvl > 0 else 0
    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
    volatility_score, _ = calculate_volatility_score(il, tvl_decline)
    protocol_risk_score, _, _ = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    if net_return < 1.0 or aril < 0:
        st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x or ARIL {aril:.1f}% indicates a loss.")
        return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
    elif apy < hurdle_rate or net_return < 1.1:
        st.warning(f"⚠️ **Investment Risk:** Moderate. APY below Hurdle Rate ({hurdle_rate:.2f}%) or marginal profit.")
        return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
    else:
        st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability.")
        return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril

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
                if market_cap == 0 and circulating_supply > 0 and asset_price > 0:
                    market_cap = circulating_supply * asset_price
                if max_supply == 0 and fdv > 0 and asset_price > 0:
                    total_supply = fdv / asset_price
                else:
                    total_supply = max_supply
                trading_volume = (vol_mkt_cap / 100) * market_cap if market_cap > 0 else 0

                months = 12
                asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
                btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
                rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
                
                asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
                btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
                rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
                
                asset_values = [initial_investment * p / asset_price for p in asset_projections]
                btc_values = [initial_investment * p / btc_price for p in btc_projections]
                
                simulations, sim_paths, all_monthly_returns = run_monte_carlo_asset(initial_investment, growth_rate, volatility, months, fear_and_greed)
                worst_case = np.percentile(simulations, 10)
                expected_case = np.mean(simulations)
                best_case = np.percentile(simulations, 90)
                
                worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
                peak = np.maximum.accumulate(worst_path)
                drawdowns = (peak - worst_path) / peak
                max_drawdown = max(drawdowns) * 100

                if total_supply > 0 and circulating_supply > 0:
                    dilution_ratio = 100 * (1 - (circulating_supply / total_supply))
                else:
                    dilution_ratio = 0
                
                circulating_supply_display = format_supply(circulating_supply) if circulating_supply > 0 else "N/A"
                max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

                projected_price = asset_projections[-1]
                projected_mcap = market_cap * (projected_price / asset_price)
                btc_mcap = btc_price * 21_000_000
                mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0

                annual_return = (asset_values[-1] / initial_investment - 1)
                rf_annual = risk_free_rate / 100
                std_dev = np.std(simulations) / initial_investment
                sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0

                negative_returns = [r for r in all_monthly_returns if r < 0]
                downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
                sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

                hurdle_rate = (risk_free_rate + 6) * 2
                asset_vs_hurdle = growth_rate - hurdle_rate

                st.subheader("Key Metrics")
                roi = ((asset_values[-1] / initial_investment) - 1) * 100
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">💰 Investment Value (1 Year)</div>
                        <div class="metric-value">${asset_values[-1]:,.2f}</div>
                        <div class="metric-desc">This shows your ${initial_investment:,.2f} investment’s potential value in 12 months based on the expected growth rate.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Max Drawdown</div>
                        <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                        <div class="metric-desc">Largest potential loss in a worst-case scenario over 12 months from Monte Carlo.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📊 Sharpe Ratio</div>
                        <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                        <div class="metric-desc">Return per unit of risk taken.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">⚖️ Dilution Risk</div>
                        <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                        <div class="metric-desc">Percentage of tokens yet to be released (Circulating: {circulating_supply_display}, Max: {max_supply_display}).</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 MCap Growth Plausibility</div>
                        <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                        <div class="metric-desc">Compares projected market cap to Bitcoin’s.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Sortino Ratio</div>
                        <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                        <div class="metric-desc">Return per unit of downside risk.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 Hurdle Rate vs. Bitcoin</div>
                        <div class="metric-value {'green-text' if asset_vs_hurdle >= 20 else 'yellow-text' if asset_vs_hurdle >= 0 else 'red-text'}">{asset_vs_hurdle:.2f}%</div>
                        <div class="metric-desc">Growth compared to minimum return needed to beat Bitcoin.</div>
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
            value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
            tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
            result = check_exit_conditions(
                investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, btc_growth_rate
            )
            break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril = result

            st.subheader("Core Metrics")
            col1, col2 = st.columns(2)
            
            def get_value_color(metric_name, value, hurdle_rate=None, target_aril=None):
                if metric_name in ["Impermanent Loss", "Projected Impermanent Loss"]:
                    return "red" if value > 0 else "green"
                elif metric_name == "TVL Growth":
                    return "green" if value >= 0 else "red"
                elif metric_name == "TVL Decline":
                    return "red" if value > 0 else "green"
                elif metric_name == "Net Return":
                    return "green" if value > 1 else "red"
                elif metric_name in ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"]:
                    return "green" if value <= 12 else "red"
                elif metric_name == "Pool Share":
                    return "green" if value < 5 else "red"
                elif metric_name == "ARIL":
                    if value < hurdle_rate:
                        return "red"
                    elif value >= target_aril:
                        return "green"
                    else:
                        return "neutral"
                return "neutral"

            with col1:
                if is_new_pool:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">📉 Initial Impermanent Loss</div>
                            <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                            <div class="metric-note">No IL as it’s a new pool. Monitor price changes for future IL.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">🔮 Projected Impermanent Loss (12 months)</div>
                            <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                            <div class="metric-note">Based on expected price changes.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">📉 Impermanent Loss (Current)</div>
                            <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                            <div class="metric-note">Loss due to price divergence from entry.</div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">⏳ Months to Breakeven Against IL</div>
                        <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months)}">{break_even_months}</div>
                        <div class="metric-note">Time to offset current IL with APY.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">⏳ Months to Breakeven with Price Changes</div>
                        <div class="metric-value {get_value_color('Months to Breakeven Including Expected Price Changes', break_even_months_with_price)}">{break_even_months_with_price}</div>
                        <div class="metric-note">Time to offset IL including expected price changes.</div>
                    </div>
                """, unsafe_allow_html=True)
                if initial_tvl > 0:
                    metric_name = "TVL Growth" if tvl_decline >= 0 else "TVL Decline"
                    display_value = abs(tvl_decline)
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">📊 {metric_name}</div>
                            <div class="metric-value {get_value_color(metric_name, display_value)}">{display_value:.2f}%</div>
                            <div class="metric-note">Change in TVL since entry.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">📊 TVL Change</div>
                            <div class="metric-value">N/A</div>
                            <div class="metric-note">Set Initial TVL to calculate change.</div>
                        </div>
                    """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📈 Net Return</div>
                        <div class="metric-value {get_value_color('Net Return', net_return)}">{net_return:.2f}x</div>
                        <div class="metric-note">Return after 12 months including IL and price changes.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">🎯 Hurdle Rate</div>
                        <div class="metric-value">{hurdle_rate:.2f}%</div>
                        <div class="metric-note">Risk-free rate + 6% inflation.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📈 ARIL</div>
                        <div class="metric-value {get_value_color('ARIL', aril, hurdle_rate, hurdle_rate * 2)}">{aril:.1f}%</div>
                        <div class="metric-note">Annualized return after IL.</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">🔗 Pool Share</div>
                        <div class="metric-value {get_value_color('Pool Share', pool_share)}">{pool_share:.2f}%</div>
                        <div class="metric-note">Your share of the pool’s TVL.</div>
                    </div>
                """, unsafe_allow_html=True)
