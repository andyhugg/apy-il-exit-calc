import streamlit as st
import numpy as np
import pandas as pd

# --- Crypto Portfolio Planning App ---
st.title("Crypto Portfolio Planning & Allocation Tool")

st.sidebar.header("Client Investment Parameters")

# User inputs
initial_investment = st.sidebar.number_input("Total Investment Capital ($)", min_value=1000.0, step=500.0, value=100000.0, format="%.2f")
annual_return_target_pct = st.sidebar.number_input("Annual Return Target (%)", min_value=1.0, step=1.0, value=45.0, format="%.2f")
defi_allocation_pct = st.sidebar.number_input("% of Portfolio for DeFi", min_value=0.0, max_value=100.0, step=1.0, value=40.0, format="%.2f")
holding_allocation_pct = st.sidebar.number_input("% of Portfolio for Holding", min_value=0.0, max_value=100.0, step=1.0, value=30.0, format="%.2f")
trading_allocation_pct = st.sidebar.number_input("% of Portfolio for Trading", min_value=0.0, max_value=100.0, step=1.0, value=20.0, format="%.2f")
stablecoin_gold_allocation_pct = st.sidebar.number_input("% of Portfolio for Stablecoin/Gold", min_value=0.0, max_value=100.0, step=1.0, value=10.0, format="%.2f")

# Ensure allocations sum to 100%
total_allocation = defi_allocation_pct + holding_allocation_pct + trading_allocation_pct + stablecoin_gold_allocation_pct
if total_allocation != 100.0:
    st.sidebar.warning("⚠️ Allocations must sum to 100%. Adjust percentages.")
    st.stop()

# BTC Price & Projection
current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=1000.0, step=100.0, value=50000.0, format="%.2f")
btc_annual_change_pct = st.sidebar.number_input("BTC Annual Expected Change (%)", min_value=-100.0, max_value=500.0, step=1.0, value=20.0, format="%.2f")
projected_btc_price = current_btc_price * (1 + btc_annual_change_pct / 100)

# Calculate allocations
defi_allocation = (defi_allocation_pct / 100) * initial_investment
holding_allocation = (holding_allocation_pct / 100) * initial_investment
trading_allocation = (trading_allocation_pct / 100) * initial_investment
stablecoin_gold_allocation = (stablecoin_gold_allocation_pct / 100) * initial_investment

# Calculate return targets
annual_return_target = (annual_return_target_pct / 100) * initial_investment
defi_return_target = (defi_allocation / initial_investment) * annual_return_target
holding_return_target = (holding_allocation / initial_investment) * annual_return_target
trading_return_target = (trading_allocation / initial_investment) * annual_return_target
stablecoin_gold_return_target = 0.0  # Stablecoins and gold typically have minimal yield

defi_apy = st.sidebar.number_input("DeFi APY (%)", min_value=0.0, max_value=200.0, step=1.0, value=10.0, format="%.2f")
monthly_defi_income = defi_allocation * (defi_apy / 100) / 12

# Display results
st.subheader("Investment Allocation Plan")
st.write(f"**Total Investment:** ${initial_investment:,.2f}")
st.write(f"**Annual Return Target:** ${annual_return_target:,.2f} ({annual_return_target_pct:.2f}%)")

st.subheader("Portfolio Breakdown")
st.write(f"- **DeFi Allocation:** ${defi_allocation:,.2f} ({defi_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${defi_return_target:,.2f}")
st.write(f"  - Monthly Passive Income: ${monthly_defi_income:,.2f}")
st.write(f"- **Holding Allocation:** ${holding_allocation:,.2f} ({holding_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${holding_return_target:,.2f}")
st.write(f"- **Trading Allocation:** ${trading_allocation:,.2f} ({trading_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${trading_return_target:,.2f}")
st.write(f"- **Stablecoin/Gold Allocation:** ${stablecoin_gold_allocation:,.2f} ({stablecoin_gold_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${stablecoin_gold_return_target:,.2f}")

# BTC Comparison
btc_investment_value = initial_investment * (projected_btc_price / current_btc_price)
st.subheader("BTC vs. Portfolio Comparison")
st.write(f"**Projected BTC Price in 12 Months:** ${projected_btc_price:,.2f}")
st.write(f"**If fully invested in BTC, portfolio value would be:** ${btc_investment_value:,.2f}")

# Maximum Drawdown & Recovery
st.subheader("Maximum Drawdown (MDD) & Recovery Needs")
mdd_levels = [20, 50, 90]
breakeven_recovery = [round(100 / (1 - mdd / 100) - 100, 2) for mdd in mdd_levels]
st.write("**BTC Maximum Drawdowns and Required Recovery Rates**")
for mdd, recovery in zip(mdd_levels, breakeven_recovery):
    st.write(f"- **{mdd}% Drawdown** requires **{recovery:.2f}%** gain to recover")

# Summary
st.subheader("Discussion Points for Planning")
st.write("✅ **Assess risk tolerance for each category (DeFi, Holding, Trading, Stablecoin/Gold).**")
st.write("✅ **Discuss specific assets and strategies for each allocation.**")
st.write("✅ **Compare projected portfolio returns vs. simply holding BTC.**")
st.write("✅ **Monitor market conditions and adjust allocations accordingly.**")
st.write("✅ **Optimize DeFi strategies to maximize passive income potential.**")
