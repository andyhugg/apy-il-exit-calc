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
holding_allocation_pct = st.sidebar.number_input("% of Portfolio for Holding", min_value=0.0, max_value=100.0, step=1.0, value=40.0, format="%.2f")
trading_allocation_pct = st.sidebar.number_input("% of Portfolio for Trading", min_value=0.0, max_value=100.0, step=1.0, value=20.0, format="%.2f")

# Ensure allocations sum to 100%
total_allocation = defi_allocation_pct + holding_allocation_pct + trading_allocation_pct
if total_allocation != 100.0:
    st.sidebar.warning("⚠️ Allocations must sum to 100%. Adjust percentages.")
    st.stop()

# Calculate allocations
defi_allocation = (defi_allocation_pct / 100) * initial_investment
holding_allocation = (holding_allocation_pct / 100) * initial_investment
trading_allocation = (trading_allocation_pct / 100) * initial_investment

# Calculate return targets
annual_return_target = (annual_return_target_pct / 100) * initial_investment
defi_return_target = (defi_allocation / initial_investment) * annual_return_target
holding_return_target = (holding_allocation / initial_investment) * annual_return_target
trading_return_target = (trading_allocation / initial_investment) * annual_return_target

# Display results
st.subheader("Investment Allocation Plan")
st.write(f"**Total Investment:** ${initial_investment:,.2f}")
st.write(f"**Annual Return Target:** ${annual_return_target:,.2f} ({annual_return_target_pct:.2f}%)")

st.subheader("Portfolio Breakdown")
st.write(f"- **DeFi Allocation:** ${defi_allocation:,.2f} ({defi_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${defi_return_target:,.2f}")
st.write(f"- **Holding Allocation:** ${holding_allocation:,.2f} ({holding_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${holding_return_target:,.2f}")
st.write(f"- **Trading Allocation:** ${trading_allocation:,.2f} ({trading_allocation_pct:.2f}%)")
st.write(f"  - Expected Return: ${trading_return_target:,.2f}")

# Summary
st.subheader("Discussion Points for Planning")
st.write("✅ **Assess risk tolerance for each category (DeFi, Holding, Trading).**")
st.write("✅ **Discuss specific assets and strategies for each allocation.**")
st.write("✅ **Monitor portfolio performance and adjust as needed.**")
st.write("✅ **Optimize yield strategies in DeFi and trading opportunities.**")
