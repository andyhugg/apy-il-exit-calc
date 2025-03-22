import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Pool Profit and Risk Analyzer Functions
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float, initial_investment: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2
    
    sqrt_price_ratio = (price_ratio_current / price_ratio_initial) ** 0.5
    
    amount_asset2 = initial_amount_asset2 * sqrt_price_ratio
    amount_asset1 = initial_amount_asset1 / sqrt_price_ratio
    
    value_in_pool = (amount_asset1 * current_price_asset1) + (amount_asset2 * current_price_asset2)
    
    impermanent_loss = ((value_in_pool - value_if_held) / value_if_held) * 100
    return impermanent_loss

def simplified_monte_carlo_pool_analysis(initial_price_asset1: float, initial_price_asset2: float, initial_investment: float, apy: float) -> tuple:
    num_simulations = 200
    price_changes_asset1 = np.random.uniform(-0.5, 0.5, num_simulations)
    price_changes_asset2 = np.random.uniform(-0.5, 0.5, num_simulations)
    
    final_values = []
    for i in range(num_simulations):
        current_price_asset1 = initial_price_asset1 * (1 + price_changes_asset1[i])
        current_price_asset2 = initial_price_asset2 * (1 + price_changes_asset2[i])
        
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
        
        pool_value = (initial_investment * (1 + (apy / 100))) + (initial_investment * (il / 100))
        final_values.append(pool_value)
    
    final_values.sort()
    worst_case = final_values[int(0.1 * num_simulations)]
    expected_case = (initial_investment * (1 + (apy / 100))) + (initial_investment * (il / 100))
    best_case = final_values[int(0.9 * num_simulations)]
    
    return worst_case, expected_case, best_case

def simplified_monte_carlo_asset_analysis(initial_price: float, expected_growth_rate: float) -> tuple:
    num_simulations = 200
    growth_rates = np.random.uniform(expected_growth_rate * 0.5, expected_growth_rate * 1.5, num_simulations)
    
    final_prices = [initial_price * (1 + rate / 100) for rate in growth_rates]
    final_prices.sort()
    
    worst_case = final_prices[int(0.1 * num_simulations)]
    expected_case = initial_price * (1 + expected_growth_rate / 100)
    best_case = final_prices[int(0.9 * num_simulations)]
    
    return worst_case, expected_case, best_case

def calculate_mdd_asset(initial_price: float, expected_growth_rate: float) -> tuple:
    num_simulations = 200
    growth_rates = np.random.uniform(expected_growth_rate * 0.5, expected_growth_rate * 1.5, num_simulations)
    months = 12
    
    mdds = []
    for rate in growth_rates:
        monthly_growth = rate / 12
        prices = [initial_price * (1 + monthly_growth / 100) ** t for t in range(months + 1)]
        
        peak = prices[0]
        max_drawdown = 0
        for price in prices:
            peak = max(peak, price)
            drawdown = (peak - price) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        mdds.append(max_drawdown)
    
    average_mdd = np.mean(mdds)
    worst_case_mdd = max(mdds)
    return average_mdd, worst_case_mdd

# Streamlit App
st.set_page_config(page_title="Crypto Asset and Pool Analyzer", layout="wide")

st.title("Crypto Asset and Pool Analyzer")
st.markdown("""
Welcome to the Crypto Asset and Pool Analyzer! This tool helps you analyze crypto assets and liquidity pools to make informed investment decisions.  
- **New Asset**: Analyze a single asset’s growth potential and risks.  
- **Existing Pool**: Evaluate an existing liquidity pool’s performance, including impermanent loss and risk.  
- **New Pool**: Project the performance of a new liquidity pool with expected price changes.  
All data can be sourced from Certik.com for a streamlined experience.
""")

# Sidebar for Analysis Selection
st.sidebar.header("Analysis Selection")
analysis_type = st.sidebar.selectbox("Select Analysis Type", ["New Asset", "Existing Pool", "New Pool"])

# Macro Environment Input (Common to All Analyses)
st.sidebar.header("Macro Environment")
macro_environment = st.sidebar.selectbox("Macro Environment", ["Bullish", "Bearish", "Neutral"], index=2)
macro_multiplier = 0.8 if macro_environment == "Bullish" else 1.2 if macro_environment == "Bearish" else 1.0
st.sidebar.markdown("The macro environment adjusts the Hurdle Rate and volatility risk. Bullish lowers the Hurdle Rate, Bearish increases it.")

