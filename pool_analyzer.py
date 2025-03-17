import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import csv

# Pool Profit and Risk Analyzer
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float, initial_investment: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    
    # Calculate initial and current amounts
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    # HODL value
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    print(f"Debug - calculate_il: value_if_held={value_if_held}")
    
    # Pool value
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    print(f"Debug - calculate_il: pool_value={pool_value}")
    
    # Impermanent Loss
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    print(f"Debug - calculate_il: initial_price_asset1={initial_price_asset1}, initial_price_asset2={initial_price_asset2}, current_price_asset1={current_price_asset1}, current_price_asset2={current_price_asset2}, initial_investment={initial_investment}, il_percentage={il_percentage}")
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

    print(f"Debug - calculate_future_value: months={months}, initial_pool_value={pool_value}")

    # Start with the current pool value (adjusted for IL) at 0 months
    if months == 0:
        return round(pool_value, 2), calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)

    # Apply APY compounding on the initial pool value
    apy_compounded_value = pool_value * (1 + monthly_apy) ** months
    print(f"Debug - calculate_future_value: apy_compounded_value={apy_compounded_value}")

    # Apply price changes incrementally
    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    print(f"Debug - calculate_future_value: final_price_asset1={final_price_asset1}, final_price_asset2={final_price_asset2}")

    # Recalculate pool value with new prices
    new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                           final_price_asset1, final_price_asset2)
    print(f"Debug - calculate_future_value: new_pool_value={new_pool_value}")

    future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
    current_value = apy_compounded_value + (new_pool_value - pool_value)  # Add price impact to compounded APY
    print(f"Debug - calculate_future_value: current_value={current_value}, future_il={future_il}")

    return round(current_value, 2), future_il

def calculate_break_even_months(apy: float, il: float) -> float:
    if apy <= 0:
        return float('inf')
    
    monthly_apy = (apy / 100) / 12
    il_decimal = il / 100
    
    if il_decimal <= 0.01:  # Adjusted threshold to 0.01% for practical breakeven
        return 0
    
    months = 0
    value = 1.0
    target = 1 / (1 - il_decimal)
    print(f"Debug - calculate_break_even_months: il={il}, target={target}")
    
    while value < target and months < 1000:
        value *= (1 + monthly_apy)
        months += 1
    
    return round(months, 2) if months < 1000 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment: float, apy: float, pool_value: float,
                                                  initial_price_asset1: float, initial_price_asset2: float,
                                                  current_price_asset1: float, current_price_asset2: float,
                                                  expected_price_change_asset1: float, expected_price_change_asset2: float,
                                                  is_new_pool: bool = False) -> float:
    if apy <= 0:
        return float('inf')

    monthly_apy = (apy / 100) / 12
    months = 0

    if is_new_pool:
        initial_adjusted_price_asset1 = current_price_asset1 * (1 + (expected_price_change_asset1 / 100))
        initial_adjusted_price_asset2 = current_price_asset2 * (1 + (expected_price_change_asset2 / 100))
        initial_pool_value, _ = calculate_pool_value(initial_investment, current_price_asset1, current_price_asset2,
                                                    initial_adjusted_price_asset1, initial_adjusted_price_asset2)
    else:
        initial_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2)

    loss_to_recover = initial_investment - initial_pool_value
    current_value = initial_pool_value
    print(f"Debug - calculate_break_even_months_with_price_changes: initial_pool_value={initial_pool_value}, loss_to_recover={loss_to_recover}")
    
    while current_value < initial_investment and months < 1000:
        months += 1
        current_value, _ = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                                                 current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                 expected_price_change_asset2, is_new_pool)
        print(f"Debug - calculate_break_even_months_with_price_changes: months={months}, current_value={current_value}")
    
    return round(months, 2) if months < 1000 else float('inf')

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_decline = (initial_tvl - current_tvl) / initial_tvl * 100
    return round(tvl_decline, 2)

