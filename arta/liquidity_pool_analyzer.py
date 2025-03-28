import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# [All your calculation functions unchanged: calculate_il, calculate_pool_value, etc.]

def run_liquidity_analyzer():
    st.title("Simple Pool Analyzer")
    st.write("Evaluate your liquidity pool with key insights and minimal clutter.")

    # Using your provided image URL since Arta.png is handled in app.py
    st.image("https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/dm-pools.png", use_container_width=True)

    with st.sidebar:
        st.header("Your Pool")
        pool_status = st.selectbox("Pool Status", ["Existing Pool", "New Pool"])
        is_new_pool = (pool_status == "New Pool")
        
        if is_new_pool:
            current_price_asset1 = st.number_input("Asset 1 Price (Today) ($)", min_value=0.01, value=1.00, format="%.2f")
            current_price_asset2 = st.number_input("Asset 2 Price (Today) ($)", min_value=0.01, value=1.00, format="%.2f")
            initial_price_asset1 = current_price_asset1
            initial_price_asset2 = current_price_asset2
        else:
            initial_price_asset1 = st.number_input("Initial Asset 1 Price ($)", min_value=0.01, value=1.00, format="%.2f")
            initial_price_asset2 = st.number_input("Initial Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f")
            current_price_asset1 = st.number_input("Current Asset 1 Price ($)", min_value=0.01, value=1.00, format="%.2f")
            current_price_asset2 = st.number_input("Current Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f")
        
        investment_amount = st.number_input("Investment ($)", min_value=0.01, value=1.00, format="%.2f")
        apy = st.number_input("APY (%)", min_value=0.01, value=25.00, format="%.2f")
        expected_price_change_asset1 = st.number_input("Expected Price Change Asset 1 (%)", min_value=-100.0, value=1.0, format="%.2f")
        expected_price_change_asset2 = st.number_input("Expected Price Change Asset 2 (%)", min_value=-100.0, value=1.0, format="%.2f")
        current_tvl = st.number_input("Current TVL ($)", min_value=0.01, value=1.00, format="%.2f")
        
        platform_trust_score = st.selectbox(
            "Platform Trust Score (1-5)",
            options=[
                (1, "1 - Unknown (highest caution)"),
                (2, "2 - Poor (known but with concerns)"),
                (3, "3 - Moderate (neutral, some audits)"),
                (4, "4 - Good (trusted, audited)"),
                (5, "5 - Excellent (top-tier, e.g., Uniswap, Aave)")
            ],
            format_func=lambda x: x[1],
            index=0
        )[0]

        current_btc_price = st.number_input("Current BTC Price ($)", min_value=0.01, value=1.00, format="%.2f")
        btc_growth_rate = st.number_input("Expected BTC Growth Rate (%)", min_value=-100.0, value=1.0, format="%.2f")
        risk_free_rate = st.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, format="%.2f")

    if st.sidebar.button("Calculate"):
        with st.spinner("Calculating..."):
            result = check_exit_conditions(
                investment_amount, apy, initial_price_asset1, initial_price_asset2, 
                current_price_asset1, current_price_asset2, current_tvl, risk_free_rate, 
                expected_price_change_asset1, expected_price_change_asset2, is_new_pool, 
                platform_trust_score
            )
            # [Rest of your calculation and display logic unchanged]
