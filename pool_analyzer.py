import streamlit as st
import numpy as np
import pandas as pd
import requests
import urllib.parse
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Impermanent Loss Calculation
def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount):
    try:
        initial_ratio = initial_price_asset1 / initial_price_asset2 if initial_price_asset2 > 0 else 1
        current_ratio = current_price_asset1 / current_price_asset2 if current_price_asset2 > 0 else 1
        price_change_ratio = current_ratio / initial_ratio if initial_ratio > 0 else 1
        sqrt_price_change = np.sqrt(price_change_ratio)
        il = 2 * sqrt_price_change / (1 + sqrt_price_change) - 1
        il_percentage = abs(il) * 100
        return round(il_percentage, 2) if il_percentage > 0.01 else il_percentage
    except Exception as e:
        logger.error(f"Error in calculate_il: {str(e)}")
        return 0.0

# Pool Value Calculation
def calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2):
    try:
        initial_amount_asset1 = initial_investment / 2 / initial_price_asset1 if initial_price_asset1 > 0 else 0
        initial_amount_asset2 = initial_investment / 2 / initial_price_asset2 if initial_price_asset2 > 0 else 0
        value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
        pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
        il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
        return pool_value, il_impact
    except Exception as e:
        logger.error(f"Error in calculate_pool_value: {str(e)}")
        return initial_investment, 0.0

# Future Value Calculation
def calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool):
    try:
        if months < 0:
            return initial_investment, 0.0
        monthly_apy = (apy / 100) / 12
        monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
        monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
        if is_new_pool:
            starting_price_asset1 = current_price_asset1
            starting_price_asset2 = current_price_asset2
            initial_adjusted_price_asset1 = current_price_asset1
            initial_adjusted_price_asset2 = current_price_asset2
            initial_pool_value, _ = calculate_pool_value(initial_investment, starting_price_asset1, starting_price_asset2, initial_adjusted_price_asset1, initial_adjusted_price_asset2)
            pool_value = initial_pool_value
        else:
            pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
            starting_price_asset1 = initial_price_asset1
            starting_price_asset2 = initial_price_asset2
        if months == 0:
            return round(pool_value, 2), calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
        apy_compounded_value = pool_value * (1 + monthly_apy) ** months
        final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2)
        future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
        current_value = apy_compounded_value + (new_pool_value - pool_value)
        return round(current_value, 2), future_il
    except Exception as e:
        logger.error(f"Error in calculate_future_value: {str(e)}")
        return initial_investment, 0.0

# Fetch DeFi data
def fetch_defi_data(pool_address: str, chain: str = "unknown") -> tuple[float, float]:
    try:
        url = f"https://api.llama.fi/yields?pool={pool_address}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and "data" in data and len(data["data"]) > 0:
            apy = float(data["data"][0].get("apy", 0)) * 100  # Convert to percentage
            tvl = float(data["data"][0].get("tvlUsd", 0))
            logger.info(f"Fetched DeFi Llama data: APY={apy:.2f}%, TVL=${tvl:,.2f}")
            return apy, tvl
        else:
            logger.warning("DeFi Llama API returned no data.")
    except Exception as e:
        logger.error(f"DeFi Llama API failed: {str(e)}")

    # Fallback for Solana (Raydium API)
    if chain == "solana":
        try:
            raydium_url = "https://api.raydium.io/v2/ammV3/ammPools"
            response = requests.get(raydium_url, timeout=10)
            response.raise_for_status()
            pools = response.json().get("data", [])
            for pool in pools:
                if pool.get("poolId") == pool_address:
                    tvl = float(pool.get("liquidity", 0))
                    apy = float(pool.get("apr", 0)) * 100 if pool.get("apr") else 0.0
                    logger.info(f"Fetched Raydium data: APY={apy:.2f}%, TVL=${tvl:,.2f}")
                    return apy, tvl
            logger.warning("Raydium API did not find this pool.")
        except Exception as e:
            logger.error(f"Raydium API failed: {str(e)}")
    return None, None

