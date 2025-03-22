import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar inputs
st.sidebar.header("Input Parameters")

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=84000.0)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=35.0)
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=1000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=60000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=15.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=10.0)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Calculations
    months = 12
    asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1  # Approx 2.54% for 35% annual growth
    btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
    rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
    
    # Standard price projections (without volatility) for the chart
    asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
    btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
    rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
    
    # Monte Carlo Simulation (capped at the user-input growth rate)
    n_simulations = 200
    monthly_volatility = 0.03  # 3% standard deviation for monthly returns
    simulations = []
    max_allowed_value = initial_investment * (1 + growth_rate/100)  # Cap at user-input growth rate (e.g., $1,350 for 35% growth)
    
    np.random.seed(42)  # For reproducibility
    for _ in range(n_simulations):
        sim_prices = [initial_investment]
        for i in range(months):
            monthly_return = np.random.normal(asset_monthly_rate, monthly_volatility)
            sim_prices.append(sim_prices[-1] * (1 + monthly_return))
        final_value = min(sim_prices[-1], max_allowed_value)  # Cap the final value
        simulations.append(final_value)
    
    best_case = max(simulations)
    worst_case = min(simulations)
    expected_case = np.mean(simulations)
    
    # Maximum Drawdown calculation (price after specific drops)
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Projected Asset Price (1 Year)", 
                 f"${asset_projections[-1]:,.2f}",
                 f"{growth_rate}%")
        
    with col2:
        st.metric("Investment Value (1 Year)",
                 f"${(initial_investment * asset_projections[-1] / asset_price):,.2f}",
                 f"${(initial_investment * asset_projections[-1] / asset_price) - initial_investment:,.2f}")

    # Price Projections Chart
    st.subheader("Asset Price Projections")
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
    plt.title('Price Projections Over 12 Months')
    plt.legend()
    st.pyplot(plt)
    plt.clf()

    # MDD Table (price after specific drops)
    st.subheader("Investment Value After Price Drops")
    mdd_data = {
        "Price Drop (%)": ["20%", "50%", "90%"],
        "Asset Price After Drop ($)": [f"${price_after_20:,.2f}", f"${price_after_50:,.2f}", f"${price_after_90:,.2f}"],
        "Investment Value After Drop ($)": [f"${investment_after_20:,.2f}", f"${investment_after_50:,.2f}", f"${investment_after_90:,.2f}"],
        "Breakeven Requirement (%)": [f"{breakeven_20:.2f}%", f"{breakeven_50:.2f}%", f"{breakeven_90:.2f}%"]
    }
    mdd_df = pd.DataFrame(mdd_data)
    st.table(mdd_df)

    # Comparison Section
    st.subheader("Comparison vs BTC and Stablecoin")
    col1, col2, col3 = st.columns(3)
    with col1:
        asset_roi = ((initial_investment * asset_projections[-1] / asset_price) / initial_investment - 1) * 100
        st.metric("Asset ROI", f"{asset_roi:.2f}%")
    with col2:
        btc_roi = ((btc_projections[-1] / btc_price) - 1) * 100
        st.metric("BTC ROI", f"{btc_roi:.2f}%")
    with col3:
        rf_roi = ((rf_projections[-1] / initial_investment) - 1) * 100
        st.metric("Stablecoin ROI", f"{rf_roi:.2f}%")

    # Monte Carlo Results
    st.subheader("Monte Carlo Analysis (200 Scenarios)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Case", f"${best_case:,.2f}")
    with col2:
        st.metric("Worst Case", f"${worst_case:,.2f}")
    with col3:
        st.metric("Expected Case", f"${expected_case:,.2f}")

    # Monte Carlo Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(simulations, bins=50)
    plt.title("Distribution of Possible Outcomes")
    plt.xlabel("Final Value ($)")
    st.pyplot(plt)
    plt.clf()

    # Actionable Insights
    st.subheader("Actionable Insights")
    asset_value = initial_investment * asset_projections[-1] / asset_price
    if asset_value > btc_projections[-1] and asset_value > rf_projections[-1]:
        st.write("✓ Your asset is projected to outperform both Bitcoin and Stablecoin returns")
    elif asset_value > rf_projections[-1]:
        st.write("✓ Your asset beats stablecoin returns but may underperform Bitcoin")
    else:
        st.write("⚠ Your asset may underperform both Bitcoin and Stablecoin returns")
