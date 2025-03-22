import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Pool Profit and Risk Analyzer Functions
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

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_change = (current_tvl - initial_tvl) / initial_tvl * 100
    return round(tvl_change, 2)

def calculate_apy_margin_of_safety(initial_pool_value: float, value_if_held: float, current_apy: float, months: int = 12) -> float:
    target_value = value_if_held * 1.02
    min_apy = ((target_value / initial_pool_value) ** (12 / months) - 1) * 100
    apy_mos = ((current_apy - min_apy) / current_apy) * 100 if current_apy > 0 else 0
    return max(0, min(apy_mos, 100))

def calculate_volatility_score(il_percentage: float, tvl_decline: float) -> tuple[float, str]:
    il_factor = min(il_percentage / 5, 1.0)
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)
    volatility_score = (il_factor + tvl_factor) * 25
    final_score = min(volatility_score, 50)

    if final_score <= 25:
        message = f"✅ Volatility Score: Low ({final_score:.0f}%). Stable conditions with low IL and TVL decline."
    else:
        message = f"⚠️ Volatility Score: Moderate ({final_score:.0f}%). Moderate IL or TVL decline may impact returns."
    
    return final_score, message

def calculate_protocol_risk_score(apy: float, tvl_decline: float, current_tvl: float, trust_score: int) -> tuple[float, str, str]:
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