def calculate_volatility_score(expected_price_change_asset1: float, expected_price_change_asset2: float, btc_growth_rate: float) -> tuple[float, str]:
    divergence = abs(expected_price_change_asset1 - expected_price_change_asset2)
    asset_volatility = max(abs(expected_price_change_asset1), abs(expected_price_change_asset2))
    
    def get_score(value):
        if value <= 5:
            return 0  # Low
        elif value <= 15:
            return 33  # Moderate
        elif value <= 30:
            return 66  # High
        else:
            return 100  # Critical
    
    divergence_score = get_score(divergence)
    asset_score = get_score(asset_volatility)
    btc_score = get_score(abs(btc_growth_rate))
    
    volatility_score = (0.5 * divergence_score) + (0.2 * asset_score) + (0.3 * btc_score)
    final_score = min(volatility_score, max(divergence_score, asset_score, btc_score))
    
    if final_score <= 25:
        category = "Low"
        message = f"✅ Volatility Score: Low ({final_score:.0f}%). Price movements are unlikely to significantly impact IL or breakeven timing."
    elif final_score <= 50:
        category = "Moderate"
        message = f"⚠️ Volatility Score: Moderate ({final_score:.0f}%). Price volatility may increase IL and delay breakeven."
    elif final_score <= 75:
        category = "High"
        message = f"⚠️ Volatility Score: High ({final_score:.0f}%). Significant volatility risks could amplify IL and extend breakeven."
    else:
        category = "Critical"
        message = f"⚠️ Volatility Score: Critical ({final_score:.0f}%). Extreme volatility risks may lead to substantial IL and potentially unachievable breakeven."
    
    return final_score, message

def calculate_protocol_risk_score(apy: float, tvl_decline: float, current_tvl: float, trust_score: int) -> tuple[float, str]:
    # Base risk score based on APY, TVL decline, and pool size
    base_score = 0
    
    # APY contribution
    if apy < 10:
        base_score += 40
    elif apy <= 15:
        base_score += 20
    
    # TVL decline contribution
    if tvl_decline > 50:
        base_score += 40
    elif tvl_decline > 30:
        base_score += 30
    elif tvl_decline > 15:
        base_score += 15
    
    # Pool size contribution
    if current_tvl < 50000:
        base_score += 40
    elif current_tvl <= 200000:
        base_score += 20
    
    # Cap base score at 100
    base_score = min(base_score, 100)
    
    # Adjust base score with Trust Score multiplier
    if trust_score == 1:  # Unknown
        adjusted_score = base_score * 1.5
    elif trust_score == 2:  # Poor
        adjusted_score = base_score * 1.25
    elif trust_score == 3:  # Moderate
        adjusted_score = base_score * 1.0
    elif trust_score == 4:  # Good
        adjusted_score = base_score * 0.75
    else:  # Excellent (5)
        adjusted_score = base_score * 0.5
    
    # Cap adjusted score at 100
    adjusted_score = min(adjusted_score, 100)
    
    # Determine risk category and message
    if adjusted_score <= 25 or trust_score == 5:
        category = "Low"
        message = f"✅ Protocol Risk: Low ({adjusted_score:.0f}%). Minimal risk of protocol failure due to high yield, stable TVL, large pool size, or excellent trust score."
    elif adjusted_score <= 50 or (current_tvl <= 200000 and trust_score >= 3):
        category = "Advisory"
        message = f"⚠️ Protocol Risk: Advisory ({adjusted_score:.0f}%). Potential protocol risk due to small pool size, moderate yield/TVL decline, or unknown trust score."
    elif adjusted_score <= 75 or (apy < 10 and trust_score <= 3):
        category = "High"
        message = f"⚠️ Protocol Risk: High ({adjusted_score:.0f}%). Elevated risk of protocol failure due to low yield, significant TVL decline, small pool size, or low trust score."
    else:
        category = "Critical"
        message = f"⚠️ Protocol Risk: Critical ({adjusted_score:.0f}%). High risk of protocol failure due to very low yield, major TVL decline, tiny pool size, and unknown/poor trust score."
    
    return adjusted_score, message

