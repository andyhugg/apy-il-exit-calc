import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom CSS for shading insights and alerts
st.markdown("""
    <style>
    .red-background {
        background-color: #ffcccc;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .yellow-background {
        background-color: #fff4cc;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .green-background {
        background-color: #ccffcc;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar inputs
st.sidebar.header("Input Parameters")

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=84000.0)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=35.0)
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=1000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=60000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate %", min_value=-100.0, value=15.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=10.0)
volatility = st.sidebar.number_input("Expected Monthly Volatility %", min_value=0.0, value=3.0) / 100  # Convert to decimal
time_horizon = st.sidebar.number_input("Time Horizon (Months)", min_value=1, value=12)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Calculations
    months = time_horizon
    asset_monthly_rate = (1 + growth_rate/100) ** (1/months) - 1
    btc_monthly_rate = (1 + btc_growth/100) ** (1/months) - 1
    rf_monthly_rate = (1 + risk_free_rate/100) ** (1/months) - 1
    
    # Standard price projections (without volatility) for the chart
    asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
    btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
    rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
    
    # Monte Carlo Simulation (capped at the user-input growth rate)
    n_simulations = 200
    simulations = []
    max_allowed_value = initial_investment * (1 + growth_rate/100)  # Cap at user-input growth rate
    
    np.random.seed(42)  # For reproducibility
    for _ in range(n_simulations):
        sim_prices = [initial_investment]
        for i in range(months):
            monthly_return = np.random.normal(asset_monthly_rate, volatility)
            sim_prices.append(sim_prices[-1] * (1 + monthly_return))
        final_value = min(sim_prices[-1], max_allowed_value)  # Cap the final value
        simulations.append(final_value)
    
    best_case = max(simulations)
    worst_case = min(simulations)
    expected_case = np.mean(simulations)
    
    # Calculate additional metrics
    # Volatility (annualized)
    monthly_returns = [(simulations[i] / initial_investment) ** (1/months) - 1 for i in range(len(simulations))]
    annualized_volatility = np.std(monthly_returns) * np.sqrt(12) * 100  # Annualized volatility in %

    # Sharpe Ratio (risk-adjusted return)
    asset_return = (expected_case / initial_investment - 1) * 100  # Expected return in %
    excess_return = asset_return - risk_free_rate
    sharpe_ratio = excess_return / annualized_volatility if annualized_volatility != 0 else 0

    # Probability of Loss
    prob_loss = sum(1 for sim in simulations if sim < initial_investment) / len(simulations) * 100

    # Annualized Asset ROI (for hurdle rate comparison)
    asset_roi = ((initial_investment * asset_projections[-1] / asset_price) / initial_investment - 1) * 100
    annualized_asset_roi = ((1 + asset_roi/100) ** (12/months) - 1) * 100 if months != 0 else asset_roi

    # Hurdle Rates
    inflation_rate = 6.0  # Global average inflation rate
    hurdle_rate_rf = risk_free_rate  # Risk-free rate as hurdle rate

    # Investment Value After Price Drops
    price_after_20 = asset_price * (1 - 0.2)
    price_after_50 = asset_price * (1 - 0.5)
    price_after_90 = asset_price * (1 - 0.9)
    
    investment_after_20 = initial_investment * (price_after_20 / asset_price)
    investment_after_50 = initial_investment * (price_after_50 / asset_price)
    investment_after_90 = initial_investment * (price_after_90 / asset_price)

    # Breakeven requirements
    def breakeven_requirement(drop):
        if drop == 0:
            return 0
        return (drop / (100 - drop)) * 100

    breakeven_20 = breakeven_requirement(20)
    breakeven_50 = breakeven_requirement(50)
    breakeven_90 = breakeven_requirement(90)

    # Display results in tiles
    st.subheader("Key Metrics")
    st.markdown("These metrics show the projected price, investment value, and risk-adjusted return of the asset.")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Projected Asset Price", 
                 f"${asset_projections[-1]:,.2f}",
                 f"{growth_rate}%")
        
    with col2:
        st.metric("Investment Value",
                 f"${(initial_investment * asset_projections[-1] / asset_price):,.2f}",
                 f"${(initial_investment * asset_projections[-1] / asset_price) - initial_investment:,.2f}")
    
    with col3:
        st.metric("Sharpe Ratio",
                 f"{sharpe_ratio:.2f}")

    st.divider()

    # Price Projections Chart
    st.subheader("Asset Price Projections")
    st.markdown("This chart shows how the asset’s price might grow over time compared to Bitcoin and stablecoins, helping you see potential returns.")
    df_proj = pd.DataFrame({
        'Month': range(months + 1),
        'Asset Price': asset_projections,
        'Bitcoin Price': btc_projections,
        'Stablecoin Value': rf_projections
    })
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_proj, x='Month', y='Asset Price', label='Asset')
    sns.lineplot(data=df_proj, x='Month', y='Bitcoin Price', label='Bitcoin')
    sns.lineplot(data=df_proj, x='Month', y='Stablecoin Value', label='Stablecoin')
    plt.title(f'Price Projections Over {months} Months')
    plt.legend()
    st.pyplot(plt)
    plt.clf()

    st.divider()

    # Additional Metrics
    st.subheader("Risk and Performance Metrics")
    st.markdown("These metrics help you understand the asset’s risk (volatility), likelihood of loss, and how it compares to Bitcoin’s historical performance.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Annualized Volatility", f"{annualized_volatility:.2f}%")
    with col2:
        st.metric("Probability of Loss", f"{prob_loss:.2f}%")
    with col3:
        historical_btc_return = 50  # Historical average annualized return for Bitcoin (simplified)
        st.metric("Historical BTC Return", f"{historical_btc_return}%")

    st.divider()

    # Hurdle Rate Comparison
    st.subheader("Performance vs. Hurdle Rates")
    st.markdown("This section compares the asset’s return to the risk-free rate and inflation, ensuring it meets minimum performance goals.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Annualized Asset ROI", f"{annualized_asset_roi:.2f}%")
    with col2:
        st.metric("Hurdle Rate (Risk-Free)", f"{hurdle_rate_rf:.2f}%")
    with col3:
        st.metric("Hurdle Rate (Inflation)", f"{inflation_rate:.2f}%")

    st.divider()

    # Investment Value After Price Drops
    st.subheader("Investment Value After Price Drops")
    st.markdown("This table shows how much your investment would be worth if the asset’s price drops by 20%, 50%, or 90%, and the growth needed to recover.")
    mdd_data = {
        "Price Drop (%)": ["20%", "50%", "90%"],
        "Asset Price After Drop ($)": [f"${price_after_20:,.2f}", f"${price_after_50:,.2f}", f"${price_after_90:,.2f}"],
        "Investment Value After Drop ($)": [f"${investment_after_20:,.2f}", f"${investment_after_50:,.2f}", f"${investment_after_90:,.2f}"],
        "Breakeven Requirement (%)": [f"{breakeven_20:.2f}%", f"{breakeven_50:.2f}%", f"{breakeven_90:.2f}%"]
    }
    mdd_df = pd.DataFrame(mdd_data)
    st.table(mdd_df)

    st.divider()

    # Comparison Section
    st.subheader("Comparison vs BTC and Stablecoin")
    st.markdown("This section compares the asset’s return to Bitcoin and stablecoin returns, helping you decide where to invest.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Asset ROI", f"{asset_roi:.2f}%")
    with col2:
        btc_roi = ((btc_projections[-1] / btc_price) - 1) * 100
        st.metric("BTC ROI", f"{btc_roi:.2f}%")
    with col3:
        rf_roi = ((rf_projections[-1] / initial_investment) - 1) * 100
        st.metric("Stablecoin ROI", f"{rf_roi:.2f}%")

    st.divider()

    # Monte Carlo Results
    st.subheader("Monte Carlo Analysis (200 Scenarios)")
    st.markdown("This section shows the best, worst, and expected outcomes for your investment based on 200 simulations, giving you a range of possibilities.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Case", f"${best_case:,.2f}")
    with col2:
        st.metric("Worst Case", f"${worst_case:,.2f}")
    with col3:
        st.metric("Expected Case", f"${expected_case:,.2f}")

    st.divider()

    # Monte Carlo Distribution
    st.subheader("Distribution of Possible Outcomes")
    st.markdown("This chart shows the range of possible investment values after the time horizon, helping you understand the likelihood of different outcomes.")
    plt.figure(figsize=(10, 6))
    sns.histplot(simulations, bins=50)
    plt.axvline(initial_investment, color='red', linestyle='--', label='Initial Investment')
    plt.title("Distribution of Possible Outcomes")
    plt.xlabel("Final Value ($)")
    plt.legend()
    st.pyplot(plt)
    plt.clf()

    st.divider()

    # Outcome Probabilities
    st.subheader("Outcome Probabilities")
    st.markdown("This chart shows the chances of losing money, breaking even, or making a profit, based on the simulations.")
    prob_profit = sum(1 for sim in simulations if sim > initial_investment) / len(simulations) * 100
    prob_breakeven = sum(1 for sim in simulations if initial_investment * 0.95 <= sim <= initial_investment * 1.05) / len(simulations) * 100
    prob_loss = sum(1 for sim in simulations if sim < initial_investment) / len(simulations) * 100

    outcome_data = pd.DataFrame({
        "Outcome": ["Loss", "Break-even", "Profit"],
        "Probability (%)": [prob_loss, prob_breakeven, prob_profit]
    })
    plt.figure(figsize=(8, 4))
    sns.barplot(data=outcome_data, x="Probability (%)", y="Outcome", hue="Outcome", palette="coolwarm")
    plt.title("Probability of Different Outcomes")
    st.pyplot(plt)
    plt.clf()

    st.divider()

    # Actionable Insights and Alerts
    st.subheader("Actionable Insights and Alerts")
    st.markdown("This section provides recommendations and warnings based on the analysis, helping you make informed decisions.")

    # Insight 1: Risk-Adjusted Return
    if sharpe_ratio > 1:
        st.markdown('<div class="green-background">✓ <b>Good Risk-Adjusted Return</b>: Sharpe Ratio > 1, indicating the asset\'s return justifies its risk.</div>', unsafe_allow_html=True)
    elif sharpe_ratio > 0:
        st.markdown('<div class="yellow-background">⚠ <b>Moderate Risk-Adjusted Return</b>: Sharpe Ratio between 0 and 1. Consider if the risk is worth the reward.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="red-background">⚠ <b>Poor Risk-Adjusted Return</b>: Sharpe Ratio < 0. The asset\'s return does not justify its risk.</div>', unsafe_allow_html=True)

    # Insight 2: Portfolio Allocation Suggestion
    total_roi = asset_roi + btc_roi + rf_roi
    if total_roi != 0:
        asset_weight = (asset_roi / total_roi) * 100
        btc_weight = (btc_roi / total_roi) * 100
        rf_weight = (rf_roi / total_roi) * 100
        st.markdown(f'<div class="green-background"><b>Portfolio Allocation Suggestion</b>: Based on projected returns, consider allocating {asset_weight:.1f}% to the asset, {btc_weight:.1f}% to Bitcoin, and {rf_weight:.1f}% to stablecoins.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="red-background">⚠ <b>Portfolio Allocation</b>: Unable to suggest allocation due to zero or negative returns.</div>', unsafe_allow_html=True)

    # Alert 1: High Volatility
    if worst_case < expected_case * 0.5:
        st.markdown('<div class="red-background">⚠ <b>High Volatility Alert</b>: The worst-case scenario is less than 50% of the expected case, indicating high risk.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="green-background">✓ <b>Volatility Check</b>: The worst-case scenario is within acceptable bounds relative to the expected case.</div>', unsafe_allow_html=True)

    # Alert 2: Underperformance
    if asset_roi < btc_roi and asset_roi < rf_roi:
        st.markdown('<div class="red-background">⚠ <b>Underperformance Alert</b>: The asset\'s projected ROI is lower than both Bitcoin and stablecoin returns. Consider alternative investments.</div>', unsafe_allow_html=True)
    elif asset_roi < btc_roi:
        st.markdown('<div class="yellow-background">⚠ <b>Underperformance Alert</b>: The asset may underperform Bitcoin. Consider allocating more to BTC.</div>', unsafe_allow_html=True)
    elif asset_roi < rf_roi:
        st.markdown('<div class="yellow-background">⚠ <b>Underperformance Alert</b>: The asset may underperform stablecoin returns. Consider a safer investment.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="green-background">✓ <b>Performance Check</b>: The asset\'s projected ROI exceeds both Bitcoin and stablecoin returns.</div>', unsafe_allow_html=True)

    # Alert 3: Comparison to Historical Returns
    historical_btc_return = 50  # Simplified historical average
    if growth_rate > historical_btc_return * 1.5:
        st.markdown('<div class="yellow-background">⚠ <b>Optimistic Growth Alert</b>: Your expected growth rate is significantly higher than Bitcoin\'s historical average (50%). Ensure this is realistic.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="green-background">✓ <b>Growth Expectation Check</b>: Your expected growth rate is within a realistic range compared to Bitcoin\'s historical average (50%).</div>', unsafe_allow_html=True)

    # Alert 4: Hurdle Rate Comparison
    if annualized_asset_roi < inflation_rate:
        st.markdown(f'<div class="red-background">⚠ <b>Hurdle Rate Alert</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) is below the global inflation rate ({inflation_rate:.2f}%). Your investment may lose purchasing power.</div>', unsafe_allow_html=True)
    elif annualized_asset_roi < hurdle_rate_rf:
        st.markdown(f'<div class="yellow-background">⚠ <b>Hurdle Rate Alert</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) beats inflation ({inflation_rate:.2f}%) but is below the risk-free rate ({hurdle_rate_rf:.2f}%). Consider if the risk is worth it.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="green-background">✓ <b>Hurdle Rate Check</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) exceeds both the risk-free rate ({hurdle_rate_rf:.2f}%) and inflation ({inflation_rate:.2f}%).</div>', unsafe_allow_html=True)
