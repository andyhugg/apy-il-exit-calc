import streamlit as st
import numpy as np
import pandas as pd

# Pool Profit and Risk Analyzer
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
    il_percentage = round(abs(il) * 100, 2)
    return il_percentage if il_percentage > 0.01 else il_percentage

def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                        current_price_asset1: float, current_price_asset2: float) -> float:
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(pool_value: float, apy: float, months: int, initial_price_asset1: float, initial_price_asset2: float,
                          current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                          expected_price_change_asset2: float, initial_investment: float) -> float:
    if months <= 0:
        return pool_value
    
    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    
    current_value = pool_value
    for month in range(months):
        # Update prices based on expected monthly changes
        new_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * (month + 1))
        new_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * (month + 1))
        
        # Recalculate pool value based on new prices
        new_pool_value = initial_investment * np.sqrt(new_price_asset1 * new_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
        # Apply APY to the current value (approximate yield on adjusted value)
        current_value = new_pool_value * (1 + monthly_apy)
    
    return round(current_value, 2)

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
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl: float, months: int = 12, expected_price_change_asset1: float = 0.0,
                         expected_price_change_asset2: float = 0.0):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2)
    
    # Calculate future pool value with depreciation and APY
    future_value = calculate_future_value(pool_value, apy, months, initial_price_asset1, initial_price_asset2,
                                         current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                         expected_price_change_asset2, initial_investment)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    # Calculate future pool value with depreciation (no APY) for APY Exit Threshold
    future_pool_value_no_apy = calculate_future_value(pool_value, 0.0, months, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                    expected_price_change_asset2, initial_investment)
    
    # Calculate total loss percentage (depreciation + IL impact)
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    future_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    future_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    future_value_if_held = (initial_amount_asset1 * future_price_asset1) + (initial_amount_asset2 * future_price_asset2)
    
    # Depreciation loss for each asset
    asset1_depreciation_loss = ((initial_investment / 2) - (initial_amount_asset1 * future_price_asset1)) / (initial_investment / 2) * 100 if (initial_investment / 2) > 0 else 0
    asset2_depreciation_loss = ((initial_investment / 2) - (initial_amount_asset2 * future_price_asset2)) / (initial_investment / 2) * 100 if (initial_investment / 2) > 0 else 0
    # Weighted average depreciation loss
    depreciation_loss = (asset1_depreciation_loss + asset2_depreciation_loss) / 2
    # Total loss includes initial IL and depreciation
    total_loss_percentage = depreciation_loss + il if depreciation_loss > 0 else il
    apy_exit_threshold = total_loss_percentage * 12 / months if months > 0 else 0
    
    break_even_months = calculate_break_even_months(apy, il)
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    st.subheader("Results:")
    if initial_tvl <= 0:
        st.write(f"**Impermanent Loss:** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
        st.write(f"**TVL Decline:** Cannot calculate without a valid Initial TVL. Set Initial TVL to Current TVL for new pool entry.")
    else:
        st.write(f"**Impermanent Loss:** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
        st.write(f"**TVL Decline:** {tvl_decline:.2f}%")
    
    st.write(f"**Pool Share:** {pool_share:.2f}%")
    if pool_share < 5:
        st.success(f"✅ Pool Share Risk: Low ({pool_share:.2f}%). Safe to enter/exit in a $300K+ pool.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ Pool Share Risk: Moderate ({pool_share:.2f}%). Monitor closely, exit may impact prices.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ Pool Share Risk: High ({pool_share:.2f}%). Reduce exposure, exit may impact prices.")
    else:
        st.warning(f"⚠️ Pool Share Risk: Critical ({pool_share:.2f}%). Exit immediately to avoid severe impact.")

    if initial_tvl > 0:
        if net_return < 1.0:
            st.warning(f"⚠️ TVL Risk: Critical (Net Return < 1.0x). You're losing money, consider exiting.")
            return 0, net_return
        elif tvl_decline >= 50:
            st.warning(f"⚠️ TVL Risk: Critical ({tvl_decline:.2f}% decline). Exit immediately to avoid total loss.")
            return 0, net_return
        elif tvl_decline >= 30:
            st.warning(f"⚠️ TVL Risk: High ({tvl_decline:.2f}% decline). Reduce exposure or exit.")
            return break_even_months, net_return
        elif tvl_decline >= 15:
            st.warning(f"⚠️ TVL Risk: Moderate ({tvl_decline:.2f}% decline). Monitor closely, consider withdrawal.")
            return break_even_months, net_return
        else:
            if apy < apy_exit_threshold or net_return < 1.1:
                st.warning(f"⚠️ TVL Risk: Moderate (APY below threshold or marginal profit). Consider exiting or monitoring closely.")
                return 0, net_return
            else:
                st.success(f"✅ TVL Risk: Low ({tvl_decline:.2f}% decline). Still in profit, no exit needed.")
                return break_even_months, net_return
    else:
        if net_return < 1.0:
            st.warning(f"⚠️ TVL Risk: Critical (Net Return < 1.0x). You're losing money, consider exiting.")
            return 0, net_return
        elif apy < apy_exit_threshold or net_return < 1.1:
            st.warning(f"⚠️ TVL Risk: Moderate (APY below threshold or marginal profit). Consider exiting or monitoring closely.")
            return 0, net_return
        else:
            st.success(f"✅ TVL Risk: Low (Net Return {net_return:.2f}x). Still in profit, no exit needed.")
            return break_even_months, net_return

# Streamlit App
st.title("DM Pool Profit and Risk Analyzer")

st.sidebar.header("Set Your Pool Parameters")

initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", min_value=0.01, step=0.01, value=1.00, format="%.2f")
apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL (set to current TVL if entering today) ($)", 
                                     min_value=0.01, step=0.01, value=1.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

# New inputs for expected price changes
expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")
expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")

# BTC-related inputs with clarified labels
initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                           min_value=0.0, step=0.01, value=1.00, format="%.2f")
current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=0.0, step=0.1, value=1.0, format="%.2f")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
        break_even_months, net_return = check_exit_conditions(investment_amount, apy, il, tvl_decline,
                                                            initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                                                            current_tvl, 12, expected_price_change_asset1, expected_price_change_asset2)
        
        # Projected Pool Value
        st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
        time_periods = [0, 3, 6, 12]
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2,
                                                   current_price_asset1, current_price_asset2)
        future_values = [calculate_future_value(pool_value, apy, months, initial_price_asset1, initial_price_asset2,
                                              current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                              expected_price_change_asset2, investment_amount) for months in time_periods]
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
        
        # Pool vs. BTC Comparison (12 Months Compounding)
        st.subheader("Pool vs. BTC Comparison | 12 Months | Compounding on Pool Assets Only")
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
        st.dataframe(styled_df_btc, use_container_width=True)
        
        # Maximum Drawdown Risk Scenarios
        st.subheader("Maximum Drawdown Risk Scenarios")
        mdd_scenarios = [10, 30, 65, 100]
        btc_mdd_scenarios = [10, 30, 65, 90]

        pool_mdd_values = [investment_amount * (1 - mdd / 100) for mdd in mdd_scenarios]
        initial_btc_amount = investment_amount / (initial_btc_price if initial_btc_price > 0 else current_btc_price)
        btc_mdd_values = [initial_btc_amount * (current_btc_price * (1 - mdd / 100)) for mdd in btc_mdd_scenarios]

        formatted_pool_mdd = [f"{int(value):,}" for value in pool_mdd_values]
        formatted_btc_mdd = [f"{int(value):,}" for value in btc_mdd_values]

        df_risk_scenarios = pd.DataFrame({
            "Scenario": ["10% MDD", "30% MDD", "65% MDD", "90%/100% MDD"],
            "Pool Value ($)": formatted_pool_mdd,
            "BTC Value ($)": formatted_btc_mdd
        })
        styled_df_risk = df_risk_scenarios.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Pool Value ($)", "BTC Value ($)"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Scenario"])
        st.dataframe(styled_df_risk, use_container_width=True)
        st.write("**Note:** Simulated maximum drawdowns based on plausible risk scenarios. Pool MDD assumes IL and TVL decline (e.g., 50% IL + 50% TVL decline for 100% loss). BTC MDD assumes price drops up to 90% (historical worst case). Actual losses may vary.")
        
        # Breakeven Analysis
        st.subheader("Breakeven Analysis")
        df_breakeven = pd.DataFrame({
            "Metric": ["Months to Breakeven Against IL"],
            "Value": [break_even_months]
        })
        st.table(df_breakeven)
