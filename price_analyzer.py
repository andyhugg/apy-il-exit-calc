import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom CSS for styling alerts, tables, and headers
st.markdown("""
    <style>
    .red-background {
        background-color: #ff6666;  /* Darker red for better contrast */
        color: white;  /* White text for readability */
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .yellow-background {
        background-color: #ffcc66;  /* Deeper yellow for better readability */
        color: black;  /* Black text for contrast */
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .green-background {
        background-color: #66cc66;  /* Brighter green for clarity */
        color: white;  /* White text for readability */
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .alert-box {
        border: 2px solid;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-size: 18px;
        font-weight: bold;
    }
    /* Style for headers */
    h2 {
        font-size: 24px !important;
        color: #333 !important;
        border-bottom: 2px solid #4CAF50 !important;
        padding-bottom: 10px !important;
    }
    /* Style for tables */
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stDataFrame table {
        width: 100%;
    }
    .stDataFrame th {
        font-weight: bold;
        background-color: #f0f0f0;
        padding: 8px;
    }
    .stDataFrame td {
        padding: 8px;
    }
    .stDataFrame tr:nth-child(odd) {
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar inputs with tooltips
st.sidebar.header("Input Parameters")

# Default values
default_values = {
    "asset_price": 0.02,
    "growth_rate": 50.0,
    "initial_investment": 1000.0,
    "btc_price": 84000.0,
    "btc_growth": 15.0,
    "risk_free_rate": 10.0,
    "volatility": 25.0,
    "time_horizon": 12,
    "market_cap_selection": "Less than $100M (Ultra High Risk)",
    "investor_profile": "Bitcoin Strategy"
}

# Initialize session state for inputs
if "inputs" not in st.session_state:
    st.session_state.inputs = default_values.copy()

# Reset button
if st.sidebar.button("Reset Inputs"):
    st.session_state.inputs = default_values.copy()
    st.rerun()

# Inputs with tooltips
asset_price = st.sidebar.number_input(
    "Current Asset Price ($)",
    min_value=0.0,
    value=st.session_state.inputs["asset_price"],
    help="The current price of the asset you’re analyzing."
)
st.session_state.inputs["asset_price"] = asset_price

growth_rate = st.sidebar.number_input(
    "Expected Growth Rate % (Annual)",
    min_value=-100.0,
    value=st.session_state.inputs["growth_rate"],
    help="The annual growth rate you expect for the asset. Higher values increase projected returns but may be less realistic."
)
st.session_state.inputs["growth_rate"] = growth_rate

initial_investment = st.sidebar.number_input(
    "Initial Investment Amount ($)",
    min_value=0.0,
    value=st.session_state.inputs["initial_investment"],
    help="The amount you plan to invest in the asset."
)
st.session_state.inputs["initial_investment"] = initial_investment

btc_price = st.sidebar.number_input(
    "Current Bitcoin Price ($)",
    min_value=0.0,
    value=st.session_state.inputs["btc_price"],
    help="The current price of Bitcoin for comparison."
)
st.session_state.inputs["btc_price"] = btc_price

btc_growth = st.sidebar.number_input(
    "Bitcoin Expected Growth Rate %",
    min_value=-100.0,
    value=st.session_state.inputs["btc_growth"],
    help="The annual growth rate you expect for Bitcoin."
)
st.session_state.inputs["btc_growth"] = btc_growth

risk_free_rate = st.sidebar.number_input(
    "Risk-Free Rate % (Stablecoin Pool)",
    min_value=0.0,
    value=st.session_state.inputs["risk_free_rate"],
    help="The expected return from a stablecoin pool, representing a risk-free rate."
)
st.session_state.inputs["risk_free_rate"] = risk_free_rate

volatility = st.sidebar.number_input(
    "Expected Monthly Volatility %",
    min_value=0.0,
    value=st.session_state.inputs["volatility"],
    help="The expected monthly volatility of the asset’s price, as a percentage."
) / 100  # Convert to decimal
st.session_state.inputs["volatility"] = volatility * 100

time_horizon = st.sidebar.number_input(
    "Time Horizon (Months)",
    min_value=1,
    value=int(st.session_state.inputs["time_horizon"]),
    help="The number of months over which to project the asset’s performance."
)
st.session_state.inputs["time_horizon"] = time_horizon

# Market Cap Selector
market_cap_options = [
    "Less than $100M (Ultra High Risk)",
    "$100M to $500M (Very High Risk)",
    "$500M to $1B (High Risk)",
    "$1B to $5B (Moderate Risk)",
    "$5B to $10B (Low Risk)",
    "$10B or more (Very Low Risk)"
]
market_cap_selection = st.sidebar.selectbox(
    "Market Cap Range",
    market_cap_options,
    index=market_cap_options.index(st.session_state.inputs["market_cap_selection"]),
    help="The market cap range of the asset, which affects its risk level."
)
st.session_state.inputs["market_cap_selection"] = market_cap_selection

# Map selection to a market cap value (in billions) for risk score calculation
market_cap_mapping = {
    "Less than $100M (Ultra High Risk)": 0.05,  # Midpoint of range
    "$100M to $500M (Very High Risk)": 0.3,
    "$500M to $1B (High Risk)": 0.75,
    "$1B to $5B (Moderate Risk)": 3.0,
    "$5B to $10B (Low Risk)": 7.5,
    "$10B or more (Very Low Risk)": 15.0
}
market_cap = market_cap_mapping[market_cap_selection]

# Investor Profile Selector
investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Growth Investor", "Conservative Investor", "Aggressive Investor", "Bitcoin Strategy"],
    index=["Growth Investor", "Conservative Investor", "Aggressive Investor", "Bitcoin Strategy"].index(st.session_state.inputs["investor_profile"]),
    help="Your investor profile, which determines the suggested portfolio allocation."
)
st.session_state.inputs["investor_profile"] = investor_profile

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Market Cap Risk Score
    def calculate_market_cap_risk_score(mcap):
        if mcap < 0.1:
            return 10  # Ultra High Risk
        elif mcap < 0.5:
            return 8   # Very High Risk
        elif mcap < 1.0:
            return 6   # High Risk
        elif mcap < 5.0:
            return 4   # Moderate Risk
        elif mcap < 10.0:
            return 2   # Low Risk
        else:
            return 1   # Very Low Risk

    market_cap_risk_score = calculate_market_cap_risk_score(market_cap)

    # Calculations
    months = time_horizon
    
    # Annual growth rate applied over the time horizon (simplified for bar chart)
    asset_end_price = asset_price * (1 + growth_rate/100) ** (months/12)
    btc_end_price = btc_price * (1 + btc_growth/100) ** (months/12)
    rf_end_value = initial_investment * (1 + risk_free_rate/100) ** (months/12)
    
    # Monte Carlo Simulation (capped at the user-input growth rate)
    asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1  # Convert annual rate to monthly
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
    
    # Calculate 95% Confidence Interval for Monte Carlo
    ci_lower = np.percentile(simulations, 2.5)
    ci_upper = np.percentile(simulations, 97.5)
    
    # Calculate additional metrics
    monthly_returns = [(simulations[i] / initial_investment) ** (1/months) - 1 for i in range(len(simulations))]
    annualized_volatility = np.std(monthly_returns) * np.sqrt(12) * 100  # Annualized volatility in %

    # Sharpe Ratio (risk-adjusted return)
    asset_return = (expected_case / initial_investment - 1) * 100  # Expected return in %
    excess_return = asset_return - risk_free_rate
    sharpe_ratio = excess_return / annualized_volatility if annualized_volatility != 0 else 0

    # Probability of Loss
    prob_loss = sum(1 for sim in simulations if sim < initial_investment) / len(simulations) * 100

    # Annualized Asset ROI (for hurdle rate comparison)
    asset_roi = ((initial_investment * asset_end_price / asset_price) / initial_investment - 1) * 100
    annualized_asset_roi = ((1 + asset_roi/100) ** (12/months) - 1) * 100 if months != 0 else asset_roi

    # Composite Risk Score
    mcap_risk = market_cap_risk_score  # Already on 1-10 scale
    vol_risk = min(annualized_volatility / 50 * 10, 10)  # Scale 0-50% to 0-10
    loss_risk = prob_loss / 10  # Scale 0-100% to 0-10
    composite_risk_score = (mcap_risk + vol_risk + loss_risk) / 3

    # Classify risk level
    if composite_risk_score > 6:
        risk_level = "High Risk"
        risk_color = "red-background"
        risk_insight = "Consider diversifying your portfolio or reducing exposure to this asset to manage risk."
    elif composite_risk_score > 3:
        risk_level = "Medium Risk"
        risk_color = "yellow-background"
        risk_insight = "Monitor this asset closely and consider balancing with safer investments like stablecoins."
    else:
        risk_level = "Low Risk"
        risk_color = "green-background"
        risk_insight = "This asset appears to have manageable risk; you may consider increasing exposure if aligned with your goals."

    # Composite Risk Score Alert (Prominent at the Top)
    st.markdown(f'<div class="alert-box {risk_color}">⚠ <b>Composite Risk Score: {composite_risk_score:.1f} ({risk_level})</b><br>{risk_insight}</div>', unsafe_allow_html=True)
    st.markdown("This alert combines market cap risk, volatility, and probability of loss to assess the overall risk of investing in this asset.")

    # Risk Score Breakdown
    with st.expander("Risk Score Breakdown"):
        st.write(f"- **Market Cap Risk**: {mcap_risk}/10")
        st.write(f"- **Volatility Risk**: {vol_risk:.1f}/10")
        st.write(f"- **Loss Risk**: {loss_risk:.1f}/10")

    # Summary Dashboard
    st.subheader("Summary Dashboard")
    st.markdown("A quick overview of the most important metrics for your investment.")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Projected Investment Value", f"${(initial_investment * asset_end_price / asset_price):,.2f}")
    with col2:
        st.metric("Annualized ROI", f"{annualized_asset_roi:.2f}%")
    with col3:
        st.metric("Composite Risk Score", f"{composite_risk_score:.1f}")
    with col4:
        st.metric("Probability of Loss", f"{prob_loss:.2f}%")

    st.divider()

    # Display results in tiles
    st.subheader("Key Metrics")
    st.markdown("These metrics show the projected price, investment value, and risk-adjusted return of the asset.")
    st.markdown("**Note on Sharpe Ratio**: The Sharpe Ratio shows how much return you’re getting for the risk you’re taking. A higher number (e.g., above 1) means better returns for the risk, while a low or negative number means the risk might not be worth it.")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Projected Asset Price", 
                 f"${asset_end_price:,.2f}",
                 f"{growth_rate}%")
        
    with col2:
        st.metric("Investment Value",
                 f"${(initial_investment * asset_end_price / asset_price):,.2f}",
                 f"${(initial_investment * asset_end_price / asset_price) - initial_investment:,.2f}")
    
    with col3:
        st.metric("Sharpe Ratio",
                 f"{sharpe_ratio:.2f}")

    st.divider()

    # Price Projections Bar Chart
    st.subheader("Asset Price Projections")
    st.markdown("These bar charts show the starting and ending values for the asset, Bitcoin, and stablecoin over the time horizon, helping you see potential returns.")

    # First bar chart: Asset and Stablecoin (smaller values)
    st.markdown("**Asset and Stablecoin Values**")
    bar_data_small = pd.DataFrame({
        "Category": ["Asset (Start)", "Asset (End)", "Stablecoin (Start)", "Stablecoin (End)"],
        "Value": [asset_price, asset_end_price, initial_investment, rf_end_value],
        "Type": ["Asset", "Asset", "Stablecoin", "Stablecoin"]
    })
    plt.figure(figsize=(8, 5))
    sns.barplot(data=bar_data_small, x="Category", y="Value", hue="Type", palette={"Asset": "blue", "Stablecoin": "green"})
    plt.title(f"Asset and Stablecoin Values Over {months} Months")
    plt.ylabel("Value ($)")
    plt.xticks(rotation=45)
    st.pyplot(plt)
    plt.clf()

    # Second bar chart: Bitcoin (larger values)
    st.markdown("**Bitcoin Values**")
    bar_data_large = pd.DataFrame({
        "Category": ["Bitcoin (Start)", "Bitcoin (End)"],
        "Value": [btc_price, btc_end_price],
        "Type": ["Bitcoin", "Bitcoin"]
    })
    plt.figure(figsize=(5, 5))
    sns.barplot(data=bar_data_large, x="Category", y="Value", hue="Type", palette={"Bitcoin": "orange"})
    plt.title(f"Bitcoin Values Over {months} Months")
    plt.ylabel("Value ($)")
    plt.xticks(rotation=45)
    st.pyplot(plt)
    plt.clf()

    st.divider()

    # Additional Metrics
    st.subheader("Risk and Performance Metrics")
    st.markdown("These metrics help you understand the asset’s risk (volatility), likelihood of loss, and how it compares to Bitcoin’s historical performance.")
    st.markdown("**Note on Probability of Loss**: The Probability of Loss shows the chance your investment could lose money, based on 200 simulations. It’s important because it helps you understand the risk of not getting your money back.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Annualized Volatility", f"{annualized_volatility:.2f}%")
    with col2:
        st.metric("Probability of Loss", f"{prob_loss:.2f}%")
    with col3:
        historical_btc_return = 50  # Historical average annualized return for Bitcoin (simplified)
        st.metric("Historical BTC Return", f"{historical_btc_return}%")

    st.divider()

    # Investment Value After Price Drops
    st.subheader("Investment Value After Price Drops")
    st.markdown("This table shows how much your investment would be worth if the asset’s price drops by 20%, 50%, or 90%, and the growth needed to recover.")
    price_after_20 = asset_price * (1 - 0.2)
    price_after_50 = asset_price * (1 - 0.5)
    price_after_90 = asset_price * (1 - 0.9)
    
    investment_after_20 = initial_investment * (price_after_20 / asset_price)
    investment_after_50 = initial_investment * (price_after_50 / asset_price)
    investment_after_90 = initial_investment * (price_after_90 / asset_price)

    def breakeven_requirement(drop):
        if drop == 0:
            return 0
        return (drop / (100 - drop)) * 100

    breakeven_20 = breakeven_requirement(20)
    breakeven_50 = breakeven_requirement(50)
    breakeven_90 = breakeven_requirement(90)

    mdd_data = {
        "Price Drop (%)": ["20%", "50%", "90%"],
        "Asset Price After Drop ($)": [f"${price_after_20:,.2f}", f"${price_after_50:,.2f}", f"${price_after_90:,.2f}"],
        "Investment Value After Drop ($)": [f"${investment_after_20:,.2f}", f"${investment_after_50:,.2f}", f"${investment_after_90:,.2f}"],
        "Breakeven Requirement (%)": [f"{breakeven_20:.2f}%", f"{breakeven_50:.2f}%", f"{breakeven_90:.2f}%"]
    }
    mdd_df = pd.DataFrame(mdd_data)
    st.dataframe(mdd_df, use_container_width=True)

    st.divider()

    # Suggested Portfolio Allocation (Pie Chart)
    st.subheader("Suggested Portfolio Allocation")
    st.markdown("This chart provides a suggested portfolio allocation based on your investor profile, helping you balance risk and return.")
    
    portfolio_data = {
        "Growth Investor": {
            "Liquidity Pools": 30.00,
            "BTC": 30.00,
            "Blue Chips": 30.00,
            "High Risk": 10.00
        },
        "Conservative Investor": {
            "Liquidity Pools": 50.00,
            "BTC": 40.00,
            "Blue Chips": 10.00,
            "High Risk": 0.00
        },
        "Aggressive Investor": {
            "Liquidity Pools": 20.00,
            "BTC": 30.00,
            "Blue Chips": 30.00,
            "High Risk": 20.00
        },
        "Bitcoin Strategy": {
            "BTC": 70.00,
            "Blue Chips": 10.00,
            "Liquidity Pools": 15.00,
            "High Risk": 5.00
        }
    }
    
    selected_portfolio = portfolio_data[investor_profile]
    labels = list(selected_portfolio.keys())
    sizes = list(selected_portfolio.values())
    
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("Set2"))
    plt.title("Suggested Portfolio Allocation")
    st.pyplot(plt)
    plt.clf()

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

    # 95% Confidence Interval
    st.markdown(f"**95% Confidence Interval**: There’s a 95% chance your investment will be between ${ci_lower:,.2f} and ${ci_upper:,.2f}.")

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
    st.markdown("This section provides recommendations and warnings based on the analysis, helping you make informed decisions. The 16% minimum hurdle rate is calculated as 10% (stablecoin pool return) + 6% (global inflation average), ensuring your investment beats inflation and matches a safe return.")

    # Insight 1: Risk-Adjusted Return
    if sharpe_ratio > 1:
        st.markdown('<div class="green-background">✓ <b>Good Risk-Adjusted Return</b>: Sharpe Ratio > 1, indicating the asset\'s return justifies its risk.</div>', unsafe_allow_html=True)
    elif sharpe_ratio > 0:
        st.markdown('<div class="yellow-background">⚠ <b>Moderate Risk-Adjusted Return</b>: Sharpe Ratio between 0 and 1. Consider if the risk is worth the reward.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="red-background">⚠ <b>Poor Risk-Adjusted Return</b>: Sharpe Ratio < 0. The asset\'s return does not justify its risk.</div>', unsafe_allow_html=True)

    # Alert 1: High Volatility
    if worst_case < expected_case * 0.5:
        st.markdown('<div class="red-background">⚠ <b>High Volatility Alert</b>: The worst-case scenario is less than 50% of the expected case, indicating high risk.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="green-background">✓ <b>Volatility Check</b>: The worst-case scenario is within acceptable bounds relative to the expected case.</div>', unsafe_allow_html=True)

    # Alert 2: Comparison to Historical Returns
    historical_btc_return = 50  # Simplified historical average
    if growth_rate > historical_btc_return * 1.5:
        st.markdown('<div class="yellow-background">⚠ <b>Optimistic Growth Alert</b>: Your expected growth rate is significantly higher than Bitcoin\'s historical average (50%). Ensure this is realistic.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="green-background">✓ <b>Growth Expectation Check</b>: Your expected growth rate is within a realistic range compared to Bitcoin\'s historical average (50%).</div>', unsafe_allow_html=True)

    # Alert 3: Hurdle Rate Comparison (16% and 25%)
    hurdle_rate_minimum = 16.0  # 10% risk-free + 6% inflation
    hurdle_rate_btc = 25.0  # Bitcoin average annual return
    if annualized_asset_roi < hurdle_rate_minimum:
        st.markdown(f'<div class="red-background">⚠ <b>Hurdle Rate Alert</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) is below the minimum hurdle rate of {hurdle_rate_minimum:.1f}% (10% stablecoin return + 6% inflation). Consider safer investments.</div>', unsafe_allow_html=True)
    elif annualized_asset_roi < hurdle_rate_btc:
        st.markdown(f'<div class="yellow-background">⚠ <b>Hurdle Rate Alert</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) meets the minimum hurdle rate of {hurdle_rate_minimum:.1f}% but is below Bitcoin\'s average return of {hurdle_rate_btc:.1f}%. Consider allocating more to Bitcoin.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="green-background">✓ <b>Hurdle Rate Check</b>: The asset\'s annualized ROI ({annualized_asset_roi:.2f}%) exceeds both the minimum hurdle rate of {hurdle_rate_minimum:.1f}% and Bitcoin\'s average return of {hurdle_rate_btc:.1f}%. This is a strong performer.</div>', unsafe_allow_html=True)
