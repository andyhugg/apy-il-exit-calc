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
    # Use higher precision to avoid rounding to 0% for small IL
    il_percentage = round(abs(il) * 100, 2)  # Round to 2 decimal places
    return il_percentage if il_percentage > 0.01 else il_percentage  # Minimum threshold of 0.01%

def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                        current_price_asset1: float, current_price_asset2: float) -> float:
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(pool_value: float, apy: float, months: int) -> float:
    if months <= 0:
        return pool_value
    
    monthly_yield = (apy / 100) / 12
    value_after_apy = pool_value * (1 + monthly_yield) ** months
    return round(value_after_apy, 2)

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

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_decline = (initial_tvl - current_tvl) / initial_tvl * 100
    return round(tvl_decline, 2)

def check_exit_conditions(initial_investment: float, apy: float, il: float, tvl_decline: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, months: int = 12):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2)
    future_value = calculate_future_value(pool_value, apy, months)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    apy_exit_threshold = (il * 12) / months

    # Calculate break_even_months upfront so it's always available
    break_even_months = calculate_break_even_months(apy, il)

    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    st.write(f"**TVL Decline:** {tvl_decline:.2f}%")

    # First check if you're losing money (net return < 1.0x)
    if net_return < 1.0:
        st.warning("⚠️ Warning: You're losing money (Net Return < 1.0x). Consider exiting or monitoring closely.")
        return 0, net_return

    # Prioritize TVL decline as the next risk factor
    elif tvl_decline >= 50:
        st.warning("⚠️ Critical Risk: TVL has dropped over 50%! Exit immediately to avoid potential total loss.")
        return 0, net_return
    elif tvl_decline >= 30:
        st.warning("⚠️ High Risk: TVL has dropped 30%-50%! Reduce exposure or consider exiting.")
        return break_even_months, net_return
    elif tvl_decline >= 15:
        st.warning("⚠️ Moderate Risk: TVL has dropped 15%-30%! Monitor closely and consider partial withdrawal.")
        return break_even_months, net_return
    else:
        # Check APY and IL if TVL decline is low and you're not losing money
        if apy < apy_exit_threshold or net_return < 1.1:  # Added net return check for marginal profit
            st.warning("⚠️ APY is below the IL threshold or profit is marginal! Consider exiting or monitoring closely.")
            return 0, net_return
        else:
            st.success("✅ Low risk. You're still in profit. No need to exit yet.")
            return break_even_months, net_return

# Streamlit App
st.title("DM Liquidity Pool Profit & Risk Analyzer")

st.sidebar.header("Set Your Pool Parameters")

initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, step=0.01, value=80000.00, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, step=0.01, value=225.00, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, step=0.01, value=83000.00, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, step=0.01, value=215.00, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=40.00, format="%.2f")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=10000.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL ($)", min_value=0.0, step=1000.0, value=875000.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.0, step=1000.0, value=850000.00, format="%.2f")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
        break_even_months, net_return = check_exit_conditions(investment_amount, apy, il, tvl_decline,
                                                            initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        
        # Projected Pool Value
        st.subheader("Projected Pool Value Based on Yield and Impermanent Loss")
        time_periods = [0, 3, 6, 12]
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2,
                                                   current_price_asset1, current_price_asset2)
        future_values = [calculate_future_value(pool_value, apy, months) for months in time_periods]
        formatted_pool_values = [f"{int(value):,}" for value in future_values]
        df_projection = pd.DataFrame({
            "Time Period (Months)": time_periods,
            "Projected Value ($)": formatted_pool_values
        })
        styled_df = df_projection.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Projected Value ($)"]).set_properties(**{
            'text-align': 'right'
        }, subset=["Time Period (Months)"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Hold vs. Pool Comparison
        st.subheader("Hold vs. Pool Comparison")
        # Calculate hold values
        initial_amount_asset1 = (investment_amount / 2) / initial_price_asset1
        initial_amount_asset2 = (investment_amount / 2) / initial_price_asset2
        value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
        
        initial_amount_asset1_only = investment_amount / initial_price_asset1
        value_if_held_asset1_only = initial_amount_asset1_only * current_price_asset1
        
        # Project hold values (no APY, static prices)
        hold_values = [value_if_held] * len(time_periods)
        hold_values_asset1_only = [value_if_held_asset1_only] * len(time_periods)
        
        # Calculate differences
        diff_values = [future_value - hold_value for future_value, hold_value in zip(future_values, hold_values)]
        diff_values_asset1_only = [future_value - hold_value for future_value, hold_value in zip(future_values, hold_values_asset1_only)]
        
        # Format values for display
        formatted_hold_values = [f"{int(value):,}" for value in hold_values]
        formatted_hold_values_asset1_only = [f"{int(value):,}" for value in hold_values_asset1_only]
        formatted_diff_values = [f"{int(diff):,}" if diff >= 0 else f"({int(abs(diff)):,})" for diff in diff_values]
        formatted_diff_values_asset1_only = [f"{int(diff):,}" if diff >= 0 else f"({int(abs(diff)):,})" for diff in diff_values_asset1_only]
        
        df_comparison = pd.DataFrame({
            "Time Period (Months)": time_periods,
            "Projected Pool Value ($)": formatted_pool_values,
            "Value if Held (Asset Pair) ($)": formatted_hold_values,
            "Value if Held (Asset 1 Only) ($)": formatted_hold_values_asset1_only,
            "Difference (Pool - Asset Pair) ($)": formatted_diff_values,
            "Difference (Pool - Asset 1 Only) ($)": formatted_diff_values_asset1_only
        })
        styled_df_comparison = df_comparison.style.set_properties(**{
            'text-align': 'right'
        }).apply(lambda x: ['color: red' if x.name == 'Difference (Pool - Asset Pair) ($)' and x[4].startswith('(') else '' for i in x],
                 axis=1).apply(lambda x: ['color: red' if x.name == 'Difference (Pool - Asset 1 Only) ($)' and x[5].startswith('(') else '' for i in x],
                 axis=1)
        st.dataframe(styled_df_comparison, use_container_width=True)
        
        # Breakeven Analysis
        st.subheader("Breakeven Analysis")
        df_breakeven = pd.DataFrame({
            "Metric": ["Months to Breakeven"],
            "Value": [break_even_months]
        })
        st.table(df_breakeven)
