import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import csv

# Function to calculate Impermanent Loss (IL)
def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount):
    if initial_price_asset1 <= 0 or initial_price_asset2 <= 0 or current_price_asset1 <= 0 or current_price_asset2 <= 0:
        return 0.0
    initial_ratio = initial_price_asset1 / initial_price_asset2
    current_ratio = current_price_asset1 / current_price_asset2
    price_change_ratio = current_ratio / initial_ratio
    sqrt_price_change = np.sqrt(price_change_ratio)
    il = 2 * sqrt_price_change / (1 + sqrt_price_change) - 1
    il_percentage = il * 100
    return il_percentage if il_percentage > 0 else 0.0

# Function to calculate pool value and IL impact
def calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2):
    if initial_price_asset1 <= 0 or initial_price_asset2 <= 0 or current_price_asset1 <= 0 or current_price_asset2 <= 0:
        return initial_investment, 0.0
    initial_ratio = initial_price_asset1 / initial_price_asset2
    current_ratio = current_price_asset1 / current_price_asset2
    price_change_ratio = current_ratio / initial_ratio
    sqrt_price_change = np.sqrt(price_change_ratio)
    pool_value = initial_investment * (2 * sqrt_price_change / (1 + sqrt_price_change))
    il_impact = initial_investment - pool_value
    return pool_value, il_impact

# Function to calculate future pool value with APY and expected price changes
def calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                           current_price_asset1, current_price_asset2, expected_price_change_asset1,
                           expected_price_change_asset2, is_new_pool):
    if initial_investment <= 0 or months <= 0:
        return initial_investment, 0.0
    monthly_apy = (apy / 100) / 12
    periods = months
    future_price_asset1 = current_price_asset1 * (1 + (expected_price_change_asset1 / 100))
    future_price_asset2 = current_price_asset2 * (1 + (expected_price_change_asset2 / 100))
    future_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                                future_price_asset1, future_price_asset2)
    future_il = calculate_il(initial_price_asset1, initial_price_asset2, future_price_asset1, future_price_asset2, initial_investment)
    for _ in range(periods):
        future_pool_value += future_pool_value * monthly_apy
    return future_pool_value, future_il

# Function to calculate break-even months against IL
def calculate_break_even_months(apy, il, pool_value, value_if_held):
    if apy <= 0 or pool_value <= 0 or value_if_held <= pool_value:
        return 0
    monthly_apy = (apy / 100) / 12
    il_loss = (il / 100) * pool_value
    required_gain = value_if_held - pool_value + il_loss
    if required_gain <= 0:
        return 0
    months = 0
    current_value = pool_value
    while current_value < (pool_value + required_gain) and months < 120:
        current_value += current_value * monthly_apy
        months += 1
    return months if months < 120 else 120

# Function to calculate break-even months including expected price changes
def calculate_break_even_months_with_price_changes(initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
                                                   current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                   expected_price_change_asset2, value_if_held, is_new_pool):
    if apy <= 0 or initial_investment <= 0:
        return 0
    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    current_value = pool_value
    months = 0
    while months < 120:
        future_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        future_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        future_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                               future_price_asset1, future_price_asset2)
        future_value += future_value * monthly_apy * months
        value_if_held_future = (initial_investment / 2 / initial_price_asset1 * future_price_asset1) + \
                              (initial_investment / 2 / initial_price_asset2 * future_price_asset2)
        if future_value >= value_if_held_future:
            return months
        months += 1
    return months if months < 120 else 120

# Function to calculate TVL decline
def calculate_tvl_decline(initial_tvl, current_tvl):
    if initial_tvl <= 0 or current_tvl <= 0:
        return 0.0
    tvl_change = ((current_tvl - initial_tvl) / initial_tvl) * 100
    return -tvl_change if tvl_change < 0 else tvl_change

# Function to calculate APY margin of safety
def calculate_apy_margin_of_safety(pool_value, value_if_held, apy):
    if pool_value <= 0 or apy <= 0:
        return 0.0
    target_value = value_if_held
    if pool_value >= target_value:
        return 100.0
    monthly_apy = (apy / 100) / 12
    months = 0
    current_value = pool_value
    while current_value < target_value and months < 12:
        current_value += current_value * monthly_apy
        months += 1
    if months >= 12:
        min_apy = apy
        step = apy / 2
        while step > 0.01:
            test_apy = min_apy - step
            if test_apy <= 0:
                break
            test_monthly_apy = (test_apy / 100) / 12
            test_value = pool_value
            for _ in range(12):
                test_value += test_value * test_monthly_apy
            if test_value >= target_value:
                min_apy = test_apy
            else:
                min_apy += step
            step /= 2
        apy_mos = ((apy - min_apy) / apy) * 100 if apy > 0 else 0.0
        return apy_mos if apy_mos > 0 else 0.0
    return 100.0

