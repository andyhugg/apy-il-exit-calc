import streamlit as st
import numpy as np
import pandas as pd
import requests

# Function to fetch all available assets from CoinGecko API
def fetch_available_assets():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        return {asset["name"]: asset["id"] for asset in response.json()}
    return {}

# Function to fetch live crypto prices from CoinGecko API
def fetch_crypto_price(asset: str):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset}&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get(asset, {}).get("usd", None)
    return None

# APY vs IL Exit Calculator
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float) -> float:
    """
    Calculates Impermanent Loss (IL) based on initial and current asset prices.
    """
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2
    
    sqrt_ratio = (price_ratio_current / price_ratio_initial) ** 0.5
    il = 2 * (sqrt_ratio / (1 + sqrt_ratio)) - 1
    
    return abs(il) * 100  # Convert to percentage

def calculate_future_value(initial_investment: float, apy: float, il: float, months: int) -> float:
    """
    Projects future value based on APY and IL over time.
    """
    monthly_return = (apy / 100) / 12
    loss_factor = 1 - (il / 100)
    return round(initial_investment * ((1 + monthly_return) ** months) * loss_factor, 2)

def check_exit_conditions(apy: float, il: float):
    """
    Determines if IL is overtaking APY and suggests exit conditions.
    """
    apy_decimal = apy / 100
    il_decimal = il / 100
    
    net_return = (1 + apy_decimal) - (1 - il_decimal)
    apy_exit_threshold = il * 12  # IL spread over 12 months
    
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    break_even_months = float('inf')  # Default value in case APY is above the threshold
    
    if apy < apy_exit_threshold:
        break_even_months = il / (apy / 12) if apy > 0 else float('inf')
        st.warning(f"APY is below the IL threshold! Consider exiting.")
        st.write(f"**Break-even Duration:** {break_even_months:.2f} months")
    else:
        st.success("You're still in profit. No need to exit yet.")
    
    return break_even_months

# Streamlit App UI
st.title("APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")

# Fetch all assets from CoinGecko
st.sidebar.subheader("Live Crypto Prices")
available_assets = fetch_available_assets()
if available_assets:
    selected_crypto_name = st.sidebar.selectbox("Select Asset 1", list(available_assets.keys()))
    selected_crypto_id = available_assets[selected_crypto_name]
    asset1_price = fetch_crypto_price(selected_crypto_id)
else:
    st.sidebar.write("⚠️ Could not fetch available assets. Using manual entry.")
    selected_crypto_name = "Manual Entry"
    asset1_price = None

if asset1_price:
    st.sidebar.write(f"**{selected_crypto_name} Price:** ${asset1_price:.2f}")
else:
    st.sidebar.write("⚠️ Could not fetch live price.")
    asset1_price = st.sidebar.number_input("Enter Asset 1 Price Manually", value=86000)

initial_price_asset1 = asset1_price
initial_price_asset2 = 1  # Default to stablecoin
current_price_asset1 = asset1_price  # Assume same price initially
current_price_asset2 = 1  # Default to stablecoin
apy = st.sidebar.number_input("Current APY (%)", value=340)
investment_amount = st.sidebar.number_input("Initial Investment ($)", value=10000)

if st.sidebar.button("Calculate"):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    break_even_months = check_exit_conditions(apy, il)
    
    # Generate Break-even Duration Table
    st.subheader("Break-even Duration for Different APY Levels")
    apy_values = [50, 75, 100, 150, 200]
    break_even_durations = [round(il / (apy_val / 12), 2) if apy_val > 0 else float('inf') for apy_val in apy_values]
    df = pd.DataFrame({"APY (%)": apy_values, "Break-even Duration (Months)": break_even_durations})
    st.table(df)
    
    # Generate Future Profit Projection Table
    st.subheader("Projected Portfolio Value")
    time_periods = [3, 6, 12]  # Months
    future_values = [calculate_future_value(investment_amount, apy, il, months) for months in time_periods]
    
    df_projection = pd.DataFrame({
        "Time Period (Months)": time_periods,
        "Projected Value ($)": future_values
    })
    st.table(df_projection)
