import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import csv

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
    
    apy_compounded_value = pool_value * (1 + monthly_apy) ** months
    
    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    final_pool_value_base = initial_investment * np.sqrt(final_price_asset1 * final_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    initial_pool_value_base = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    price_adjustment_ratio = final_pool_value_base / initial_pool_value_base if initial_pool_value_base > 0 else 1
    
    current_value = apy_compounded_value * price_adjustment_ratio
    
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

def calculate_break_even_months_with_price_changes(initial_investment: float, apy: float, pool_value: float,
                                                  initial_price_asset1: float, initial_price_asset2: float,
                                                  current_price_asset1: float, current_price_asset2: float,
                                                  expected_price_change_asset1: float, expected_price_change_asset2: float) -> float:
    if apy <= 0:
        return float('inf')

    monthly_apy = (apy / 100) / 12
    months = 0
    current_value = pool_value
    
    while current_value < initial_investment and months < 1000:
        months += 1
        current_value = calculate_future_value(pool_value, apy, months, initial_price_asset1, initial_price_asset2,
                                              current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                              expected_price_change_asset2, initial_investment)
    
    return round(months, 2) if months < 1000 else float('inf')

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_decline = (initial_tvl - current_tvl) / initial_tvl * 100
    return round(tvl_decline, 2)

def calculate_composite_risk_score(il: float, tvl_decline: float, pool_share: float, net_return: float) -> tuple[float, str]:
    il_risk = min(il / 5, 1) * 0.3
    tvl_risk = min(tvl_decline / 50, 1) * 0.3
    pool_share_risk = min((pool_share / 20), 1) * 0.2
    net_return_risk = max(0, (1 - net_return) * 0.2) if net_return < 1 else 0
    
    risk_score = (il_risk + tvl_risk + pool_share_risk + net_return_risk) * 100
    risk_category = "Low" if risk_score < 25 else "Moderate" if risk_score < 50 else "High" if risk_score < 75 else "Critical"
    return round(risk_score, 2), risk_category

def check_exit_conditions(initial_investment: float, apy: float, il: float, tvl_decline: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl: float, months: int = 12, expected_price_change_asset1: float = 0.0,
                         expected_price_change_asset2: float = 0.0):
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2)
    
    future_value = calculate_future_value(pool_value, apy, months, initial_price_asset1, initial_price_asset2,
                                         current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                         expected_price_change_asset2, initial_investment)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    future_pool_value_no_apy = calculate_future_value(pool_value, 0.0, months, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                    expected_price_change_asset2, initial_investment)
    
    total_loss_percentage = ((initial_investment - future_pool_value_no_apy) / initial_investment) * 100 if initial_investment > 0 else 0
    apy_exit_threshold = max(0, total_loss_percentage * 12 / months if months > 0 else 0)
    
    break_even_months = calculate_break_even_months(apy, il)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0
    
    risk_score, risk_category = calculate_composite_risk_score(il, tvl_decline, pool_share, net_return)

    st.subheader("Results:")
    if initial_tvl <= 0:
        st.write(f"**Impermanent Loss:** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (accounts for expected price changes for Asset 1 and Asset 2; 0% indicates no exit needed due to price gains)")
        st.write(f"**TVL Decline:** Cannot calculate without a valid Initial TVL. Set Initial TVL to Current TVL for new pool entry.")
    else:
        st.write(f"**Impermanent Loss:** {il:.2f}%")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (accounts for expected price changes for Asset 1 and Asset 2; 0% indicates no exit needed due to price gains)")
        st.write(f"**TVL Decline:** {tvl_decline:.2f}%")
    
    st.write(f"**Pool Share:** {pool_share:.2f}%")
    st.write(f"**Composite Risk Score:** {risk_score}% ({risk_category})")
    if pool_share < 5:
        st.success(f"✅ Pool Share Risk: Low ({pool_share:.2f}%). Safe to enter/exit in a $300K+ pool.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ Pool Share Risk: Moderate ({pool_share:.2f}%). Monitor closely, exit may impact prices.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ Pool Share Risk: High ({pool_share:.2f}%). Reduce exposure, exit may impact prices.")
    else:
        st.warning(f"⚠️ Pool Share Risk: Critical ({pool_share:.2f}%). Exit immediately to avoid severe impact.")

    if initial_tvl > 0:
        if tvl_decline >= 50:
            st.warning(f"⚠️ TVL Decline Risk: Critical ({tvl_decline:.2f}% decline). Exit immediately to avoid total loss.")
        elif tvl_decline >= 30:
            st.warning(f"⚠️ TVL Decline Risk: High ({tvl_decline:.2f}% decline). Reduce exposure or exit.")
        elif tvl_decline >= 15:
            st.warning(f"⚠️ TVL Decline Risk: Moderate ({tvl_decline:.2f}% decline). Monitor closely, consider withdrawal.")
        else:
            st.success(f"✅ TVL Decline Risk: Low ({tvl_decline:.2f}% decline). Pool health appears stable.")

    if initial_tvl > 0:
        if net_return < 1.0:
            st.warning(f"⚠️ Investment Risk: Critical (Net Return < 1.0x). You're losing money, consider exiting.")
            return 0, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category
        elif apy < apy_exit_threshold or net_return < 1.1:
            st.warning(f"⚠️ Investment Risk: Moderate (APY below threshold or marginal profit). Consider exiting or monitoring closely.")
            return 0, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category
        else:
            st.success(f"✅ Investment Risk: Low (Net Return {net_return:.2f}x). Still in profit, no exit needed.")
            return break_even_months, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category
    else:
        if net_return < 1.0:
            st.warning(f"⚠️ Investment Risk: Critical (Net Return < 1.0x). You're losing money, consider exiting.")
            return 0, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category
        elif apy < apy_exit_threshold or net_return < 1.1:
            st.warning(f"⚠️ Investment Risk: Moderate (APY below threshold or marginal profit). Consider exiting or monitoring closely.")
            return 0, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category
        else:
            st.success(f"✅ Investment Risk: Low (Net Return {net_return:.2f}x). Still in profit, no exit needed.")
            return break_even_months, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category

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
        break_even_months, net_return, break_even_months, break_even_months_with_price, apy_exit_threshold, pool_share, risk_score, risk_category = check_exit_conditions(
            investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, 12, expected_price_change_asset1, expected_price_change_asset2
        )
        
        # Projected Pool Value
        st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
        st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${investment_amount:,.2f}).")
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
        asset1_change_text = f"{abs(expected_price_change_asset1)}% {asset1_change_desc}" if expected_price_change_asset1 != 0 else "0% change"
        asset2_change_text = f"{abs(expected_price_change_asset2)}% {asset2_change_desc}" if expected_price_change_asset2 != 0 else "0% change"
        st.write(f"**Note:** Pool Value includes expected {asset1_change_text} of Asset 1 and {asset2_change_text} for Asset 2.")
        
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
        st.write("**Note:** Simulated maximum drawdowns based on projected values after 12 months, including expected price changes (e.g., 10% appreciation of Asset 1, 0% change for Asset 2) and 5% APY for the pool, and 10% growth for BTC.")
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
        st.write("**Note:** 'Months to Breakeven Against IL' reflects only the recovery of impermanent loss with APY, while 'Months to Breakeven Including Expected Price Changes' includes the total loss relative to initial investment, factoring in both APY and expected price changes, which may extend the breakeven period.")
        
        # Export Results
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Impermanent Loss (%)", f"{il:.2f}"])
        writer.writerow(["Net Return (x)", f"{net_return:.2f}"])
        writer.writerow(["APY Exit Threshold (%)", f"{apy_exit_threshold:.2f}"])
        writer.writerow(["TVL Decline (%)", f"{tvl_decline:.2f}" if initial_tvl > 0 else "N/A"])
        writer.writerow(["Pool Share (%)", f"{pool_share:.2f}"])
        writer.writerow(["Composite Risk Score (%)", f"{risk_score}"])
        writer.writerow(["Risk Category", risk_category])
        writer.writerow(["Months to Breakeven Against IL", f"{break_even_months}"])
        writer.writerow(["Months to Breakeven Including Expected Price Changes", f"{break_even_months_with_price}"])
        st.download_button(label="Export Results as CSV", data=output.getvalue(), file_name="pool_analysis_results.csv", mime="text/csv")