# Function to calculate volatility score
def calculate_volatility_score(il, tvl_decline):
    il_score = min(il / 5, 1.0) * 50
    tvl_score = min(tvl_decline / 50, 1.0) * 50
    volatility_score = (il_score + tvl_score) / 2
    if volatility_score > 25:
        return volatility_score, f"⚠️ Volatility Score: {volatility_score:.0f}% (High volatility due to IL and TVL decline)"
    return volatility_score, f"✅ Volatility Score: {volatility_score:.0f}% (Low volatility)"

# Function to calculate protocol risk score
def calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score):
    apy_risk = min(apy / 50, 1.0) * 25
    tvl_decline_risk = min(tvl_decline / 50, 1.0) * 25
    tvl_size_risk = (1 - min(current_tvl / 1000000, 1.0)) * 25
    trust_risk = (5 - trust_score) / 5 * 25
    protocol_risk_score = apy_risk + tvl_decline_risk + tvl_size_risk + trust_risk
    if protocol_risk_score >= 75:
        return protocol_risk_score, f"⚠️ Protocol Risk: {protocol_risk_score:.0f}% (Critical risk due to high APY, TVL decline, small TVL, or low trust)", "Critical"
    elif protocol_risk_score >= 50:
        return protocol_risk_score, f"⚠️ Protocol Risk: {protocol_risk_score:.0f}% (High risk, proceed with caution)", "High"
    elif protocol_risk_score >= 25:
        return protocol_risk_score, f"⚠️ Protocol Risk: {protocol_risk_score:.0f}% (Advisory: Moderate risk, review protocol details)", "Advisory"
    return protocol_risk_score, f"✅ Protocol Risk: {protocol_risk_score:.0f}% (Low risk, protocol appears stable)", "Low"