def check_exit_conditions(initial_investment: float, apy: float, il: float, tvl_decline: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl: float, risk_free_rate: float, trust_score: int, months: int = 12, 
                         expected_price_change_asset1: float = 0.0, expected_price_change_asset2: float = 0.0, 
                         is_new_pool: bool = False, btc_growth_rate: float = 0.0):
    pool_value, il_impact = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    value_if_held = (initial_investment / 2 / initial_price_asset1 * current_price_asset1) + (initial_investment / 2 / initial_price_asset2 * current_price_asset2)
    
    future_value, future_il = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                    expected_price_change_asset2, is_new_pool)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    aril = ((future_value / initial_investment) - 1) * 100
    hurdle_rate = risk_free_rate + 6.0
    target_aril = hurdle_rate * 2
    
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
    volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)
    protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    # [Metric cards and display logic remains unchanged, included here for completeness]
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>Core Metrics</h1>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1f2a44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-title {
        font-weight: bold;
        font-size: 16px;
        color: #ffffff;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 20px;
        font-weight: 500;
    }
    .metric-value.green {
        color: #00cc00;
    }
    .metric-value.red {
        color: #ff3333;
    }
    .metric-value.neutral {
        color: #ffffff;
    }
    .metric-note {
        font-size: 12px;
        color: #b0b0b0;
        margin-top: 5px;
        flex: 1;
        white-space: normal;
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True)

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
            il_note = "Your pool has no impermanent loss as it’s a new pool."
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📉 Initial Impermanent Loss</div>
                <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                <div class="metric-note">{il_note}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🔮 Projected Impermanent Loss</div>
                <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                <div class="metric-note">(based on expected price changes)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            il_note = "IL calculated for existing pool."
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📉 Impermanent Loss</div>
                <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                <div class="metric-note">{il_note}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Against IL</div>
            <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months)}">{break_even_months}</div>
            <div class="metric-note">Time to offset IL with current APY</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Net Return</div>
            <div class="metric-value {get_value_color('Net Return', net_return)}">{net_return:.2f}x</div>
            <div class="metric-note">Return after 12 months</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 ARIL</div>
            <div class="metric-value {get_value_color('ARIL', aril, hurdle_rate, target_aril)}">{aril:.1f}%</div>
            <div class="metric-note">Annualized Return After IL</div>
        </div>
        """, unsafe_allow_html=True)

    # [Remaining check_exit_conditions logic for risk management and investment alerts]

    return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril

# Streamlit App
st.title("Pool Profit and Risk Analyzer")

st.sidebar.header("Set Your Pool or Asset Parameters")

pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool", "New Asset"])
is_new_pool = (pool_status == "New Pool")
is_new_asset = (pool_status == "New Asset")

if is_new_asset:
    asset_price = st.sidebar.number_input("Asset Price ($)", min_value=0.01, step=0.01, value=100.00, format="%.2f")
    certik_score = st.sidebar.number_input("Certik Score (0-100)", min_value=0, max_value=100, step=1, value=75)
    st.sidebar.markdown("**Note:** Certik Score reflects security audit rating.")
    market_cap = st.sidebar.number_input("Market Cap ($)", min_value=0.01, step=1000.0, value=1000000.00, format="%.2f")
    twitter_followers = st.sidebar.number_input("Twitter Followers", min_value=0, step=100, value=5000)
    twitter_posts = st.sidebar.number_input("Twitter Posts", min_value=0, step=10, value=100)
    expected_growth_rate = st.sidebar.number_input("Expected Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=20.0, format="%.2f")
    current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=84000.00, format="%.2f")
    btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=50.0, format="%.2f")
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
    investment_amount = st.sidebar.number_input("Investment Amount ($)", min_value=0.01, step=0.01, value=1000.00, format="%.2f")

    current_price_asset1 = asset_price
    current_price_asset2 = 1.00
    initial_price_asset1 = asset_price
    initial_price_asset2 = 1.00
    expected_price_change_asset1 = expected_growth_rate
    expected_price_change_asset2 = 0.0
    trust_score = max(1, min(5, int(certik_score / 20)))
    apy = 0.0
    initial_tvl = market_cap
    current_tvl = market_cap
elif is_new_pool:
    current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    initial_price_asset1 = current_price_asset1
    initial_price_asset2 = current_price_asset2
else:
    initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.01, step=0.01, value=88000.00, format="%.2f")
    initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.01, step=0.01, value=125000.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

if not is_new_asset:
    apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=2000.00, format="%.2f")
    initial_tvl = st.sidebar.number_input("Initial TVL ($)", min_value=0.01, step=0.01, value=750000.00, format="%.2f")
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")
    trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
    expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")
    expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-30.0, format="%.2f")
    initial_btc_price = st.sidebar.number_input("Initial BTC Price ($)", min_value=0.0, step=0.01, value=84000.00, format="%.2f")
    current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=84000.00, format="%.2f")
    btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl) if not is_new_asset else 0.0
        break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
        break_even_months_with_price = calculate_break_even_months_with_price_changes(
            investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool or is_new_asset
        )
        result = check_exit_conditions(
            investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool or is_new_asset, btc_growth_rate
        )
        break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril = result
        
        if is_new_asset:
            st.subheader("Projected Asset Value Based on Expected Growth Rate")
            time_periods = [0, 3, 6, 12]
            future_values = []
            for months in time_periods:
                monthly_growth = (expected_growth_rate / 100) / 12
                value = investment_amount * (1 + monthly_growth * months)
                future_values.append(value)
            future_ils = [0.0] * len(time_periods)

            df_projection = pd.DataFrame({
                "Time Period (Months)": time_periods,
                "Projected Value ($)": [f"${int(value):,}" for value in future_values],
                "Projected Impermanent Loss (%)": [f"{il:.2f}%" for il in future_ils]
            })
            st.dataframe(df_projection.style.set_properties(**{'text-align': 'right'}), hide_index=True, use_container_width=True)

            # [Add MDD and Monte Carlo for New Asset as in previous response]
        else:
            st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
            time_periods = [0, 3, 6, 12]
            future_values = []
            future_ils = []
            for months in time_periods:
                value, il_at_time = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                          current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                          expected_price_change_asset2, is_new_pool)
                future_values.append(value)
                future_ils.append(il_at_time)
            
            df_projection = pd.DataFrame({
                "Time Period (Months)": time_periods,
                "Projected Value ($)": [f"${int(value):,}" for value in future_values],
                "Projected Impermanent Loss (%)": [f"{il:.2f}%" for il in future_ils]
            })
            st.dataframe(df_projection.style.set_properties(**{'text-align': 'right'}), hide_index=True, use_container_width=True)

            # [Add original MDD and Monte Carlo sections]
