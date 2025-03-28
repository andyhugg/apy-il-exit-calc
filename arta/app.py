import streamlit as st
from liquidity_pool_analyzer import run_liquidity_analyzer
from asset_valuation_tool import run_valuation_tool

# Header section
st.image("Arta.png", use_column_width=True)  # Assuming Arta.png is in the same directory
st.title("Welcome to the Crypto Analysis Suite")
st.write("""
This app provides tools for liquidity pool analysis and asset valuation.
Not financial advice.
""")

# Tool selection
tool_choice = st.radio("Choose a tool:", 
                      ("Liquidity Pool Analyzer", "Asset Valuation Tool"))

# Run selected tool
if tool_choice == "Liquidity Pool Analyzer":
    run_liquidity_analyzer()
else:
    run_valuation_tool()