# Function to check exit conditions and display metrics
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
    
    # Simplified Hurdle Rate: Risk-Free Rate + 6% global inflation
    hurdle_rate = risk_free_rate + 6.0
    
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
    volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)
    protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    # Core Metrics Section with Evenly Sized Blocks
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>Core Metrics</h1>", unsafe_allow_html=True)
    st.write("Debug: Core Metrics header rendered.")  # Debug point

    # Custom CSS for metric cards with fixed height (simplified)
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1f2a44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        min-height: 120px; /* Fixed height to ensure uniformity */
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
    }
    </style>
    """, unsafe_allow_html=True)
    st.write("Debug: Core Metrics CSS applied.")  # Debug point

    # Split into two columns
    col1, col2 = st.columns(2)
    st.write("Debug: Columns created.")  # Debug point

    # Helper function to determine value color
    def get_value_color(metric_name, value):
        if metric_name in ["Impermanent Loss", "TVL Decline", "Projected Impermanent Loss"]:
            return "red" if value > 0 else "green"
        elif metric_name == "Net Return":
            return "green" if value > 1 else "red"
        elif metric_name in ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"]:
            return "green" if value <= 12 else "red"
        elif metric_name == "Pool Share":
            return "green" if value < 5 else "red"
        return "neutral"

    # Metrics for Column 1
    with col1:
        if initial_tvl <= 0:
            if is_new_pool:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">(new pool, IL starts at 0)</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                    <div class="metric-note">(based on expected price changes)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if is_new_pool:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">(new pool, IL starts at 0)</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                    <div class="metric-note">(based on expected price changes)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Against IL</div>
            <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months)}">{break_even_months} months</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Including Expected Price Changes</div>
            <div class="metric-value {get_value_color('Months to Breakeven Including Expected Price Changes', break_even_months_with_price)}">{break_even_months_with_price} months</div>
        </div>
        """, unsafe_allow_html=True)
    st.write("Debug: Column 1 metrics rendered.")  # Debug point

    # Metrics for Column 2
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Net Return</div>
            <div class="metric-value {get_value_color('Net Return', net_return)}">{net_return:.2f}x</div>
            <div class="metric-note">(includes expected price changes for Asset 1 and Asset 2)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Hurdle Rate</div>
            <div class="metric-value {get_value_color('Hurdle Rate', hurdle_rate)}">{hurdle_rate:.2f}%</div>
            <div class="metric-note">(Your {risk_free_rate}% risk-free rate + 6% avg global inflation, 2025 est.)</div>
        </div>
        """, unsafe_allow_html=True)

        if initial_tvl <= 0:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 TVL Decline</div>
                <div class="metric-value">Cannot calculate</div>
                <div class="metric-note">Set Initial TVL to Current TVL for new pool entry.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 TVL Decline</div>
                <div class="metric-value {get_value_color('TVL Decline', tvl_decline)}">{tvl_decline:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔗 Pool Share</div>
            <div class="metric-value {get_value_color('Pool Share', pool_share)}">{pool_share:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    st.write("Debug: Column 2 metrics rendered.")  # Debug point

    st.markdown("---")
    st.markdown("<h1>Margin of Safety</h1>", unsafe_allow_html=True)
    st.write(f"**APY Margin of Safety:** {apy_mos:.2f}% (APY can decrease by this percentage before breakeven exceeds 12 months)  ")
    mos_assessment = "✅ High" if apy_mos > 50 else "⚠️ Low"
    st.write(f"**Margin of Safety Assessment:** {mos_assessment} Margin of Safety  ")

    st.markdown("---")
    st.markdown("<h1>Risk Management</h1>", unsafe_allow_html=True)
    if pool_share < 5:
        st.success(f"✅ **Pool Share Risk:** Low ({pool_share:.2f}%). Minimal impact expected on pool prices due to small share.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ **Pool Share Risk:** Moderate ({pool_share:.2f}%). Potential for price impact due to moderate pool share.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ **Pool Share Risk:** High ({pool_share:.2f}%). Significant price impact possible due to high pool share.")
    else:
        st.error(f"⚠️ **Pool Share Risk:** Critical ({pool_share:.2f}%). High risk of severe price impact due to very large pool share.")

    if initial_tvl > 0:
        if tvl_decline >= 50:
            st.error(f"⚠️ **TVL Decline Risk:** Critical ({tvl_decline:.2f}% decline). High risk of significant loss due to substantial TVL reduction.")
        elif tvl_decline >= 30:
            st.warning(f"⚠️ **TVL Decline Risk:** High ({tvl_decline:.2f}% decline). Elevated risk due to significant TVL reduction.")
        elif tvl_decline >= 15:
            st.warning(f"⚠️ **TVL Decline Risk:** Moderate ({tvl_decline:.2f}% decline). Potential risk due to moderate TVL reduction.")
        else:
            st.success(f"✅ **TVL Decline Risk:** Low ({tvl_decline:.2f}% decline). Pool health appears stable with minimal TVL reduction.")
    
    if protocol_risk_category == "Critical":
        st.error(f"⚠️ **Protocol Risk:** {protocol_risk_message.split('⚠️ Protocol Risk: ')[1]}")
    elif protocol_risk_category in ["High", "Advisory"]:
        st.warning(f"⚠️ **Protocol Risk:** {protocol_risk_message.split('⚠️ Protocol Risk: ')[1]}")
    else:
        st.success(f"✅ **Protocol Risk:** {protocol_risk_message.split('✅ Protocol Risk: ')[1]}")

    if volatility_score > 25:
        st.warning(f"⚠️ **Volatility Score:** {volatility_message.split('⚠️ Volatility Score: ')[1]}")
    else:
        st.success(f"✅ **Volatility Score:** {volatility_message.split('✅ Volatility Score: ')[1]}")

    st.markdown("---")
    st.markdown("<h1>Investment Risk Alert</h1>", unsafe_allow_html=True)
    if initial_tvl > 0:
        if net_return < 1.0 or tvl_decline >= 50 or protocol_risk_score >= 75:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x, TVL Decline {tvl_decline:.2f}%, Protocol Risk {protocol_risk_score:.0f}% indicate severe risks.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        elif apy < hurdle_rate or net_return < 1.1 or volatility_score > 25:
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            if volatility_score > 25:
                reasons.append(f"moderate volatility ({volatility_score:.0f}%)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability with low risk.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
    else:
        if net_return < 1.0:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x indicates a loss.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        elif apy < hurdle_rate or net_return < 1.1:
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos

# Streamlit App
st.title("Pool Profit and Risk Analyzer")
st.write("Debug: App started successfully.")  # Debug point 1

try:
    st.markdown("""
    Welcome to the Pool Profit and Risk Analyzer! This tool helps you evaluate the profitability and risks of liquidity pools in DeFi. By inputting your pool parameters, you can assess impermanent loss, net returns, and potential drawdowns, empowering you to make informed investment decisions. **Disclaimer:** This tool is for informational purposes only and does not constitute financial advice. Projections are estimates based on the inputs provided and are not guaranteed to reflect actual future outcomes.
    """)
    st.write("Debug: Welcome message rendered.")  # Debug point 2

    st.markdown("""
    <style>
    div[data-testid="stSidebar"] select {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    div[data-testid="stSidebar"] select option {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    div[data-testid="stSidebar"] select option:checked {
        background-color: #333333;
        color: #ffffff;
    }
    div[data-testid="stSidebar"] select option:hover {
        background-color: #444444;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)
    st.write("Debug: Sidebar styling applied.")  # Debug point 3

    st.sidebar.header("Set Your Pool Parameters")
    st.write("Debug: Sidebar header rendered.")  # Debug point 4

    pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool"])
    is_new_pool = (pool_status == "New Pool")
    st.write(f"Debug: Pool status selected - is_new_pool: {is_new_pool}")  # Debug point 5

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
    st.write("Debug: Asset prices set.")  # Debug point 6

    apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    st.sidebar.markdown("**Note:** **Annual Percentage Yield** For conservative projections, consider halving the entered APY to buffer against market volatility.")
    st.write("Debug: APY input set.")  # Debug point 7

    trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
    st.sidebar.markdown("""
    **Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
    - 1 = Unknown (default, highest caution)
    - 2 = Poor (known but with concerns)
    - 3 = Moderate (neutral, some audits)
    - 4 = Good (trusted, audited)
    - 5 = Excellent (top-tier, e.g., Uniswap, Aave)
    """)
    st.write("Debug: Trust score set.")  # Debug point 8

    investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=169.00, format="%.2f")
    initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", 
                                         min_value=0.01, step=0.01, value=855000.00, format="%.2f")
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")
    st.write("Debug: Investment and TVL inputs set.")  # Debug point 9

    expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")
    expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")
    st.sidebar.markdown("**Note:** We’ll take your expected APY and price changes, stretch them 50% up and down (e.g., 10% becomes 5-15%), and run 200 scenarios to project your pool’s value over 12 months.")
    st.write("Debug: Expected price changes set.")  # Debug point 10

    initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                               min_value=0.0, step=0.01, value=100.00, format="%.2f")
    current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=0.0, step=0.1, value=100.0, format="%.2f")
    st.write("Debug: BTC inputs set.")  # Debug point 11

    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
    st.sidebar.markdown("""
    **Note:** The Risk-Free Rate is what you could earn in a safe pool (e.g., 5-15%). The Hurdle Rate is this rate plus 6% (average global inflation in 2025), setting the minimum APY your pool needs to beat to outpace inflation and justify the risk.
    """)
    st.write("Debug: Risk-free rate set.")  # Debug point 12

    if st.sidebar.button("Calculate"):
        st.write("Debug: Calculate button clicked.")  # Debug point 13
        with st.spinner("Calculating..."):
            il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
            pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
            value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
            tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
            break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
            break_even_months_with_price = calculate_break_even_months_with_price_changes(
                investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
                current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
            )
            st.write("Debug: Calculations before check_exit_conditions completed.")  # Debug point 14
            result = check_exit_conditions(
                investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, btc_growth_rate
            )
            st.write("Debug: check_exit_conditions called.")  # Debug point 15
            break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos = result
            st.write("Debug: Results unpacked.")  # Debug point 16

            # Monte Carlo Simulation
            st.markdown("---")
            st.markdown("<h1>Monte Carlo Simulation</h1>", unsafe_allow_html=True)
            st.write("Running 200 scenarios with APY and price changes varied by ±50%...")
            scenarios = []
            for _ in range(200):
                apy_factor = np.random.uniform(0.5, 1.5)
                price_change_factor1 = np.random.uniform(0.5, 1.5)
                price_change_factor2 = np.random.uniform(0.5, 1.5)
                sim_apy = apy * apy_factor
                sim_price_change_asset1 = expected_price_change_asset1 * price_change_factor1
                sim_price_change_asset2 = expected_price_change_asset2 * price_change_factor2
                sim_future_value, _ = calculate_future_value(
                    investment_amount, sim_apy, 12, initial_price_asset1, initial_price_asset2,
                    current_price_asset1, current_price_asset2, sim_price_change_asset1, sim_price_change_asset2, is_new_pool
                )
                scenarios.append(sim_future_value)
            
            scenarios = np.array(scenarios)
            avg_future_value = np.mean(scenarios)
            st.write(f"**Average Future Value (after 12 months):** ${avg_future_value:.2f}")
            st.write(f"**Best Case (95th percentile):** ${np.percentile(scenarios, 95):.2f}")
            st.write(f"**Worst Case (5th percentile):** ${np.percentile(scenarios, 5):.2f}")

            # Plot Monte Carlo results
            fig, ax = plt.subplots()
            ax.hist(scenarios, bins=30, color='skyblue', edgecolor='black')
            ax.set_title("Monte Carlo Simulation: Future Pool Value Distribution")
            ax.set_xlabel("Future Pool Value ($)")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Debug: Exception caught.")  # Debug point
