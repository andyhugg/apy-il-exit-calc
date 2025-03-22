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
Welcome to the Pool Profit and Risk Analyzer! This tool helps you evaluate the profitability and risks of liquidity pools in DeFi. By inputting your pool parameters, you can assess impermanent loss, net returns, and potential drawdowns, empowering you to make informed investment decisions. **Disclaimer:** This tool is for informational purposes only and does not constitute financial advice. Projections are estimates based on the inputs provided and are not guaranteed to reflect actual future outcomes.
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

st.sidebar.header("Set Your Pool Parameters")

pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool", "New Asset"])
is_new_pool = (pool_status == "New Pool")
is_new_asset = (pool_status == "New Asset")

if is_new_asset:
    # New Asset Inputs
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

    # Map New Asset inputs to existing variables
    current_price_asset1 = asset_price  # Asset price as Asset 1
    current_price_asset2 = 1.00         # Assume paired with a stablecoin at $1
    initial_price_asset1 = asset_price  # Same as current for new entry
    initial_price_asset2 = 1.00         # Stablecoin price remains $1
    expected_price_change_asset1 = expected_growth_rate
    expected_price_change_asset2 = 0.0  # Stablecoin price change is 0%
    trust_score = max(1, min(5, int(certik_score / 20)))  # Convert Certik to 1-5 scale
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

apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
st.sidebar.markdown("**Note:** **Annual Percentage Yield** For conservative projections, consider halving the entered APY to buffer against market volatility.")

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

investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=2000.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", 
                                     min_value=0.01, step=0.01, value=750000.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")

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
    **Note:** The Risk-Free Rate is what you could earn in a safe pool (e.g., 5-15%) with no price volatility, such as a stablecoin pool. This rate is used as the stablecoin yield in the "Pool vs. BTC vs. Stablecoin Comparison" section. The Hurdle Rate is this rate plus 6% (average global inflation in 2025), setting the minimum APY your pool needs to beat to outpace inflation and justify the risk.
    """)

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
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
        
        # [The rest of the calculation and display logic remains unchanged, including metric cards, projections, MDD, and Monte Carlo sections]
        
        st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
        st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${investment_amount:,.2f}).")
        time_periods = [0, 3, 6, 12]
        future_values = []
        future_ils = []
        for months in time_periods:
            value, il_at_time = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                      current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                      expected_price_change_asset2, is_new_pool or is_new_asset)
            future_values.append(value)
            future_ils.append(il_at_time)
        
        # [Remaining display code for projections, charts, comparisons, MDD, Monte Carlo, and CSV export remains unchanged]
