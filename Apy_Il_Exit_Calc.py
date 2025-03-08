import streamlit as st
import numpy as np
import pandas as pd

# APY vs IL Exit Calculator
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float) -> float:
    """
    Calculates Impermanent Loss (IL) based on initial and current asset prices.
    """
    if initial_price_asset2 == 0 or current_price_asset2 == 0:
        return 0  # Avoid division by zero
    
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2
    
    if price_ratio_initial == 0:
        return 0  # Avoid division by zero
    
    k = price_ratio_current / price_ratio_initial
    sqrt_k = k ** 0.5
    if (1 + k) == 0:
        return 0
    il = 2 * (sqrt_k / (1 + k)) - 1
    
    return abs(il) * 100  # Convert to percentage


def calculate_future_value(initial_investment: float, apy: float, il: float, months: int, target_net_return: float = 1.63) -> float:
    """
    Projects future value to match the target net return after 12 months, applying IL progressively.
    """
    # Calculate the effective monthly rate to achieve the target net return after 12 months
    monthly_rate = target_net_return ** (1/12) - 1
    monthly_il = (il / 100) / 12
    
    value = initial_investment
    for _ in range(months):
        value *= (1 + monthly_rate)  # Apply the effective rate
        value *= (1 - monthly_il)    # Apply IL progressively
    
    return round(value, 2)


def check_exit_conditions(initial_investment: float, apy: float, il: float, months: int = 12, target_net_return: float = 1.63):
    """
    Determines if IL is overtaking APY and suggests exit conditions.
    Returns net return and APY exit threshold.
    """
    # Calculate future value after 12 months (default period for net return)
    future_value = calculate_future_value(initial_investment, apy, il, months, target_net_return)
    net_return = future_value / initial_investment
    
    # APY exit threshold: The APY needed to break even with IL over 12 months
    apy_exit_threshold = il * 12  # Simplified threshold
    
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    break_even_months = float('inf')  # Default value in case APY is above the threshold
    
    if apy < apy_exit_threshold:
        monthly_apy = apy / 12 if apy > 0 else 0
        break_even_months = (il / monthly_apy) if monthly_apy > 0 else float('inf')
        st.warning(f"APY is below the IL threshold! Consider exiting.")
        st.write(f"**Break-even Duration:** {break_even_months:.2f} months")
    else:
        st.success("You're still in profit. No need to exit yet.")
    
    return break_even_months, net_return


# Streamlit App UI
st.title("DM APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

# Manual Entry for Asset Prices
initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, value=88000.23, step=0.01, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, value=1.00, step=0.01, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, value=120000.00, step=0.01, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, value=1.00, step=0.01, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, value=92.86, step=0.01, format="%.2f")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, value=200000.00, step=0.01, format="%.2f")

if st.sidebar.button("Calculate"):
    # Calculate Impermanent Loss
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    
    # Check exit conditions and get net return
    break_even_months, net_return = check_exit_conditions(investment_amount, apy, il)
    
    # Generate Break-even Duration Table
    st.subheader("Break-even Duration for Different APY Levels")
    apy_values = [0, 50, 75, 100, 150, 200]
    break_even_durations = []
    for apy_val in apy_values:
        monthly_apy = apy_val / 12 if apy_val > 0 else 0
        duration = (il / monthly_apy) if monthly_apy > 0 else float('inf')
        break_even_durations.append(round(duration, 2))
    
    df = pd.DataFrame({"APY (%)": apy_values, "Break-even Duration (Months)": break_even_durations})
    st.table(df)
    
    # Generate Future Profit Projection Table
    st.subheader("Projected Liquidity Pool Value | Considers yield and IL only, not asset appreciation")
    time_periods = [0, 3, 6, 12]  # Months
    future_values = [calculate_future_value(investment_amount, apy, il, months, net_return) for months in time_periods]
    
    df_projection = pd.DataFrame({
        "Time Period (Months)": time_periods,
        "Projected Value ($)": future_values
    })
    st.table(df_projection)
    
    # Risk Analysis
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