# Analysis-Specific Inputs
if analysis_type == "New Asset":
    st.sidebar.header("New Asset Inputs")
    asset_1_price = st.sidebar.number_input("Asset 1 Price ($)", min_value=0.0, value=1.0, step=0.01)
    expected_growth_rate = st.sidebar.number_input("Expected Growth Rate (%)", value=30.0, step=1.0)
    market_cap = st.sidebar.number_input("Market Cap ($)", min_value=0.0, value=50_000_000.0, step=1_000_000.0, help="Source from Certik.com")
    volume_24h = st.sidebar.number_input("24-Hour Trading Volume ($)", min_value=0.0, value=1_000_000.0, step=100_000.0, help="Source from Certik.com")
    twitter_followers = st.sidebar.number_input("Total Twitter Followers", min_value=0, value=526609, step=1000, help="Source from Certik.com")
    total_tweets = st.sidebar.number_input("Total Tweets", min_value=0, value=1642, step=100, help="Source from Certik.com")
    certik_trust_score = st.sidebar.number_input("Certik.com Trust Score (0-100, optional)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, help="Source from Certik.com")
    btc_current_price = st.sidebar.number_input("BTC Current Price ($)", min_value=0.0, value=50_000.0, step=1_000.0)
    btc_expected_growth_rate = st.sidebar.number_input("BTC Expected Growth Rate (%)", value=20.0, step=1.0)
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, step=0.1)
    
    # Macro Environment Guidance for BTC Growth Rate
    btc_guidance = 30.0 if macro_environment == "Bullish" else -10.0 if macro_environment == "Bearish" else 10.0
    st.sidebar.markdown(f"In a {macro_environment} environment, consider setting BTC Expected Growth Rate to {btc_guidance}%.")

    # Asset Analysis
    st.header("New Asset Analysis")
    
    # Base Calculations
    projected_price = asset_1_price * (1 + expected_growth_rate / 100)
    projected_market_cap = market_cap * (1 + expected_growth_rate / 100)
    
    # Hurdle Rate with Macro Adjustment
    base_hurdle_rate = risk_free_rate + 6.0
    hurdle_rate = base_hurdle_rate * macro_multiplier
    asset_vs_hurdle = expected_growth_rate - hurdle_rate
    
    # Asset vs. BTC Performance
    btc_projected_price = btc_current_price * (1 + btc_expected_growth_rate / 100)
    asset_value = projected_price / asset_1_price
    btc_value = btc_projected_price / btc_current_price
    asset_vs_btc = ((asset_value / btc_value) - 1) * 100
    
    # Volatility Risk Score
    volatility_score = (abs(expected_growth_rate) / 50) * (5e9 / market_cap) * 50 * macro_multiplier
    volatility_score = min(volatility_score, 100)
    
    # Market Cap Rank Risk
    if market_cap > 5_000_000_000:
        market_cap_rank_score = 2
    elif market_cap > 1_000_000_000:
        market_cap_rank_score = 1
    elif market_cap > 500_000_000:
        market_cap_rank_score = 0
    elif market_cap > 100_000_000:
        market_cap_rank_score = -1
    else:
        market_cap_rank_score = -2
    
    # Risk-Adjusted Return (Sharpe Ratio)
    sharpe_ratio = (expected_growth_rate - risk_free_rate) / (expected_growth_rate * 0.5)
    
    # Liquidity Risk Score (Updated with Volume)
    liquidity_risk_score = (1e9 / market_cap) * 25 * (1e9 / volume_24h) * 10
    liquidity_risk_score = min(liquidity_risk_score, 100)
    
    # Maximum Drawdown
    average_mdd, worst_case_mdd = calculate_mdd_asset(asset_1_price, expected_growth_rate)
    
    # Contract/Program Risk (Certik Trust Score)
    contract_risk_score = 100 - certik_trust_score if certik_trust_score > 0 else 50
    
    # Community Engagement Score
    follower_score = (twitter_followers / 1e6) * 50
    follower_score = min(follower_score, 100)
    tweet_score = (total_tweets / 10_000) * 50
    tweet_score = min(tweet_score, 100)
    community_engagement_score = (follower_score + tweet_score) / 2
    
    # Followers-to-Tweets Ratio
    followers_to_tweets_ratio = (total_tweets / twitter_followers) * 100 if twitter_followers > 0 else 0
    
    # Composite Score (Removed FD Mcap Growth, Mcap to FD Mcap Ratio, Token Security Risk)
    total_score = 0
    
    # 1. Projected Growth Rate
    if expected_growth_rate > 50:
        total_score += 2
    elif expected_growth_rate > 20:
        total_score += 1
    elif expected_growth_rate > 0:
        total_score += 0
    elif expected_growth_rate > -20:
        total_score -= 1
    else:
        total_score -= 2
    
    # 2. Asset vs. Hurdle Rate Performance
    if asset_vs_hurdle > 20:
        total_score += 2
    elif asset_vs_hurdle > 5:
        total_score += 1
    elif asset_vs_hurdle > -5:
        total_score += 0
    elif asset_vs_hurdle > -20:
        total_score -= 1
    else:
        total_score -= 2
    
    # 3. Asset vs. BTC Performance
    if asset_vs_btc > 20:
        total_score += 2
    elif asset_vs_btc > 5:
        total_score += 1
    elif asset_vs_btc > -5:
        total_score += 0
    elif asset_vs_btc > -20:
        total_score -= 1
    else:
        total_score -= 2
    
    # 4. Volatility Risk Score
    if volatility_score < 25:
        total_score += 2
    elif volatility_score < 50:
        total_score += 1
    elif volatility_score < 75:
        total_score += 0
    elif volatility_score < 90:
        total_score -= 1
    else:
        total_score -= 2
    
    # 5. Market Cap Rank Risk
    total_score += market_cap_rank_score
    
    # 6. Risk-Adjusted Return (Sharpe Ratio)
    if sharpe_ratio > 2:
        total_score += 2
    elif sharpe_ratio > 1:
        total_score += 1
    elif sharpe_ratio > 0:
        total_score += 0
    elif sharpe_ratio > -1:
        total_score -= 1
    else:
        total_score -= 2
    
    # 7. Liquidity Risk Score
    if liquidity_risk_score < 25:
        total_score += 2
    elif liquidity_risk_score < 50:
        total_score += 1
    elif liquidity_risk_score < 75:
        total_score += 0
    elif liquidity_risk_score < 90:
        total_score -= 1
    else:
        total_score -= 2
    
    # 8. Maximum Drawdown Risk
    if average_mdd < 15:
        total_score += 2
    elif average_mdd < 30:
        total_score += 1
    elif average_mdd < 50:
        total_score += 0
    elif average_mdd < 75:
        total_score -= 1
    else:
        total_score -= 2
    
    # 9. Contract/Program Risk (Certik Trust Score)
    if contract_risk_score < 25:
        total_score += 2
    elif contract_risk_score < 50:
        total_score += 1
    elif contract_risk_score < 75:
        total_score += 0
    elif contract_risk_score < 90:
        total_score -= 1
    else:
        total_score -= 2
    
    # 10. Community Engagement Score
    if community_engagement_score > 75:
        total_score += 2
    elif community_engagement_score > 50:
        total_score += 1
    elif community_engagement_score > 25:
        total_score += 0
    elif community_engagement_score > 10:
        total_score -= 1
    else:
        total_score -= 2
    
    # Decision Outcome (Adjusted for 10 Metrics, Range -20 to +20)
    if total_score >= 15:
        recommendation = "Strong Buy"
        rec_color = "green"
    elif total_score >= 8:
        recommendation = "Buy"
        rec_color = "lightgreen"
    elif total_score >= -7:
        recommendation = "Wait"
        rec_color = "yellow"
    elif total_score >= -14:
        recommendation = "Sell"
        rec_color = "orange"
    else:
        recommendation = "Strong Sell"
        rec_color = "red"
    
    # Metric Cards (Restored Original Stacking Style)
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Investment Recommendation", recommendation, f"Score: {total_score}", delta_color="off")
        st.markdown(f"<div style='background-color: {rec_color}; padding: 10px; border-radius: 5px; text-align: center;'>Recommendation: {recommendation}</div>", unsafe_allow_html=True)
        st.metric("Projected Price (12 Months)", f"${projected_price:.2f}", f"{expected_growth_rate}%")
        st.metric("Projected Market Cap (12 Months)", f"${projected_market_cap:,.0f}")
        market_cap_label = "Very Low Risk" if market_cap > 5_000_000_000 else "Low Risk" if market_cap > 1_000_000_000 else "Neutral" if market_cap > 500_000_000 else "Moderate Risk" if market_cap > 100_000_000 else "High Risk"
        market_cap_color = "green" if market_cap > 5_000_000_000 else "lightgreen" if market_cap > 1_000_000_000 else "yellow" if market_cap > 500_000_000 else "orange" if market_cap > 100_000_000 else "red"
        st.metric("Market Cap Risk", market_cap_label, f"Market Cap: ${market_cap:,.0f}", delta_color="off")
        st.markdown(f"<div style='background-color: {market_cap_color}; padding: 5px; border-radius: 5px; text-align: center;'>Smaller market caps (< $500M) carry higher risks.</div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Hurdle Rate", f"{hurdle_rate:.2f}%", f"Adjusted for {macro_environment} macro environment", delta_color="off")
        st.metric("Asset vs. Hurdle Rate Performance", f"{asset_vs_hurdle:.2f}%")
        st.metric("Asset vs. BTC Performance", f"{asset_vs_btc:.2f}%")
        st.metric("Volatility Risk Score", f"{volatility_score:.2f}%", "High risk due to small market cap" if market_cap < 500_000_000 else "", delta_color="off")
        st.metric("Liquidity Risk", f"{liquidity_risk_score:.2f}%", "Low volume increases slippage risk" if volume_24h < 1_000_000 else "", delta_color="off")
        st.metric("Risk-Adjusted Return (Sharpe Ratio)", f"{sharpe_ratio:.2f}")
        st.metric("Maximum Drawdown Risk", f"Average MDD: {average_mdd:.2f}%", f"Worst-Case MDD: {worst_case_mdd:.2f}%", delta_color="off")
        contract_label = "Low Risk" if contract_risk_score < 25 else "Moderate Risk" if contract_risk_score < 50 else "Neutral" if contract_risk_score < 75 else "High Risk" if contract_risk_score < 90 else "Very High Risk"
        contract_color = "green" if contract_risk_score < 25 else "yellow" if contract_risk_score < 50 else "orange" if contract_risk_score < 75 else "red" if contract_risk_score < 90 else "darkred"
        st.metric("Contract/Program Risk", f"{contract_risk_score:.2f}% ({contract_label})", "Based on Certik Trust Score", delta_color="off")
        st.markdown(f"<div style='background-color: {contract_color}; padding: 5px; border-radius: 5px; text-align: center;'>{contract_label}</div>", unsafe_allow_html=True)
        st.metric("Community Engagement Score", f"{community_engagement_score:.2f}%")
        ratio_label = "Low Activity" if followers_to_tweets_ratio < 0.1 else "Balanced Activity" if followers_to_tweets_ratio < 1 else "High Activity" if followers_to_tweets_ratio < 5 else "Very High Activity"
        ratio_color = "orange" if followers_to_tweets_ratio < 0.1 else "green" if followers_to_tweets_ratio < 1 else "yellow" if followers_to_tweets_ratio < 5 else "red"
        st.metric("Followers-to-Tweets Ratio", f"{followers_to_tweets_ratio:.2f}% ({ratio_label})", "Measures Twitter activity relative to followers", delta_color="off")
        st.markdown(f"<div style='background-color: {ratio_color}; padding: 5px; border-radius: 5px; text-align: center;'>{ratio_label}</div>", unsafe_allow_html=True)
    
    # Monte Carlo Analysis
    worst_case_price, expected_case_price, best_case_price = simplified_monte_carlo_asset_analysis(asset_1_price, expected_growth_rate)
    
    # Seaborn Chart
    st.subheader("Asset Price Projection Over 12 Months")
    months = np.arange(0, 13)
    monthly_growth = expected_growth_rate / 12
    expected_prices = [asset_1_price * (1 + monthly_growth / 100) ** t for t in months]
    worst_case_prices = [asset_1_price * (worst_case_price / expected_case_price) * (1 + monthly_growth / 100) ** t for t in months]
    best_case_prices = [asset_1_price * (best_case_price / expected_case_price) * (1 + monthly_growth / 100) ** t for t in months]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=months, y=expected_prices, label="Expected Price", color="blue", ax=ax)
    ax.fill_between(months, worst_case_prices, best_case_prices, color="gray", alpha=0.3, label="Monte Carlo Range (Worst to Best)")
    ax.set_xlabel("Months")
    ax.set_ylabel("Price ($)")
    ax.set_title("Asset Price Projection Over 12 Months")
    ax.legend()
    st.pyplot(fig)
    
    # Monte Carlo Results Table
    monte_carlo_data = {
        "Scenario": ["Worst Case", "Expected Case", "Best Case"],
        "Price ($)": [worst_case_price, expected_case_price, best_case_price],
        "Growth (%)": [(worst_case_price / asset_1_price - 1) * 100, expected_growth_rate, (best_case_price / asset_1_price - 1) * 100]
    }
    st.table(monte_carlo_data)
    
    # Risk Summary
    st.subheader("Risk Summary")
    if market_cap < 500_000_000:
        st.markdown("⚠️ **Market Cap Risk**: This asset has a market cap of ${:,.0f}, placing it in the high-risk category. Smaller market caps are more prone to volatility, low liquidity, and manipulation.".format(market_cap))
    if liquidity_risk_score > 75:
        st.markdown("⚠️ **Liquidity Risk**: High liquidity risk ({:.2f}%) due to low 24-hour volume. This may lead to price slippage and difficulty exiting positions.".format(liquidity_risk_score))
    if average_mdd > 30:
        st.markdown("⚠️ **Maximum Drawdown Risk**: An average MDD of {:.2f}% suggests significant downside risk over the 12-month period.".format(average_mdd))
    if contract_risk_score > 50:
        st.markdown("⚠️ **Contract/Program Risk**: High risk ({:.2f}%) based on a Certik Trust Score of {:.0f}. Consider the security risks of this asset.".format(contract_risk_score, certik_trust_score))
    else:
        st.markdown("✅ **Contract/Program Risk**: Low risk ({:.2f}%) based on a Certik Trust Score of {:.0f}.".format(contract_risk_score, certik_trust_score))
    if community_engagement_score > 50:
        st.markdown("✅ **Community Engagement**: High ({:.2f}%) indicates strong social presence, which may support price growth.".format(community_engagement_score))
    else:
        st.markdown("⚠️ **Community Engagement**: Low ({:.2f}%) suggests limited social presence, which may hinder adoption.".format(community_engagement_score))
    if followers_to_tweets_ratio < 0.1:
        st.markdown("⚠️ **Twitter Activity**: Low ({:.2f}%) suggests potential inactivity or fake followers.".format(followers_to_tweets_ratio))
    elif followers_to_tweets_ratio > 5:
        st.markdown("⚠️ **Twitter Activity**: Very High ({:.2f}%) may indicate excessive posting or spamming.".format(followers_to_tweets_ratio))
    else:
        st.markdown("✅ **Twitter Activity**: Balanced ({:.2f}%) suggests healthy engagement relative to the follower base.".format(followers_to_tweets_ratio))
    
    # CSV Export
    export_data = {
        "Recommendation": [recommendation],
        "Total Score": [total_score],
        "Projected Price": [projected_price],
        "Projected Market Cap": [projected_market_cap],
        "Market Cap Risk": [market_cap_label],
        "Hurdle Rate (%)": [hurdle_rate],
        "Asset vs. Hurdle Rate (%)": [asset_vs_hurdle],
        "Asset vs. BTC Performance (%)": [asset_vs_btc],
        "Volatility Risk Score (%)": [volatility_score],
        "Liquidity Risk Score (%)": [liquidity_risk_score],
        "Risk-Adjusted Return (Sharpe Ratio)": [sharpe_ratio],
        "Average MDD (%)": [average_mdd],
        "Worst-Case MDD (%)": [worst_case_mdd],
        "Certik Trust Score": [certik_trust_score],
        "Contract/Program Risk Score (%)": [contract_risk_score],
        "24-Hour Volume ($)": [volume_24h],
        "Total Twitter Followers": [twitter_followers],
        "Total Tweets": [total_tweets],
        "Community Engagement Score (%)": [community_engagement_score],
        "Followers-to-Tweets Ratio (%)": [followers_to_tweets_ratio]
    }
    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False)
    st.download_button("Download Analysis as CSV", csv, "asset_analysis.csv", "text/csv")