# Parse URL and extract pool info
def parse_pool_url(url: str) -> tuple[str, str, str]:
    try:
        parsed_url = urllib.parse.urlparse(url)
        if "raydium.io" in parsed_url.netloc:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            pool_id = query_params.get("pool_id", [None])[0]
            return pool_id, "solana", "raydium"
        elif "beefy.com" in parsed_url.netloc:
            path_parts = parsed_url.path.split("/")
            vault_name = path_parts[-1] if path_parts[-1] else path_parts[-2]
            # Map vault name to pool address (simplified for Beefy)
            if vault_name == "uniswap-cow-base-usdc-cbbtc-rp":
                return "0x9cDE59Eb5B67c3B6a6E629066f4F806933905539", "evm", "beefy"
            return vault_name, "evm", "beefy"
        return None, "unknown", None
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {str(e)}")
        return None, "unknown", None

# Scrape pool data as a fallback
def scrape_pool_data(url: str) -> tuple[float, str]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Improved selector based on Raydium structure (e.g., liquidity value)
        liquidity_element = soup.find("div", class_="sc-1g6z4xm-0 jZPiho", string=lambda text: "Liquidity" in text)
        if liquidity_element:
            liquidity_text = liquidity_element.find_next("span").text.strip().replace("$", "").replace(",", "")
            tvl = float(liquidity_text) if liquidity_text.replace(".", "").isdigit() else 0.0
            logger.info(f"Scraped TVL: ${tvl:,.2f}")
            return tvl, "scraped"
        logger.warning("No liquidity data found while scraping.")
        return 0.0, "scraped"
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        return 0.0, "scraped"

# Streamlit App
st.title("Pool Profit and Risk Analyzer")

st.markdown("""
Welcome to the Pool Profit and Risk Analyzer! Paste a pool page URL from Raydium, Orca, Beefy, or other DEXs to get real-time data, or enter details manually. This tool helps you evaluate profitability and risks in DeFi pools. **Disclaimer:** This is for informational purposes only and not financial advice.
""")

# Sidebar for inputs
st.sidebar.header("Pool Input")
pool_url = st.sidebar.text_input("Pool Page URL", "https://raydium.io/clmm/create-position/?pool_id=7KFSBUVDW1ajac2ku6AsZwMwUtcXn4bRxTtv52Q5ubUC")
use_manual = st.sidebar.checkbox("Use Manual Input Instead", value=False)

# Initialize variables with defaults
apy = 0.0
tvl = 0.0
initial_investment = 10000.0
initial_price_asset1 = 125.0
initial_price_asset2 = 1.0
current_price_asset1 = 125.0
current_price_asset2 = 1.0
expected_price_change_asset1 = 0.0
expected_price_change_asset2 = 0.0
months = 12
risk_free_rate = 2.0
trust_score = 3
is_new_pool = False
btc_growth_rate = 0.0
initial_tvl = 1000000.0

if not use_manual and pool_url:
    pool_id, chain, platform = parse_pool_url(pool_url)
    if pool_id:
        st.sidebar.write(f"Detected Chain: {chain}, Platform: {platform}, Pool ID: {pool_id}")
        apy, tvl = fetch_defi_data(pool_id, chain)
        if apy is not None and tvl is not None:
            st.sidebar.write(f"Fetched APY: {apy:.2f}%, TVL: ${tvl:,.2f}")
        else:
            tvl, source = scrape_pool_data(pool_url)
            if tvl > 0:
                st.sidebar.write(f"Scraped TVL: ${tvl:,.2f} (from {source})")
                apy = st.sidebar.number_input("Manual APY (%) (since auto-fetch failed)", value=0.0, step=0.1)
            else:
                st.sidebar.warning("Couldn’t fetch data automatically. Please enter details manually.")
    else:
        st.sidebar.warning("Invalid URL format. Please enter a valid pool page URL or use manual input.")
