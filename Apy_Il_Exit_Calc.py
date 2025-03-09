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
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(initial_investment: float, apy: float, il: float, months: int) -> float:
    if months <= 0:
        return initial_investment
    
    monthly_yield = (apy / 100) / 12
    value_after_apy = initial_investment * (1 + monthly_yield) ** months
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
    target = 1 / (1 - il_decimal)
    
    while value < target and months < 1000:
        value *= (1 + monthly_apy)
        months += 1
    
    return round(months, 2) if months < 1000 else float('inf')

def check_exit_conditions(initial_investment: float, apy: float, il: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, months: int = 12):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2)
    future_value = calculate_future_value(pool_value, apy, il, months)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    apy_exit_threshold = (il * 12) / months
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    if apy < apy_exit_threshold:
        st.warning("⚠️ APY is below the IL threshold! Immediate exit recommended.")
        return 0, net_return
    
    break_even_months = calculate_break_even_months(apy, il)
    st.success("You're still in profit. No need to exit yet.")
    
    # Exit Strategy Recommendations
    st.subheader("Exit Strategy Recommendations")
    if il > apy * 0.75:
        st.warning("⚠️ IL is approaching APY! Monitor closely and consider exiting if IL exceeds APY within the next 3-6 months.")
    elif net_return < 1:
        st.warning("⚠️ Net return is negative! Exit immediately to minimize losses.")
    else:
        st.success("✅ Low risk. Hold for at least 6-12 months to maximize yields, or rebalance if market conditions change.")
    
    return break_even_months, net_return

# Streamlit App
st.title("DM APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, step=0.01, value=80000.00, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, step=0.01, value=99000.00, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=10000.00, format="%.2f")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        break_even_months, net_return = check_exit_conditions(investment_amount, apy, il,
                                                            initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        
        # Projected Pool Value
        st.subheader("Projected Pool Value | Based on Yield and Impermanent Loss")
        time_periods = [0, 3, 6, 12]
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2,
                                                   current_price_asset1, current_price_asset2)
        future_values = [calculate_future_value(pool_value, apy, il_impact, months) for months in time_periods]
        formatted_values = [f"{int(value):,}" for value in future_values]
        df_projection = pd.DataFrame({
            "Time Period (Months)": time_periods,
            "Projected Value ($)": formatted_values
        })
        styled_df = df_projection.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Projected Value ($)"]).set_properties(**{
            'text-align': 'right'
        }, subset=["Time Period (Months)"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Breakeven Analysis
        st.subheader("Breakeven Analysis")
        df_breakeven = pd.DataFrame({
            "Metric": ["Months to Breakeven"],
            "Value": [break_even_months]
        })
        st.table(df_breakeven)