elif analysis_type == "Existing Pool":
    st.sidebar.header("Existing Pool Inputs")
    initial_price_asset1 = st.sidebar.number_input("Initial Price Asset 1 ($)", min_value=0.0, value=1.0, step=0.01)
    initial_price_asset2 = st.sidebar.number_input("Initial Price Asset 2 ($)", min_value=0.0, value=1.0, step=0.01)
    current_price_asset1 = st.sidebar.number_input("Current Price Asset 1 ($)", min_value=0.0, value=1.2, step=0.01)
    current_price_asset2 = st.sidebar.number_input("Current Price Asset 2 ($)", min_value=0.0, value=0.8, step=0.01)
    initial_investment = st.sidebar.number_input("Initial Investment ($)", min_value=0.0, value=10_000.0, step=100.0)
    apy = st.sidebar.number_input("APY (%)", min_value=0.0, value=20.0, step=1.0)
    initial_tvl = st.sidebar.number_input("Initial TVL ($)", min_value=0.0, value=10_000_000.0, step=100_000.0)
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.0, value=9_000_000.0, step=100_000.0)
    volume_24h = st.sidebar.number_input("24-Hour Trading Volume ($)", min_value=0.0, value=1_000_000.0, step=100_000.0, help="Average of both tokens, source from Certik.com")
    twitter_followers = st.sidebar.number_input("Total Twitter Followers", min_value=0, value=526609, step=1000, help="Average of both tokens, source from Certik.com")
    total_tweets = st.sidebar.number_input("Total Tweets", min_value=0, value=1642, step=100, help="Average of both tokens, source from Certik.com")
    certik_trust_score = st.sidebar.number_input("Certik.com Trust Score (0-100, optional)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, help="Average of both tokens, source from Certik.com")
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, step=0.1)
    
    # Pool Analysis
    st.header("Existing Pool Analysis")
    
    # Base Calculations
    il_percentage = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
    pool_value = initial_investment + (initial_investment * (il_percentage / 100))
    aril = apy + il_percentage
    tvl_decline = ((current_tvl - initial_tvl) / initial_tvl) * 100
    
    # Hurdle Rate with Macro Adjustment
    base_hurdle_rate = risk_free_rate + 6.0
    hurdle_rate = base_hurdle_rate * macro_multiplier
    
    # Volatility Score
    il_factor = min(abs(il_percentage) / 5, 1.0)
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)
    volatility_score = (il_factor + tvl_factor) * 25 * macro_multiplier
    volatility_score = min(volatility_score, 100)
    
    # Protocol Risk Score
    apy_risk = (apy / 20) * 10
    tvl_decline_risk = (abs(tvl_decline) / 20) * 10 if tvl_decline < 0 else 0
    tvl_size_risk = (1e9 / current_tvl) * 10
    base_protocol_risk_score = apy_risk + tvl_decline_risk + tvl_size_risk
    contract_risk_score = 100 - certik_trust_score if certik_trust_score > 0 else 50
    liquidity_factor = (1e9 / volume_24h) * 10
    liquidity_factor = min(liquidity_factor, 1.0)
    protocol_risk_score = base_protocol_risk_score * (1 + (contract_risk_score / 100 - 0.5)) * (1 + liquidity_factor)
    protocol_risk_score = min(protocol_risk_score, 100)
    
    # Risk Category
    if protocol_risk_score < 25:
        risk_category = "Low"
        risk_color = "green"
        risk_message = "✅ Minimal risk due to a strong Certik Trust Score, stable TVL, and adequate yield."
    elif protocol_risk_score < 50:
        risk_category = "Advisory"
        risk_color = "yellow"
        risk_message = "⚠️ Moderate risk. Review the Certik Trust Score, TVL decline, and yield sustainability."
    elif protocol_risk_score < 75:
        risk_category = "High"
        risk_color = "orange"
        risk_message = "⚠️ High risk. Significant concerns with Certik Trust Score, TVL, or yield."
    else:
        risk_category = "Critical"
        risk_color = "red"
        risk_message = "🚨 Critical risk. Major issues with Certik Trust Score, TVL decline, or unsustainable yield."
    
    # Community Engagement Score
    follower_score = (twitter_followers / 1e6) * 50
    follower_score = min(follower_score, 100)
    tweet_score = (total_tweets / 10_000) * 50
    tweet_score = min(tweet_score, 100)
    community_engagement_score = (follower_score + tweet_score) / 2
    
    # Followers-to-Tweets Ratio
    followers_to_tweets_ratio = (total_tweets / twitter_followers) * 100 if twitter_followers > 0 else 0
    
    # Metric Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Investment Risk", risk_category, f"Protocol Risk Score: {protocol_risk_score:.2f}%", delta_color="off")
        st.markdown(f"<div style='background-color: {risk_color}; padding: 10px; border-radius: 5px; text-align: center;'>{risk_message}</div>", unsafe_allow_html=True)
        st.metric("Pool Value (Current)", f"${pool_value:,.2f}")
        st.metric("Impermanent Loss (%)", f"{il_percentage:.2f}%")
        st.metric("APY (%)", f"{apy:.2f}%")
        aril_color = "green" if aril > hurdle_rate else "red"
        st.metric("ARIL (%)", f"{aril:.2f}%", f"{'Above' if aril > hurdle_rate else 'Below'} Hurdle Rate ({hurdle_rate:.2f}%)", delta_color="off")
        st.markdown(f"<div style='background-color: {aril_color}; padding: 5px; border-radius: 5px; text-align: center;'>{aril:.2f}% ARIL</div>", unsafe_allow_html=True)
        tvl_color = "red" if tvl_decline < -20 else "orange" if tvl_decline < 0 else "green"
        st.metric("TVL Decline (%)", f"{tvl_decline:.2f}%")
        st.markdown(f"<div style='background-color: {tvl_color}; padding: 5px; border-radius: 5px; text-align: center;'>{tvl_decline:.2f}% TVL Change</div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Hurdle Rate", f"{hurdle_rate:.2f}%", f"Adjusted for {macro_environment} macro environment", delta_color="off")
        st.metric("Protocol Risk Score", f"{protocol_risk_score:.2f}%")
        st.metric("Volatility Score", f"{volatility_score:.2f}%")
        st.metric("Community Engagement Score", f"{community_engagement_score:.2f}%")
        ratio_label = "Low Activity" if followers_to_tweets_ratio < 0.1 else "Balanced Activity" if followers_to_tweets_ratio < 1 else "High Activity" if followers_to_tweets_ratio < 5 else "Very High Activity"
        ratio_color = "orange" if followers_to_tweets_ratio < 0.1 else "green" if followers_to_tweets_ratio < 1 else "yellow" if followers_to_tweets_ratio < 5 else "red"
        st.metric("Followers-to-Tweets Ratio", f"{followers_to_tweets_ratio:.2f}% ({ratio_label})", "Measures Twitter activity relative to followers", delta_color="off")
        st.markdown(f"<div style='background-color: {ratio_color}; padding: 5px; border-radius: 5px; text-align: center;'>{ratio_label}</div>", unsafe_allow_html=True)
    
    # Monte Carlo Analysis
    worst_case_value, expected_case_value, best_case_value = simplified_monte_carlo_pool_analysis(initial_price_asset1, initial_price_asset2, initial_investment, apy)
    
    # Seaborn Chart
    st.subheader("Pool Value Projection Over 12 Months")
    months = np.arange(0, 13)
    expected_values = [initial_investment + (initial_investment * (il_percentage / 100)) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    worst_case_values = [initial_investment * (worst_case_value / expected_case_value) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    best_case_values = [initial_investment * (best_case_value / expected_case_value) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=months, y=expected_values, label="Expected Value", color="blue", ax=ax)
    ax.fill_between(months, worst_case_values, best_case_values, color="gray", alpha=0.3, label="Monte Carlo Range (Worst to Best)")
    ax.set_xlabel("Months")
    ax.set_ylabel("Pool Value ($)")
    ax.set_title("Pool Value Projection Over 12 Months")
    ax.legend()
    st.pyplot(fig)
    
    # Monte Carlo Results Table
    monte_carlo_data = {
        "Scenario": ["Worst Case", "Expected Case", "Best Case"],
        "Pool Value ($)": [worst_case_value, expected_case_value, best_case_value],
        "Return (%)": [(worst_case_value / initial_investment - 1) * 100, (expected_case_value / initial_investment - 1) * 100, (best_case_value / initial_investment - 1) * 100]
    }
    st.table(monte_carlo_data)
    
    # Risk Summary
    st.subheader("Risk Summary")
    if protocol_risk_score > 50:
        st.markdown(f"⚠️ **Protocol Risk**: {risk_message}")
    else:
        st.markdown(f"✅ **Protocol Risk**: {risk_message}")
    if community_engagement_score > 50:
        st.markdown("✅ **Community Engagement**: High ({:.2f}%) indicates strong social presence, which may support pool stability.".format(community_engagement_score))
    else:
        st.markdown("⚠️ **Community Engagement**: Low ({:.2f}%) suggests limited social presence, which may impact adoption.".format(community_engagement_score))
    if followers_to_tweets_ratio < 0.1:
        st.markdown("⚠️ **Twitter Activity**: Low ({:.2f}%) suggests potential inactivity or fake followers.".format(followers_to_tweets_ratio))
    elif followers_to_tweets_ratio > 5:
        st.markdown("⚠️ **Twitter Activity**: Very High ({:.2f}%) may indicate excessive posting or spamming.".format(followers_to_tweets_ratio))
    else:
        st.markdown("✅ **Twitter Activity**: Balanced ({:.2f}%) suggests healthy engagement relative to the follower base.".format(followers_to_tweets_ratio))
    
    # CSV Export
    export_data = {
        "Investment Risk": [risk_category],
        "Protocol Risk Score (%)": [protocol_risk_score],
        "Pool Value ($)": [pool_value],
        "Impermanent Loss (%)": [il_percentage],
        "APY (%)": [apy],
        "ARIL (%)": [aril],
        "TVL Decline (%)": [tvl_decline],
        "Hurdle Rate (%)": [hurdle_rate],
        "Volatility Score (%)": [volatility_score],
        "24-Hour Volume ($)": [volume_24h],
        "Total Twitter Followers": [twitter_followers],
        "Total Tweets": [total_tweets],
        "Community Engagement Score (%)": [community_engagement_score],
        "Followers-to-Tweets Ratio (%)": [followers_to_tweets_ratio],
        "Certik Trust Score": [certik_trust_score],
        "Contract/Program Risk Score (%)": [contract_risk_score]
    }
    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False)
    st.download_button("Download Analysis as CSV", csv, "pool_analysis.csv", "text/csv")

elif analysis_type == "New Pool":
    st.sidebar.header("New Pool Inputs")
    current_price_asset1 = st.sidebar.number_input("Current Price Asset 1 ($)", min_value=0.0, value=1.0, step=0.01)
    current_price_asset2 = st.sidebar.number_input("Current Price Asset 2 ($)", min_value=0.0, value=1.0, step=0.01)
    initial_investment = st.sidebar.number_input("Initial Investment ($)", min_value=0.0, value=10_000.0, step=100.0)
    expected_price_change_asset1 = st.sidebar.number_input("Expected Price Change Asset 1 (%)", value=20.0, step=1.0)
    expected_price_change_asset2 = st.sidebar.number_input("Expected Price Change Asset 2 (%)", value=-10.0, step=1.0)
    apy = st.sidebar.number_input("APY (%)", min_value=0.0, value=20.0, step=1.0)
    current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.0, value=10_000_000.0, step=100_000.0)
    volume_24h = st.sidebar.number_input("24-Hour Trading Volume ($)", min_value=0.0, value=1_000_000.0, step=100_000.0, help="Average of both tokens, source from Certik.com")
    twitter_followers = st.sidebar.number_input("Total Twitter Followers", min_value=0, value=526609, step=1000, help="Average of both tokens, source from Certik.com")
    total_tweets = st.sidebar.number_input("Total Tweets", min_value=0, value=1642, step=100, help="Average of both tokens, source from Certik.com")
    certik_trust_score = st.sidebar.number_input("Certik.com Trust Score (0-100, optional)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, help="Average of both tokens, source from Certik.com")
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, step=0.1)
    
    # Pool Analysis
    st.header("New Pool Analysis")
    
    # Base Calculations
    projected_price_asset1 = current_price_asset1 * (1 + expected_price_change_asset1 / 100)
    projected_price_asset2 = current_price_asset2 * (1 + expected_price_change_asset2 / 100)
    il_percentage = calculate_il(current_price_asset1, current_price_asset2, projected_price_asset1, projected_price_asset2, initial_investment)
    pool_value = initial_investment + (initial_investment * (il_percentage / 100))
    aril = apy + il_percentage
    
    # Hurdle Rate with Macro Adjustment
    base_hurdle_rate = risk_free_rate + 6.0
    hurdle_rate = base_hurdle_rate * macro_multiplier
    
    # Volatility Score
    il_factor = min(abs(il_percentage) / 5, 1.0)
    volatility_score = il_factor * 50 * macro_multiplier
    volatility_score = min(volatility_score, 100)
    
    # Protocol Risk Score
    apy_risk = (apy / 20) * 10
    tvl_size_risk = (1e9 / current_tvl) * 10
    base_protocol_risk_score = apy_risk + tvl_size_risk
    contract_risk_score = 100 - certik_trust_score if certik_trust_score > 0 else 50
    liquidity_factor = (1e9 / volume_24h) * 10
    liquidity_factor = min(liquidity_factor, 1.0)
    protocol_risk_score = base_protocol_risk_score * (1 + (contract_risk_score / 100 - 0.5)) * (1 + liquidity_factor)
    protocol_risk_score = min(protocol_risk_score, 100)
    
    # Risk Category
    if protocol_risk_score < 25:
        risk_category = "Low"
        risk_color = "green"
        risk_message = "✅ Minimal risk due to a strong Certik Trust Score and adequate yield."
    elif protocol_risk_score < 50:
        risk_category = "Advisory"
        risk_color = "yellow"
        risk_message = "⚠️ Moderate risk. Review the Certik Trust Score and yield sustainability."
    elif protocol_risk_score < 75:
        risk_category = "High"
        risk_color = "orange"
        risk_message = "⚠️ High risk. Significant concerns with Certik Trust Score or yield."
    else:
        risk_category = "Critical"
        risk_color = "red"
        risk_message = "🚨 Critical risk. Major issues with Certik Trust Score or unsustainable yield."
    
    # Community Engagement Score
    follower_score = (twitter_followers / 1e6) * 50
    follower_score = min(follower_score, 100)
    tweet_score = (total_tweets / 10_000) * 50
    tweet_score = min(tweet_score, 100)
    community_engagement_score = (follower_score + tweet_score) / 2
    
    # Followers-to-Tweets Ratio
    followers_to_tweets_ratio = (total_tweets / twitter_followers) * 100 if twitter_followers > 0 else 0
    
    # Metric Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Investment Risk", risk_category, f"Protocol Risk Score: {protocol_risk_score:.2f}%", delta_color="off")
        st.markdown(f"<div style='background-color: {risk_color}; padding: 10px; border-radius: 5px; text-align: center;'>{risk_message}</div>", unsafe_allow_html=True)
        st.metric("Projected Pool Value (12 Months)", f"${pool_value:,.2f}")
        st.metric("Projected Impermanent Loss (%)", f"{il_percentage:.2f}%")
        st.metric("APY (%)", f"{apy:.2f}%")
        aril_color = "green" if aril > hurdle_rate else "red"
        st.metric("ARIL (%)", f"{aril:.2f}%", f"{'Above' if aril > hurdle_rate else 'Below'} Hurdle Rate ({hurdle_rate:.2f}%)", delta_color="off")
        st.markdown(f"<div style='background-color: {aril_color}; padding: 5px; border-radius: 5px; text-align: center;'>{aril:.2f}% ARIL</div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Hurdle Rate", f"{hurdle_rate:.2f}%", f"Adjusted for {macro_environment} macro environment", delta_color="off")
        st.metric("Protocol Risk Score", f"{protocol_risk_score:.2f}%")
        st.metric("Volatility Score", f"{volatility_score:.2f}%")
        st.metric("Community Engagement Score", f"{community_engagement_score:.2f}%")
        ratio_label = "Low Activity" if followers_to_tweets_ratio < 0.1 else "Balanced Activity" if followers_to_tweets_ratio < 1 else "High Activity" if followers_to_tweets_ratio < 5 else "Very High Activity"
        ratio_color = "orange" if followers_to_tweets_ratio < 0.1 else "green" if followers_to_tweets_ratio < 1 else "yellow" if followers_to_tweets_ratio < 5 else "red"
        st.metric("Followers-to-Tweets Ratio", f"{followers_to_tweets_ratio:.2f}% ({ratio_label})", "Measures Twitter activity relative to followers", delta_color="off")
        st.markdown(f"<div style='background-color: {ratio_color}; padding: 5px; border-radius: 5px; text-align: center;'>{ratio_label}</div>", unsafe_allow_html=True)
    
    # Monte Carlo Analysis
    worst_case_value, expected_case_value, best_case_value = simplified_monte_carlo_pool_analysis(current_price_asset1, current_price_asset2, initial_investment, apy)
    
    # Seaborn Chart
    st.subheader("Pool Value Projection Over 12 Months")
    months = np.arange(0, 13)
    expected_values = [initial_investment + (initial_investment * (il_percentage / 100)) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    worst_case_values = [initial_investment * (worst_case_value / expected_case_value) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    best_case_values = [initial_investment * (best_case_value / expected_case_value) + (initial_investment * (apy / 100) * (t / 12)) for t in months]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=months, y=expected_values, label="Expected Value", color="blue", ax=ax)
    ax.fill_between(months, worst_case_values, best_case_values, color="gray", alpha=0.3, label="Monte Carlo Range (Worst to Best)")
    ax.set_xlabel("Months")
    ax.set_ylabel("Pool Value ($)")
    ax.set_title("Pool Value Projection Over 12 Months")
    ax.legend()
    st.pyplot(fig)
    
    # Monte Carlo Results Table
    monte_carlo_data = {
        "Scenario": ["Worst Case", "Expected Case", "Best Case"],
        "Pool Value ($)": [worst_case_value, expected_case_value, best_case_value],
        "Return (%)": [(worst_case_value / initial_investment - 1) * 100, (expected_case_value / initial_investment - 1) * 100, (best_case_value / initial_investment - 1) * 100]
    }
    st.table(monte_carlo_data)
    
    # Risk Summary
    st.subheader("Risk Summary")
    if protocol_risk_score > 50:
        st.markdown(f"⚠️ **Protocol Risk**: {risk_message}")
    else:
        st.markdown(f"✅ **Protocol Risk**: {risk_message}")
    if community_engagement_score > 50:
        st.markdown("✅ **Community Engagement**: High ({:.2f}%) indicates strong social presence, which may support pool stability.".format(community_engagement_score))
    else:
        st.markdown("⚠️ **Community Engagement**: Low ({:.2f}%) suggests limited social presence, which may impact adoption.".format(community_engagement_score))
    if followers_to_tweets_ratio < 0.1:
        st.markdown("⚠️ **Twitter Activity**: Low ({:.2f}%) suggests potential inactivity or fake followers.".format(followers_to_tweets_ratio))
    elif followers_to_tweets_ratio > 5:
        st.markdown("⚠️ **Twitter Activity**: Very High ({:.2f}%) may indicate excessive posting or spamming.".format(followers_to_tweets_ratio))
    else:
        st.markdown("✅ **Twitter Activity**: Balanced ({:.2f}%) suggests healthy engagement relative to the follower base.".format(followers_to_tweets_ratio))
    
    # CSV Export
    export_data = {
        "Investment Risk": [risk_category],
        "Protocol Risk Score (%)": [protocol_risk_score],
        "Projected Pool Value ($)": [pool_value],
        "Projected Impermanent Loss (%)": [il_percentage],
        "APY (%)": [apy],
        "ARIL (%)": [aril],
        "Hurdle Rate (%)": [hurdle_rate],
        "Volatility Score (%)": [volatility_score],
        "24-Hour Volume ($)": [volume_24h],
        "Total Twitter Followers": [twitter_followers],
        "Total Tweets": [total_tweets],
        "Community Engagement Score (%)": [community_engagement_score],
        "Followers-to-Tweets Ratio (%)": [followers_to_tweets_ratio],
        "Certik Trust Score": [certik_trust_score],
        "Contract/Program Risk Score (%)": [contract_risk_score]
    }
    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False)
    st.download_button("Download Analysis as CSV", csv, "new_pool_analysis.csv", "text/csv")
