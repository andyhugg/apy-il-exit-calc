import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# [Existing functions remain unchanged: calculate_il, calculate_pool_value, calculate_future_value, etc.]

# Streamlit App
st.title("Pool Profit and Risk Analyzer")

st.markdown("""
Welcome to the Pool Profit and Risk Analyzer! This tool helps you evaluate the profitability and risks of liquidity pools in DeFi or standalone crypto assets. By inputting your parameters, you can assess impermanent loss, net returns, and potential drawdowns, empowering you to make informed investment decisions. **Disclaimer:** This tool is for informational purposes only and does not constitute financial advice. Projections are estimates based on the inputs provided and are not guaranteed to reflect actual future outcomes.
""")

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

st.sidebar.header("Set Your Pool or Asset Parameters")

pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool", "New Asset"])
is_new_pool = (pool_status == "New Pool")
is_new_asset = (pool_status == "New Asset")

if is_new_asset:
    # New Asset Inputs (Single Crypto Project)
    asset_price = st.sidebar.number_input("Asset Price ($)", min_value=0.01, step=0.01, value=100.00, format="%.2f")
    certik_score = st.sidebar.number_input("Certik Score (0-100)", min_value=0, max_value=100, step=1, value=75)
    st.sidebar.markdown("**Note:** Certik Score reflects the project's security audit rating (0-100). Higher scores indicate better security.")
    market_cap = st.sidebar.number_input("Market Cap ($)", min_value=0.01, step=1000.0, value=1000000.00, format="%.2f")
    twitter_followers = st.sidebar.number_input("Twitter Followers", min_value=0, step=100, value=5000)
    twitter_posts = st.sidebar.number_input("Twitter Posts", min_value=0, step=10, value=100)
    expected_growth_rate = st.sidebar.number_input("Expected Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=20.0, format="%.2f")
    current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=84000.00, format="%.2f")
    btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=50.0, format="%.2f")
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
    st.sidebar.markdown("**Note:** Risk-Free Rate defaults to 10% for a stablecoin pool, adjustable for benchmarking.")
    investment_amount = st.sidebar.number_input("Investment Amount ($)", min_value=0.01, step=0.01, value=1000.00, format="%.2f")

    # Map New Asset inputs to existing variables (paired with stablecoin for pool simulation)
    current_price_asset1 = asset_price  # Asset price as Asset 1
    current_price_asset2 = 1.00         # Paired with a stablecoin at $1
    initial_price_asset1 = asset_price  # Same as current for new entry
    initial_price_asset2 = 1.00         # Stablecoin price remains $1
    expected_price_change_asset1 = expected_growth_rate
    expected_price_change_asset2 = 0.0  # Stablecoin price change is 0%
    trust_score = max(1, min(5, int(certik_score / 20)))  # Convert Certik to 1-5 scale
    apy = 0.0  # No APY for a standalone asset, set to 0 (simulates holding)
    initial_tvl = market_cap  # Use market cap as a proxy for TVL if needed
    current_tvl = market_cap  # Assume current TVL equals market cap for simplicity
elif is_new_pool:
    current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    initial_price_asset1 = current_price_asset1
    initial_price_asset2 = current_price_asset2
else:
    initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.01, step=0.01, value=88000.00, format="%.2f")
    initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.01, step=0.01, value=125000.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

if not is_new_asset:
    apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    st.sidebar.markdown("**Note:** **Annual Percentage Yield** For conservative projections, consider halving the entered APY to buffer against market volatility.")
    investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=2000.00, format="%.2f")
    initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", 
                                         min_value=0.01, step=0.01, value=750000.00, format="%.2f")
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")

if not is_new_asset:
    trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
    st.sidebar.markdown("""
    **Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
    - 1 = Unknown (default, highest caution)
    - 2 = Poor (known but with concerns)
    - 3 = Moderate (neutral, some audits)
    - 4 = Good (trusted, audited)
    - 5 = Excellent (top-tier, e.g., Uniswap, Aave)
    """)

