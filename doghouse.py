import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from pycoingecko import CoinGeckoAPI

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Custom CSS (unchanged from your provided code)
st.markdown("""
    <style>
    /* Your existing CSS here */
    </style>
""", unsafe_allow_html=True)

# Title and Introduction (unchanged)
st.title("Arta - Master the Risk - CryptoRiskAnalyzer.com")
st.markdown("""
Arta - Indonesian for "wealth" - was the name of my cat and now the name of my app! It's perfect for fast, accurate insights into price projections, potential profits, and crypto asset or liquidity pool risk. You can run scenarios, test your assumptions, and sharpen your edge, all in real time. **Builder - AHU**
""")
st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
**Looking to analyze a Liquidity Pool?**  
If you want to analyze a liquidity pool for potential returns, risks, or impermanent loss, click the link below to use our Pool Analyzer tool:  
<a href="https://crypto-pool-analyzer.onrender.com" target="_self">Go to Pool Analyzer</a>
""", unsafe_allow_html=True)

st.sidebar.header("Configure your Crypto Asset")

# Cache CoinGecko asset list
@st.cache_data
def get_coingecko_assets():
    try:
        assets = cg.get_coins_list()
        return {asset['name']: asset['id'] for asset in assets}
    except Exception as e:
        st.error(f"Error fetching asset list: {e}")
        return {}

# Fetch Fear and Greed Index (using Alternative.me API as an example)
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_fear_and_greed():
    try:
        response = requests.get("https://api.alternative.me/fng/?limit=1")
        data = response.json()['data'][0]
        return float(data['value'])
    except Exception:
        return 50.0  # Default to neutral if API fails

# Fetch asset data from CoinGecko
def get_asset_data(asset_id):
    try:
        data = cg.get_coin_by_id(asset_id, market_data=True)
        return {
            'price': data['market_data']['current_price']['usd'],
            'market_cap': data['market_data']['market_cap']['usd'],
            'fdv': data['market_data'].get('fully_diluted_valuation', {}).get('usd', 0),
            'vol_24h': data['market_data']['total_volume']['usd']
        }
    except Exception as e:
        st.error(f"Error fetching data for {asset_id}: {e}")
        return None

# Asset selection
assets = get_coingecko_assets()
asset_names = list(assets.keys())
selected_asset = st.sidebar.selectbox("Select Asset", [""] + asset_names)

# Autofill fields if asset selected
if selected_asset:
    asset_id = assets[selected_asset]
    asset_data = get_asset_data(asset_id)
    if asset_data:
        asset_price = asset_data['price']
        market_cap = asset_data['market_cap']
        fdv = asset_data['fdv'] if asset_data['fdv'] > 0 else market_cap  # Fallback to market cap if FDV missing
        vol_mkt_cap = (asset_data['vol_24h'] / market_cap * 100) if market_cap > 0 else 0
    else:
        asset_price = market_cap = fdv = vol_mkt_cap = 0.0
else:
    asset_price = market_cap = fdv = vol_mkt_cap = 0.0

# Display autofilled fields (read-only)
st.sidebar.number_input("Current Asset Price ($)", value=asset_price, disabled=True, format="%.4f")
st.sidebar.number_input("Current Market Cap ($)", value=market_cap, disabled=True, format="%.0f")
st.sidebar.number_input("Fully Diluted Valuation (FDV) ($)", value=fdv, disabled=True, format="%.0f")
st.sidebar.number_input("Vol/Mkt Cap (24h) %", value=vol_mkt_cap, disabled=True, format="%.2f")

# User inputs that remain manual
investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
    index=0
)
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
st.sidebar.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")
fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=get_fear_and_greed())
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", value=cg.get_price(ids='bitcoin', vs_currencies='usd')['bitcoin']['usd'], disabled=True)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

calculate = st.sidebar.button("Calculate")

# Main content (unchanged calculations from your original code)
if calculate:
    if asset_price == 0 or initial_investment == 0:
        st.error("Please select an asset and enter an Initial Investment greater than 0.")
    else:
        total_supply = fdv / asset_price if fdv > 0 and asset_price > 0 else 0
        trading_volume = (vol_mkt_cap / 100) * market_cap if market_cap > 0 else 0

        months = 12
        asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
        btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
        rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
        
        asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
        btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
        rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
        
        asset_values = [initial_investment * p / asset_price for p in asset_projections]
        btc_values = [initial_investment * p / btc_price for p in btc_projections]
        
        @st.cache_data
        def run_monte_carlo(initial_investment, growth_rate, fear_and_greed, months, n_simulations=200):
            expected_annual_return = growth_rate / 100
            if fear_and_greed <= 24:
                volatility_value = 0.75
            elif fear_and_greed <= 49:
                volatility_value = 0.60
            elif fear_and_greed == 50:
                volatility_value = 0.40
            elif fear_and_greed <= 74:
                volatility_value = 0.50
            else:
                volatility_value = 0.70
            volatility_adjustment = 1.2 if fear_and_greed <= 49 else 1.1 if fear_and_greed > 50 else 1.0
            adjusted_volatility = volatility_value * volatility_adjustment
            monthly_volatility = adjusted_volatility / np.sqrt(12) if adjusted_volatility > 0 else 0.1
            lower_bound = expected_annual_return - adjusted_volatility
            upper_bound = expected_annual_return + adjusted_volatility
            monthly_expected_return = (1 + expected_annual_return) ** (1/12) - 1
            simulations, sim_paths, all_monthly_returns = [], [], []
            for _ in range(n_simulations):
                alpha, beta = (2, 5) if fear_and_greed <= 49 else (5, 2) if fear_and_greed > 50 else (2, 2)
                raw_return = np.random.beta(alpha, beta)
                annual_return = lower_bound + (upper_bound - lower_bound) * raw_return
                monthly_base_return = (1 + annual_return) ** (1/12) - 1
                monthly_returns = np.random.normal(monthly_base_return, monthly_volatility/2, months)
                sim_prices = [initial_investment]
                for i in range(months):
                    sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
                max_allowed_value = initial_investment * (1 + expected_annual_return + adjusted_volatility)
                sim_prices[-1] = min(sim_prices[-1], max_allowed_value)
                simulations.append(sim_prices[-1])
                sim_paths.append(sim_prices)
                all_monthly_returns.extend(monthly_returns)
            return simulations, sim_paths, all_monthly_returns

        simulations, sim_paths, all_monthly_returns = run_monte_carlo(initial_investment, growth_rate, fear_and_greed, months)
        worst_case = np.percentile(simulations, 10)
        expected_case = np.mean(simulations)
        best_case = np.percentile(simulations, 90)
        worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
        peak = np.maximum.accumulate(worst_path)
        drawdowns = (peak - worst_path) / peak
        max_drawdown = max(drawdowns) * 100

        # Rest of your calculation and display logic remains unchanged
        # Add your existing code here for risk assessment, key metrics, projections, Monte Carlo, and portfolio structure
        # For brevity, I'll assume you can integrate this into your existing structure

        st.success("Calculations complete! Check the expanders below for results.")