else:
    apy = st.sidebar.number_input("APY (%)", value=1.0, step=0.1)
    tvl = st.sidebar.number_input("TVL ($)", value=1000000.0, step=1000.0)
    initial_investment = st.sidebar.number_input("Initial Investment ($)", value=10000.0, step=100.0)
    initial_price_asset1 = st.sidebar.number_input("Initial Price Asset 1 ($)", value=125.0, step=1.0)
    initial_price_asset2 = st.sidebar.number_input("Initial Price Asset 2 ($)", value=1.0, step=0.1)
    current_price_asset1 = st.sidebar.number_input("Current Price Asset 1 ($)", value=125.0, step=1.0)
    current_price_asset2 = st.sidebar.number_input("Current Price Asset 2 ($)", value=1.0, step=0.1)
    expected_price_change_asset1 = st.sidebar.number_input("Expected % Price Change Asset 1 (Annual)", value=0.0, step=1.0)
    expected_price_change_asset2 = st.sidebar.number_input("Expected % Price Change Asset 2 (Annual)", value=0.0, step=1.0)
    months = st.sidebar.number_input("Projection Months", value=12, step=1)
    risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", value=2.0, step=0.1)
    trust_score = st.sidebar.selectbox("Trust Score (1-5)", options=[1, 2, 3, 4, 5], index=2)
    is_new_pool = st.sidebar.checkbox("New Pool Entry (IL starts at 0)", value=False)
    btc_growth_rate = st.sidebar.number_input("BTC Growth Rate (%)", value=0.0, step=1.0)
    initial_tvl = st.sidebar.number_input("Initial TVL ($)", value=tvl, step=1000.0)

# Perform calculations only when button is clicked
if st.sidebar.button("Calculate"):
    try:
        pool_value, il_impact = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        future_value, future_il = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, is_new_pool)
        net_return = future_value / initial_investment if initial_investment > 0 else 0
        tvl_decline = ((initial_tvl - tvl) / initial_tvl * 100) if initial_tvl > 0 else 0.0
        pool_share = (initial_investment / tvl) * 100 if tvl > 0 else 0

        # Display results
        st.subheader("Results")
        st.write(f"Impermanent Loss (Current): {il_impact:.2f}%")
        st.write(f"Projected Impermanent Loss ({months} months): {future_il:.2f}%")
        st.write(f"Future Value: ${future_value:,.2f}")
        st.write(f"Net Return: {net_return:.2f}x")
        st.write(f"TVL Decline: {tvl_decline:.2f}%")
        st.write(f"Pool Share: {pool_share:.2f}%")
    except Exception as e:
        st.error(f"Calculation error: {str(e)}. Please check your inputs.")
        logger.error(f"Calculation failed: {str(e)}")

# Testing Section
st.sidebar.header("Testing")
if st.sidebar.button("Test URLs"):
    test_urls = [
        "https://raydium.io/clmm/create-position/?pool_id=7KFSBUVDW1ajac2ku6AsZwMwUtcXn4bRxTtv52Q5ubUC",
        "https://app.beefy.com/vault/uniswap-cow-base-usdc-cbbtc-rp"
    ]
    for url in test_urls:
        st.sidebar.write(f"Testing URL: {url}")
        pool_id, chain, platform = parse_pool_url(url)
        if pool_id:
            st.sidebar.write(f"Detected: Chain={chain}, Platform={platform}, Pool ID={pool_id}")
            apy, tvl = fetch_defi_data(pool_id, chain)
            if apy is not None and tvl is not None:
                st.sidebar.write(f"Result: APY={apy:.2f}%, TVL=${tvl:,.2f}")
            else:
                tvl, source = scrape_pool_data(url)
                st.sidebar.write(f"Fallback TVL: ${tvl:,.2f} (from {source})")
        else:
            st.sidebar.write("Invalid URL format.")