if not is_new_asset:
    expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")
    expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-30.0, format="%.2f")
    st.sidebar.markdown("**Note:** We’ll take your expected APY and price changes, stretch them 50% up and down (e.g., 10% becomes 5-15%), and run 200 scenarios to project your pool’s value over 12 months.")

    initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                               min_value=0.0, step=0.01, value=84000.00, format="%.2f")
    current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=84000.00, format="%.2f")
    btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")

    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
    st.sidebar.markdown("""
    **Note:** The Risk-Free Rate is what you could earn in a safe pool (e.g., 5-15%) with no price volatility, such as a stablecoin pool. This rate is used as the stablecoin yield in the "Pool vs. BTC vs. Stablecoin Comparison" section. The Hurdle Rate is this rate plus 6% (average global inflation in 2025), setting the minimum return your pool needs to beat to outpace inflation and justify the risk.
    """)

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl) if not is_new_asset else 0.0  # No TVL decline for new asset
        break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
        break_even_months_with_price = calculate_break_even_months_with_price_changes(
            investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool or is_new_asset
        )
        result = check_exit_conditions(
            investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool or is_new_asset, btc_growth_rate
        )
        break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril = result
        
        # For New Asset, adjust display to focus on holding value rather than pool metrics
        if is_new_asset:
            st.subheader("Projected Asset Value Based on Expected Growth Rate")
            st.write(f"**Note:** Projections assume you hold the asset directly, with no liquidity pool involvement. Initial value is your investment amount (${investment_amount:,.2f}).")
            time_periods = [0, 3, 6, 12]
            future_values = []
            for months in time_periods:
                monthly_growth = (expected_growth_rate / 100) / 12
                value = investment_amount * (1 + monthly_growth * months)
                future_values.append(value)
            future_ils = [0.0] * len(time_periods)  # No IL for holding a single asset

            formatted_values = [f"{int(value):,}" for value in future_values]
            formatted_ils = [f"{il:.2f}%" for il in future_ils]
            df_projection = pd.DataFrame({
                "Time Period (Months)": time_periods,
                "Projected Value ($)": formatted_values,
                "Projected Impermanent Loss (%)": formatted_ils
            })
            styled_df = df_projection.style.set_properties(**{
                'text-align': 'right'
            }, subset=["Projected Value ($)", "Projected Impermanent Loss (%)"]).set_properties(**{
                'text-align': 'right'
            }, subset=["Time Period (Months)"])
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
            
            # Enhanced Matplotlib Chart
            sns.set_theme()
            plt.figure(figsize=(10, 6))
            plt.plot(time_periods, future_values, marker='o', markersize=10, linewidth=3, color='#1f77b4', label="Asset Value")
            plt.fill_between(time_periods, future_values, color='#1f77b4', alpha=0.2)
            plt.axhline(y=investment_amount, color='#ff3333', linestyle='--', linewidth=2, label=f"Initial Investment (${investment_amount:,.0f})")
            y_max = max(max(future_values), investment_amount) * 1.1
            y_min = min(min(future_values), investment_amount) * 0.9
            plt.fill_between(time_periods, investment_amount, y_max, color='green', alpha=0.1, label='Profit Zone')
            plt.fill_between(time_periods, y_min, investment_amount, color='red', alpha=0.1, label='Loss Zone')
            for i, value in enumerate(future_values):
                plt.text(time_periods[i], value + (y_max - y_min) * 0.05, f"${value:,.0f}", ha='center', fontsize=10, color='#1f77b4')
            final_value = future_values[-1]
            plt.annotate(f"Final Value: ${final_value:,.0f}", 
                         xy=(12, final_value), 
                         xytext=(10, final_value + (y_max - y_min) * 0.15),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                         fontsize=10, color='black')
            plt.title("Projected Asset Value Over Time", fontsize=16, pad=20)
            plt.xlabel("Months", fontsize=12)
            plt.ylabel("Value ($)", fontsize=12)
            plt.xticks(time_periods, fontsize=10)
            plt.yticks(fontsize=10)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend(fontsize=10)
            plt.gca().set_facecolor('#f0f0f0')
            plt.tight_layout()
            st.pyplot(plt)

            st.subheader("Asset vs. BTC vs. Stablecoin Comparison | 12 Months")
            st.write(f"**Note:** Asset Value is based on an expected {expected_growth_rate:.1f}% annual growth rate. BTC comparison assumes a {btc_growth_rate:.1f}% annual growth rate. Stablecoin comparison assumes the risk-free rate of {risk_free_rate:.1f}% APY with no price volatility.")
            
            projected_btc_value = investment_amount * (1 + btc_growth_rate / 100)
            asset_value_12_months = future_values[-1]
            stablecoin_value_12_months = investment_amount * (1 + risk_free_rate / 100)
            
            df_comparison = pd.DataFrame({
                "Metric": [
                    "Projected Asset Value",
                    "Value if Invested in BTC",
                    f"Value if Invested in Stablecoin (Risk-Free Rate: {risk_free_rate:.1f}%)",
                ],
                "Value": [
                    f"${int(asset_value_12_months):,}",
                    f"${int(projected_btc_value):,}",
                    f"${int(stablecoin_value_12_months):,}",
                ]
            })
            st.dataframe(df_comparison.style.set_properties(**{'text-align': 'right'}), hide_index=True, use_container_width=True)
            
            st.subheader("Maximum Drawdown Risk Scenarios")
            mdd_scenarios = [10, 30, 65, 100]
            asset_mdd_values = [asset_value_12_months * (1 - mdd / 100) for mdd in mdd_scenarios]
            btc_mdd_values = [projected_btc_value * (1 - mdd / 100) for mdd in mdd_scenarios]
            
            df_mdd = pd.DataFrame({
                "Scenario": ["10% MDD", "30% MDD", "65% MDD", "100% MDD"],
                "Asset Value ($)": [f"${int(value):,}" for value in asset_mdd_values],
                "BTC Value ($)": [f"${int(value):,}" for value in btc_mdd_values]
            })
            st.dataframe(df_mdd.style.set_properties(**{'text-align': 'right'}), hide_index=True, use_container_width=True)
            
            st.subheader("Simplified Monte Carlo Analysis - 12 Month Projections")
            growth_range = [expected_growth_rate * 0.5, expected_growth_rate * 1.5] if expected_growth_rate >= 0 else [expected_growth_rate * 1.5, expected_growth_rate * 0.5]
            growth_samples = np.random.uniform(growth_range[0], growth_range[1], 200)
            values = [investment_amount * (1 + growth / 100) for growth in growth_samples]
            worst_value = sorted(values)[19]  # 10th percentile
            best_value = sorted(values)[179]  # 90th percentile
            expected_value = asset_value_12_months
            
            df_monte_carlo = pd.DataFrame({
                "Scenario": ["Worst Case", "Expected Case", "Best Case"],
                "Projected Value ($)": [f"${worst_value:,.0f}", f"${expected_value:,.0f}", f"${best_value:,.0f}"]
            })
            st.dataframe(df_monte_carlo.style.set_properties(**{'text-align': 'center'}), hide_index=True, use_container_width=True)
        else:
            # [Original pool calculation and display logic remains unchanged]
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
            
            # [Remaining original display code for pool projections, charts, comparisons, MDD, Monte Carlo, and CSV export]
