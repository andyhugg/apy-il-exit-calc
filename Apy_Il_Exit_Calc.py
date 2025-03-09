import streamlit as st
import numpy as np
import pandas as pd

# APY vs IL Exit Calculator
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0:
        return 0
    
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2
    
    if price_ratio_initial == 0:
        return 0
    
    k = price_ratio_current / price_ratio_initial
    sqrt_k = np.sqrt(k) if k > 0 else 0
    if (1 + k) == 0:
        return 0
    
    il = 2 * (sqrt_k / (1 + k)) - 1
    il_percentage = abs(il) * 100
    return il_percentage

def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                        current_price_asset1: float, current_price_asset2: float) -> float:
    # Assume initial investment is split equally between two assets
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    # Current value if held outside pool (no IL)
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    
    # Current value in pool (affected by IL)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    # Impermanent loss as a percentage of the difference
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(initial_investment: float, apy: float, il: float, months: int) -> float:
    if months <= 0:
        return initial_investment
    
    # Apply APY with monthly compounding
    monthly_yield = (apy / 100) / 12
    value_after_apy = initial_investment * (1 + monthly_yield) ** months
    
    # Adjust for IL (assume IL is a one-time effect at the current price ratio)
    loss_factor = 1 - (il / 100)
    final_value = value_after_apy * loss_factor
    return round(final_value, 2)

def calculate_break_even_months(apy: float, il: float) -> float:
    if apy <= 0:
        return float('inf')
    
    monthly_apy = (apy / 100) / 12
    il_decimal = il / 100
    
    if il_decimal == 0:
        return 0
    
    months = 0
    value = 1.0
    target = 1 / (1 - il_decimal)  # Breakeven when APY compensates for IL
    
    while value < target and months < 1000:
        value *= (1 + monthly_apy)
        months += 1
    
    return round(months, 2) if months < 1000 else float('inf')

def check_exit_conditions(initial_investment: float, apy: float, il: float, initial_price_asset1, initial_price_asset2,
                         current_price_asset1, current_price_asset2, months: int = 12):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2)
    future_value = calculate_future_value(pool_value, apy, il, months)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    # APY exit threshold should be based on IL annualized impact
    apy_exit_threshold = (il * 12) / months  # Annualized IL effect
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    if apy < apy_exit_threshold:
        st.warning("⚠️ APY is below the IL threshold! Immediate exit recommended.")
        return 0, net_return
    
    break_even_months = calculate_break_even_months(apy, il)
    st.success("You're still in profit. No need to exit yet.")
    
    return break_even_months, net_return

st.title("DM APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, step=0.01, value=80000.00, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, step=0.01, value=99000.00, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=10000.00, format="%.2f")

if st.sidebar.button("Calculate"):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    break_even_months, net_return = check_exit_conditions(investment_amount, apy, il, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2)
    
    st.subheader("Projected Pool Value | Based on Yield and Impermanent Loss")
    time_periods = [0, 3, 6, 12]
    pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2,
                                               current_price_asset1, current_price_asset2)
    future_values = [calculate_future_value(pool_value, apy, il_impact, months) for months in time_periods]
    df_projection = pd.DataFrame({"Time Period (Months)": time_periods, "Projected Value ($)": future_values})
    st.table(df_projection)
    
    st.subheader("Risk Analysis")
    risk_level = "Low"
    if il > apy * 0.75:
        risk_level = "High"
    elif il > apy * 0.5:
        risk_level = "Moderate"
    
    st.write(f"**Risk Level:** {risk_level}")
    if risk_level == "High":
        st.warning("⚠️ High Risk: IL is significantly reducing your yield. Consider exiting or diversifying.")
    elif risk_level == "Moderate":
        st.warning("⚠️ Moderate Risk: Monitor the pool closely to ensure IL does not surpass APY.")
    else:
        st.success("✅ Low Risk: IL is manageable, and your yield remains profitable.")
    
    st.subheader("Breakeven Analysis")
    df_breakeven = pd.DataFrame({
        "Metric": ["Months to Breakeven"],
        "Value": [break_even_months]
    })
    st.table(df_breakeven)
