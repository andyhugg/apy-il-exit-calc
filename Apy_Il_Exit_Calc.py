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
    
    sqrt_ratio = (price_ratio_current / price_ratio_initial) ** 0.5
    il = 2 * (sqrt_ratio / (1 + sqrt_ratio)) - 1
    
    return abs(il) * 100  # Convert to percentage

def calculate_future_value(initial_investment: float, apy: float, il: float, months: int) -> float:
    """
    Projects future value based on APY and IL over time.
    """
    monthly_return = (apy / 100) / 12
    loss_factor = 1 - (il / 100)
    return round(initial_investment * ((1 + monthly_return) ** months) * loss_factor, 2)

def check_exit_conditions(apy: float, il: float):
    """
    Determines if IL is overtaking APY and suggests exit conditions.
    """
    apy_decimal = apy / 100
    il_decimal = il / 100
    
    net_return = (1 + apy_decimal) - (1 - il_decimal)
    apy_exit_threshold = il * 12  # IL spread over 12 months
    
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    break_even_months = float('inf')  # Default value in case APY is above the threshold
    
    if apy < apy_exit_threshold:
        break_even_months = il / (apy / 12) if apy > 0 else float('inf')
        st.warning(f"APY is below the IL threshold! Consider exiting.")
        st.write(f"**Break-even Duration:** {break_even_months:.2f} months")
    else:
        st.success("You're still in profit. No need to exit yet.")
    
    return break_even_months

# Streamlit App UI
st.title("DM APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

# Manual Entry for Asset Prices
initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", value=0, step=1)
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", value=0, min_value=1, step=1)
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", value=0, step=1)
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", value=0, min_value=1, step=1)
apy = st.sidebar.number_input("Current APY (%)", value=340, step=1)
investment_amount = st.sidebar.number_input("Initial Investment ($)", value=10000, step=1)

if st.sidebar.button("Calculate"):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    break_even_months = check_exit_conditions(apy, il)
    
    # Generate Break-even Duration Table
    st.subheader("Break-even Duration for Different APY Levels")
    apy_values = [50, 75, 100, 150, 200]
    break_even_durations = [round(il / (apy_val / 12), 2) if apy_val > 0 else float('inf') for apy_val in apy_values]
    df = pd.DataFrame({"APY (%)": apy_values, "Break-even Duration (Months)": break_even_durations})
    st.table(df)
    
    # Generate Future Profit Projection Table
    st.subheader("Projected Liquidity Pool Value | Considers yield and IL only not asset appreciation")
    time_periods = [3, 6, 12]  # Months
    future_values = [calculate_future_value(investment_amount, apy, il, months) for months in time_periods]
    
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
    
    st.markdown("""
    ### How Risk Levels Are Determined:
    - **High Risk:** IL is greater than **75% of APY** (`il > apy * 0.75`).
      - Your profits are at serious risk, and you may face a **net loss**.
      - Consider exiting or diversifying.
    - **Moderate Risk:** IL is between **50% and 75% of APY** (`il > apy * 0.5`).
      - IL is eating into a significant portion of profits but may still be viable.
      - Monitor closely to ensure it doesn’t escalate.
    - **Low Risk:** IL is **≤ 50% of APY** (default case).
      - IL is manageable, and **your yield remains profitable**.
    
    **Example Scenarios:**
    | **APY (%)** | **IL (%)** | **Risk Level** | **Explanation** |
    |------------|------------|-------------|----------------|
    | 200%  | 160%  | **High**  | IL is 80% of APY, meaning most of your profits are eroded. |
    | 100%  | 60%   | **Moderate** | IL is 60% of APY, a significant impact but not disastrous. |
    | 150%  | 30%   | **Low**  | IL is only 20% of APY, leaving plenty of yield. |
    """)
