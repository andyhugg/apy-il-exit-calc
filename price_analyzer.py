import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Title
st.title("Crypto Price and Risk Calculator")

# Sidebar inputs
st.sidebar.header("Input Parameters")

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=1.0)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=10.0)
market_cap = st.sidebar.number_input("Current Market Cap ($)", min_value=0.0, value=1000000.0)
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=1000.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=60000.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=15.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=5.0)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Calculations
    months = 12
    asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
    btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
    rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
    
    # Price projections
    asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
    btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
    rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
    
    # Monte Carlo Simulation
    n_simulations = 200
    simulations = []
    for _ in range(n_simulations):
        monthly_returns = np.random.uniform(-0.5, 0.5, months)  # ±50% monthly variation
        sim_prices = [initial_investment]
        for i in range(months):
            sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
        simulations.append(sim_prices[-1])
    
    best_case = max(simulations)
    worst_case = min(simulations)
    expected_case = np.mean(simulations)
    
    # Maximum Drawdown calculation
    asset_values = [initial_investment * p / asset_price for p in asset_projections]
    peak = np.maximum.accumulate(asset_values)
    drawdowns = (peak - asset_values) / peak
    max_drawdown = max(drawdowns) * 100

    # Display results in tiles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Projected Asset Price (1 Year)", 
                 f"${asset_projections[-1]:,.2f}",
                 f"{growth_rate}%")
        
    with col2:
        st.metric("Investment Value (1 Year)",
                 f"${asset_values[-1]:,.2f}",
                 f"${asset_values[-1] - initial_investment:,.2f}")
        
    with col3:
        st.metric("Max Drawdown",
                 f"{max_drawdown:.2f}%")

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
    plt.clf()  # Clear the figure after displaying

    # Comparison Section
    st.subheader("Comparison vs BTC and Stablecoin")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Asset ROI", f"{((asset_values[-1]/initial_investment)-1)*100:.2f}%")
    with col2:
        st.metric("BTC ROI", f"{((btc_projections[-1]/btc_price)-1)*100:.2f}%")
    with col3:
        st.metric("Stablecoin ROI", f"{((rf_projections[-1]/initial_investment)-1)*100:.2f}%")

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
    plt.clf()  # Clear the figure after displaying

    # Actionable Insights
    st.subheader("Actionable Insights")
    if asset_values[-1] > btc_projections[-1] and asset_values[-1] > rf_projections[-1]:
        st.write("✓ Your asset is projected to outperform both Bitcoin and Stablecoin returns")
    elif asset_values[-1] > rf_projections[-1]:
        st.write("✓ Your asset beats stablecoin returns but may underperform Bitcoin")
    else:
        st.write("⚠ Your asset may underperform both Bitcoin and Stablecoin returns")
        
    if max_drawdown > 50:
        st.write("⚠ High risk: Maximum drawdown exceeds 50%")
    elif max_drawdown > 30:
        st.write("⚠ Medium risk: Maximum drawdown between 30-50%")
    else:
        st.write("✓ Low risk: Maximum drawdown below 30%")
