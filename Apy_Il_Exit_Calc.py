import streamlit as st
import numpy as np
import pandas as pd

# APY vs IL Exit Calculator
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float) -> float:
    """
    Calculates Impermanent Loss (IL) percentage based on initial and current asset prices.
    IL is the loss compared to holding the assets, assuming a 50/50 initial pool.
    """
    if initial_price_asset2 == 0 or current_price_asset2 == 0:
        return 0  # Avoid division by zero

    # Price ratios
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2

    if price_ratio_initial == 0:
        return 0  # Avoid division by zero

    # Price change factor (k)
    k = price_ratio_current / price_ratio_initial

    # IL formula for a 50/50 liquidity pool: (2 * sqrt(k) / (1 + k)) - 1
    sqrt_k = np.sqrt(k) if k > 0 else 0
    if (1 + k) == 0:
        return 0
    il = 2 * (sqrt_k / (1 + k)) - 1

    # Convert to percentage and ensure it's positive (IL is a loss, so take absolute value)
    il_percentage = abs(il) * 100

    return il_percentage


def calculate_future_value(initial_investment: float, apy: float, il: float, months: int) -> float:
    """
    Projects future value based on APY (compounded monthly) and applies IL at the end.
    Uses standard financial compounding: FV = PV * (1 + monthly_rate)^months.
    """
    if months <= 0:
        return initial_investment

    # Monthly yield from APY (standard monthly compounding)
    monthly_yield = (apy / 100) / 12  # Convert APY to monthly rate
    # Compound growth from APY
    value_after_apy = initial_investment * (1 + monthly_yield) ** months
    # Apply IL as a one-time loss (simplified assumption)
    loss_factor = 1 - (il / 100)
    final_value = value_after_apy * loss_factor

    return round(final_value, 2)


def calculate_break_even_months(apy: float, il: float) -> float:
    """
    Calculates the number of months required for APY to offset the IL.
    Uses logarithmic approximation with a minimum of 1 month for small IL values.
    """
    if apy <= 0:
        return float('inf')
    
    monthly_apy = (apy / 100) / 12  # Monthly APY rate as a decimal
    il_decimal = il / 100  # IL as a decimal
    
    if il_decimal == 0:
        return 0  # No IL to offset
    
    # Logarithmic approximation
    if monthly_apy > 0:
        months = max(1, int(np.ceil(np.log(1 + il_decimal) / np.log(1 + monthly_apy))))
    else:
        months = float('inf')
    
    return months


def check_exit_conditions(initial_investment: float, apy: float, il: float, months: int = 12):
    """
    Determines if IL is overtaking APY and suggests exit conditions.
    Uses the standard definition of net return (final value / initial investment).
    """
    # Calculate future value
    future_value = calculate_future_value(initial_investment, apy, il, months)
    # Net return = Final Value / Initial Investment
    net_return = future_value / initial_investment if initial_investment > 0 else 0

    # APY exit threshold: The minimum APY needed to offset IL over 12 months
    apy_exit_threshold = (il * 12) / months  # Annualized IL impact as a percentage

    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")

    break_even_months = calculate_break_even_months(apy, il)
    
    if apy < apy_exit_threshold:
        st.warning(f"APY is below the IL threshold! Consider exiting after {break_even_months:.2f} months.")
    else:
        st.success("You're still in profit. No need to exit yet.")

    return break_even_months, net_return


# Streamlit App UI
st.title("DM APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

# Manual Entry for Asset Prices and Investment
initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, value=88000.00, step=0.01, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, value=1.00, step=0.01, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, value=95000.00, step=0.01, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, value=1.00, step=0.01, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, value=1.00, step=0.01, format="%.2f", help="APY is variable and user-defined.")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, value=100.00, step=0.01, format="%.2f")

if st.sidebar.button("Calculate"):
    # Calculate Impermanent Loss based on price changes
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    
    # Check exit conditions and get net return
    break_even_months, net_return = check_exit_conditions(investment_amount, apy, il)
    
    # Generate Break-even Duration Table for different APY levels
    st.subheader("Break-even Duration for Different APY Levels")
    apy_values = [0, 50, 75, 100, 150, 200]
    break_even_durations = [calculate_break_even_months(apy_val, il) for apy_val in apy_values]
    df = pd.DataFrame({"APY (%)": apy_values, "Break-even Duration (Months)": break_even_durations})
    st.table(df)
    
    # Generate Projected Pool Value Table with updated description and formatting
    st.subheader("Projected Pool Value | Based on Yield (Your Earnings) and Impermanent Loss (Loss from Price Changes), Excluding Gains from Asset Price Rises")
    time_periods = [0, 3, 6, 12]  # Months
    future_values = [calculate_future_value(investment_amount, apy, il, months) for months in time_periods]
    df_projection = pd.DataFrame({
        "Time Period (Months)": time_periods,
        "Projected Value ($)": [f"${value:,.2f}" for value in future_values]  # Format with commas for clarity
    })
    st.table(df_projection)
    
    # Risk Analysis
    st.subheader("Risk Analysis")
    risk_level = "Low"
    # High risk if IL exceeds 75% of APY
    if il > (apy * 0.75):
        risk_level = "High"
    # Moderate risk if IL exceeds 50% of APY
    elif il > (apy * 0.5):
        risk_level = "Moderate"
    
    st.write(f"**Risk Level:** {risk_level}")
    
    if risk_level == "High":
        st.warning("⚠️ High Risk: IL is significantly reducing your yield. Consider exiting or diversifying.")
    elif risk_level == "Moderate":
        st.warning("⚠️ Moderate Risk: Monitor the pool closely to ensure IL does not surpass APY.")
    else:
        st.success("✅ Low Risk: IL is manageable, and your yield remains profitable.")