def check_exit_conditions(initial_investment: float, apy: float, il: float, tvl_decline: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl: float, risk_free_rate: float, trust_score: int, months: int = 12, 
                         expected_price_change_asset1: float = 0.0, expected_price_change_asset2: float = 0.0, 
                         is_new_pool: bool = False, btc_growth_rate: float = 0.0):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    
    future_value, future_il = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                    expected_price_change_asset2, is_new_pool)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    future_pool_value_no_apy, _ = calculate_future_value(initial_investment, 0.0, months, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    
    total_loss_percentage = ((initial_investment - future_pool_value_no_apy) / initial_investment) * 100 if initial_investment > 0 else 0
    apy_exit_threshold = max(0, total_loss_percentage * 12 / months if months > 0 else 0)
    
    # Calculate Volatility Score to adjust APY Exit Threshold
    volatility_score, _ = calculate_volatility_score(expected_price_change_asset1, expected_price_change_asset2, btc_growth_rate)
    apy_exit_threshold = max(apy_exit_threshold, risk_free_rate)
    if volatility_score > 75 or il > 50 or future_il > 50:
        apy_exit_threshold = max(apy_exit_threshold, risk_free_rate + 5.0)
    
    break_even_months = calculate_break_even_months(apy, il)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    st.subheader("Results:")
    if initial_tvl <= 0:
        if is_new_pool:
            st.write(f"**Initial Impermanent Loss:** 0.00% (new pool, IL starts at 0)")
            st.write(f"**Projected Impermanent Loss (after {months} months):** {future_il:.2f}% (based on expected price changes)")
        else:
            st.write(f"**Impermanent Loss (at current time):** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (based on your risk-free rate; increased by 5% under high volatility or IL conditions)")
        st.write(f"**TVL Decline:** Cannot calculate without a valid Initial TVL. Set Initial TVL to Current TVL for new pool entry.")
    else:
        if is_new_pool:
            st.write(f"**Initial Impermanent Loss:** 0.00% (new pool, IL starts at 0)")
            st.write(f"**Projected Impermanent Loss (after {months} months):** {future_il:.2f}% (based on expected price changes)")
        else:
            st.write(f"**Impermanent Loss (at current time):** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (based on your risk-free rate; increased by 5% under high volatility or IL conditions)")
        st.write(f"**TVL Decline:** {tvl_decline:.2f}%")
    
    st.write(f"**Pool Share:** {pool_share:.2f}%")
    if pool_share < 5:
        st.success(f"✅ Pool Share Risk: Low ({pool_share:.2f}%). Minimal impact expected on pool prices due to small share.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ Pool Share Risk: Moderate ({pool_share:.2f}%). Potential for price impact due to moderate pool share.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ Pool Share Risk: High ({pool_share:.2f}%). Significant price impact possible due to high pool share.")
    else:
        st.error(f"⚠️ Pool Share Risk: Critical ({pool_share:.2f}%). High risk of severe price impact due to very large pool share.")

    if initial_tvl > 0:
        if tvl_decline >= 50:
            st.error(f"⚠️ TVL Decline Risk: Critical ({tvl_decline:.2f}% decline). High risk of significant loss due to substantial TVL reduction.")
        elif tvl_decline >= 30:
            st.warning(f"⚠️ TVL Decline Risk: High ({tvl_decline:.2f}% decline). Elevated risk due to significant TVL reduction.")
        elif tvl_decline >= 15:
            st.warning(f"⚠️ TVL Decline Risk: Moderate ({tvl_decline:.2f}% decline). Potential risk due to moderate TVL reduction.")
        else:
            st.success(f"✅ TVL Decline Risk: Low ({tvl_decline:.2f}% decline). Pool health appears stable with minimal TVL reduction.")
    
    # Protocol Risk Alert
    protocol_risk_score, protocol_risk_message = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)
    if "Critical" in protocol_risk_message:
        st.error(protocol_risk_message)
    elif "High" in protocol_risk_message or "Advisory" in protocol_risk_message:
        st.warning(protocol_risk_message)
    else:
        st.success(protocol_risk_message)

    if initial_tvl > 0:
        # Investment Risk Logic: Factor in TVL Decline and Protocol Risk
        if net_return < 1.0 or tvl_decline >= 50 or protocol_risk_score >= 75:
            st.error(f"⚠️ Investment Risk: Critical. Net Return {net_return:.2f}x, TVL Decline {tvl_decline:.2f}%, Protocol Risk {protocol_risk_score:.0f}% indicate severe risks.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score
        elif apy < apy_exit_threshold or net_return < 1.1:
            st.warning(f"⚠️ Investment Risk: Moderate. APY below threshold ({apy_exit_threshold:.2f}%) or marginal profit (Net Return {net_return:.2f}x) indicates potential underperformance.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score
        else:
            st.success(f"✅ Investment Risk: Low. Net Return {net_return:.2f}x indicates profitability.")
            return break_even_months, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score
    else:
        if net_return < 1.0:
            st.error(f"⚠️ Investment Risk: Critical. Net Return {net_return:.2f}x indicates a loss.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score
        elif apy < apy_exit_threshold or net_return < 1.1:
            st.warning(f"⚠️ Investment Risk: Moderate. APY below threshold ({apy_exit_threshold:.2f}%) or marginal profit (Net Return {net_return:.2f}x) indicates potential underperformance.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score
        else:
            st.success(f"✅ Investment Risk: Low. Net Return {net_return:.2f}x indicates profitability.")
            return break_even_months, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score

# Streamlit App
st.title("DM Pool Profit and Risk Analyzer")

# Add the summary at the top
st.markdown("""
Welcome to the DM Pool Profit and Risk Analyzer! This tool helps you evaluate the profitability and risks of liquidity pools in DeFi. By inputting your pool parameters, you can assess impermanent loss, net returns, and potential drawdowns, empowering you to make informed investment decisions. **Disclaimer:** This tool is for informational purposes only and does not constitute financial advice. Projections are estimates based on the inputs provided and are not guaranteed to reflect actual future outcomes.
""")

# Add custom CSS to improve dropdown readability
st.markdown("""
<style>
/* Style the select dropdown in the sidebar */
div[data-testid="stSidebar"] select {
    background-color: #1a1a1a;  /* Dark background for the dropdown */
    color: #ffffff;  /* Bright white text for the selected option */
}

/* Style the dropdown options */
div[data-testid="stSidebar"] select option {
    background-color: #1a1a1a;  /* Dark background for options */
    color: #ffffff;  /* Bright white text for options */
}

/* Style the selected option */
div[data-testid="stSidebar"] select option:checked {
    background-color: #333333;  /* Slightly lighter background for selected option */
    color: #ffffff;  /* Bright white text for selected option */
}

/* Add hover effect for options */
div[data-testid="stSidebar"] select option:hover {
    background-color: #444444;  /* Slightly lighter background on hover */
    color: #ffffff;  /* Bright white text on hover */
}
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Set Your Pool Parameters")

# Add dropdown for pool status
pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool"])
is_new_pool = (pool_status == "New Pool")

# Conditionally display price inputs based on pool status
if is_new_pool:
    current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    initial_price_asset1 = current_price_asset1
    initial_price_asset2 = current_price_asset2
else:
    initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.01, step=0.01, value=100.00, format="%.2f")
    initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=5.00, format="%.2f")

# New: Protocol Trust Score Input
trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
st.sidebar.markdown("""
**Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
- 1 = Unknown (default, highest caution)
- 2 = Poor (known but with concerns)
- 3 = Moderate (neutral, some audits)
- 4 = Good (trusted, audited)
- 5 = Excellent (top-tier, e.g., Uniswap, Aave)
""")

investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=169.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL (set to current TVL if entering today) ($)", 
                                     min_value=0.01, step=0.01, value=855000.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=755000.00, format="%.2f")

# New inputs for expected price changes
expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=100.0, format="%.2f")
expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")

# BTC-related inputs with clarified labels
initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                           min_value=0.0, step=0.01, value=100.00, format="%.2f")
current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=0.0, step=0.1, value=100.0, format="%.2f")

# Add user-adjusted risk-free rate
risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
st.sidebar.markdown("""
**Note:** The Risk-Free Rate represents the APY you could earn in a low-risk stablecoin pool (e.g., 5-15% depending on market conditions). The APY Exit Threshold uses this as a baseline, increasing by 5% under high volatility (>75% Volatility Score) or IL (>50%) conditions, ensuring a margin of safety.
""")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
        break_even_months, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score = check_exit_conditions(
            investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, btc_growth_rate
        )
        
        # Projected Pool Value
        st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
        st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${investment_amount:,.2f}).")
        time_periods = [0, 3, 6, 12]
        future_values = []
        future_ils = []
        for months in time_periods:
            value, il_at_time = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                      current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                      expected_price_change_asset2, is_new_pool)
            future_values.append(value)
            future_ils.append(il_at_time)
        
        formatted_pool_values = [f"{int(value):,}" for value in future_values]
        formatted_ils = [f"{il:.2f}%" for il in future_ils]
        df_projection = pd.DataFrame({
            "Time Period (Months)": time_periods,
            "Projected Value ($)": formatted_pool_values,
            "Projected Impermanent Loss (%)": formatted_ils
        })
        styled_df = df_projection.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Projected Value ($)", "Projected Impermanent Loss (%)"]).set_properties(**{
            'text-align': 'right'
        }, subset=["Time Period (Months)"])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        
        # Visualization: Plot Projected Pool Value
        plt.figure(figsize=(10, 5))
        plt.plot(time_periods, future_values, marker='o', label="Pool Value")
        plt.axhline(y=investment_amount, color='r', linestyle='--', label="Initial Investment")
        plt.title("Projected Pool Value Over Time")
        plt.xlabel("Months")
        plt.ylabel("Value ($)")
        plt.legend()
        st.pyplot(plt)

        # Pool vs. BTC Comparison (12 Months Compounding)
        st.subheader("Pool vs. BTC Comparison | 12 Months | Compounding on Pool Assets Only")
        asset1_change_desc = "appreciation" if expected_price_change_asset1 >= 0 else "depreciation"
        asset2_change_desc = "appreciation" if expected_price_change_asset2 >= 0 else "depreciation"
        asset1_change_text = f"{abs(expected_price_change_asset1):.1f}% {asset1_change_desc}" if expected_price_change_asset1 != 0 else "no change"
        asset2_change_text = f"{abs(expected_price_change_asset2):.1f}% {asset2_change_desc}" if expected_price_change_asset2 != 0 else "no change"
        st.write(f"**Note:** Pool Value is based on an expected {asset1_change_text} for Asset 1, {asset2_change_text} for Asset 2, and a compounded APY of {apy:.1f}% over 12 months. This comparison assumes a {btc_growth_rate:.1f}% annual growth rate for BTC and no additional fees or slippage.")
        
        projected_btc_price = initial_btc_price * (1 + btc_growth_rate / 100) if initial_btc_price > 0 else current_btc_price * (1 + btc_growth_rate / 100)
        
        if initial_btc_price == 0.0 or initial_btc_price == current_btc_price:
            initial_btc_amount = investment_amount / current_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        else:
            initial_btc_amount = investment_amount / initial_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        
        pool_value_12_months = future_values[-1]
        difference = pool_value_12_months - btc_value_12_months
        pool_return_pct = (pool_value_12_months / investment_amount - 1) * 100
        btc_return_pct = (btc_value_12_months / investment_amount - 1) * 100
        
        formatted_pool_value_12 = f"{int(pool_value_12_months):,}"
        formatted_btc_value_12 = f"{int(btc_value_12_months):,}"
        formatted_difference = f"{int(difference):,}" if difference >= 0 else f"({int(abs(difference)):,})"
        formatted_pool_return = f"{pool_return_pct:.2f}%"
        formatted_btc_return = f"{btc_return_pct:.2f}%"
        
        df_btc_comparison = pd.DataFrame({
            "Metric": ["Projected Pool Value", "Value if Invested in BTC Only", "Difference (Pool - BTC)", "Pool Return (%)", "BTC Return (%)"],
            "Value": [formatted_pool_value_12, formatted_btc_value_12, formatted_difference, formatted_pool_return, formatted_btc_return]
        })
        styled_df_btc = df_btc_comparison.style.set_properties(**{
            'text-align': 'right'
        }).apply(lambda x: ['color: red' if x.name == 'Value' and x[1].startswith('(') else '' for i in x], axis=1)
        st.dataframe(styled_df_btc, hide_index=True, use_container_width=True)
        
        # Maximum Drawdown Risk Scenarios
        st.subheader("Maximum Drawdown Risk Scenarios")
        mdd_scenarios = [10, 30, 65, 100]
        btc_mdd_scenarios = [10, 30, 65, 90]

        # MDD from Initial Investment
        st.subheader("MDD from Initial Investment")
        st.write("**Note:** Simulated maximum drawdowns based on initial investment. Pool MDD assumes IL and TVL decline (e.g., 50% IL + 50% TVL decline for 100% loss). BTC MDD assumes price drops up to 90% (historical worst case).")
        pool_mdd_values_initial = [investment_amount * (1 - mdd / 100) for mdd in mdd_scenarios]
        initial_btc_amount = investment_amount / (initial_btc_price if initial_btc_price > 0 else current_btc_price)
        btc_mdd_values_initial = [initial_btc_amount * (current_btc_price * (1 - mdd / 100)) for mdd in btc_mdd_scenarios]

        formatted_pool_mdd_initial = [f"{int(value):,}" for value in pool_mdd_values_initial]
        formatted_btc_mdd_initial = [f"{int(value):,}" for value in btc_mdd_values_initial]

        df_risk_scenarios_initial = pd.DataFrame({
            "Scenario": ["10% MDD", "30% MDD", "65% MDD", "90%/100% MDD"],
            "Pool Value ($)": formatted_pool_mdd_initial,
            "BTC Value ($)": formatted_btc_mdd_initial
        })
        styled_df_risk_initial = df_risk_scenarios_initial.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Pool Value ($)", "BTC Value ($)"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Scenario"])
        st.dataframe(styled_df_risk_initial, hide_index=True, use_container_width=True)

        # MDD from Projected Value After 12 Months
        st.subheader("MDD from Projected Value After 12 Months")
        st.write(f"**Note:** Simulated maximum drawdowns based on projected values after 12 months, including expected price changes (e.g., {expected_price_change_asset1}% appreciation of Asset 1, {expected_price_change_asset2}% change for Asset 2) and {apy}% APY for the pool, and {btc_growth_rate}% growth for BTC.")
        pool_mdd_values_projected = [future_values[-1] * (1 - mdd / 100) for mdd in mdd_scenarios]
        btc_mdd_values_projected = [btc_value_12_months * (1 - mdd / 100) for mdd in btc_mdd_scenarios]

        formatted_pool_mdd_projected = [f"{int(value):,}" for value in pool_mdd_values_projected]
        formatted_btc_mdd_projected = [f"{int(value):,}" for value in btc_mdd_values_projected]

        df_risk_scenarios_projected = pd.DataFrame({
            "Scenario": ["10% MDD", "30% MDD", "65% MDD", "90%/100% MDD"],
            "Pool Value ($)": formatted_pool_mdd_projected,
            "BTC Value ($)": formatted_btc_mdd_projected
        })
        styled_df_risk_projected = df_risk_scenarios_projected.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Pool Value ($)", "BTC Value ($)"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Scenario"])
        st.dataframe(styled_df_risk_projected, hide_index=True, use_container_width=True)

        # Breakeven Analysis
        st.subheader("Breakeven Analysis")
        df_breakeven = pd.DataFrame({
            "Metric": ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"],
            "Value": [break_even_months, break_even_months_with_price]
        })
        styled_df_breakeven = df_breakeven.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Value"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Metric"])
        st.dataframe(styled_df_breakeven, hide_index=True, use_container_width=True)
        st.write("**Note:** 'Months to Breakeven Against IL' reflects only the recovery of impermanent loss with APY, while 'Months to Breakeven Including Expected Price Changes' accounts for the initial pool value after IL and price changes. The target is to recover the difference between your initial investment and this adjusted value, which may extend the breakeven period significantly if IL is high.")
        
        # Volatility Score
        volatility_score, volatility_message = calculate_volatility_score(expected_price_change_asset1, expected_price_change_asset2, btc_growth_rate)
        if "Critical" in volatility_message:
            st.error(volatility_message)
        elif "High" in volatility_message or "Moderate" in volatility_message:
            st.warning(volatility_message)
        else:
            st.success(volatility_message)
        
        # Export Results
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        if is_new_pool:
            writer.writerow(["Initial Impermanent Loss (%)", "0.00"])
            writer.writerow(["Projected Impermanent Loss (after 12 months) (%)", f"{future_il:.2f}"])
        else:
            writer.writerow(["Impermanent Loss (at current time) (%)", f"{il:.2f}"])
        writer.writerow(["Net Return (x)", f"{net_return:.2f}"])
        writer.writerow(["APY Exit Threshold (%)", f"{apy_exit_threshold:.2f}"])
        writer.writerow(["TVL Decline (%)", f"{tvl_decline:.2f}" if initial_tvl > 0 else "N/A"])
        writer.writerow(["Pool Share (%)", f"{pool_share:.2f}"])
        writer.writerow(["Months to Breakeven Against IL", f"{break_even_months}"])
        writer.writerow(["Months to Breakeven Including Expected Price Changes", f"{break_even_months_with_price}"])
        writer.writerow(["Volatility Score (%)", f"{volatility_score:.0f}"])
        writer.writerow(["Protocol Risk Score (%)", f"{protocol_risk_score:.0f}"])
        st.download_button(label="Export Results as CSV", data=output.getvalue(), file_name="pool_analysis_results.csv", mime="text/csv")
