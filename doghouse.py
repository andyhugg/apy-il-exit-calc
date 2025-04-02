# --- Start of Part 1 ---

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from pycoingecko import CoinGeckoAPI
import time

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Custom CSS (unchanged)
st.markdown("""
    <style>
    .metric-tile {
        background-color: #1E2A44;
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 15px;
        width: 100%;
        min-height: 80px;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-title {
        font-size: 16px;
        font-weight: bold;
        width: 20%;
        min-width: 120px;
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        width: 20%;
        min-width: 120px;
        white-space: normal;
        word-wrap: break-word;
    }
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 100px;
        line-height: 1.4;
    }
    .tooltip {
        cursor: help;
        color: #FFC107;
        font-size: 14px;
        margin-left: 5px;
    }
    .red-text { color: #FF4D4D; }
    .green-text { color: #32CD32; }
    .yellow-text { color: #FFC107; }
    .neutral-text { color: #A9A9A9; }
    .risk-assessment {
        background-color: #1E2A44;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .risk-red { border: 2px solid #FF4D4D; }
    .risk-yellow { border: 2px solid #FFC107; }
    .risk-green { border: 2px solid #32CD32; }
    .progress-bar {
        width: 100%;
        background-color: #A9A9A9;
        border-radius: 5px;
        height: 10px;
        margin-top: 10px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 5px;
    }
    .proj-table-container {
        overflow-x: auto;
        max-width: 100%;
    }
    .proj-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(to bottom, #1E2A44, #6A82FB);
    }
    .proj-table th, .proj-table td {
        padding: 12px;
        text-align: center;
        color: #FFFFFF;
        border: 1px solid #2A3555;
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        font-weight: 500;
    }
    .proj-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .proj-table tr:nth-child(even) td { background: rgba(255, 255, 255, 0.05); }
    .proj-table tr:nth-child(odd) td { background: rgba(255, 255, 255, 0.1); }
    .proj-table tr:hover td {
        background: rgba(255, 255, 255, 0.2);
        transition: background 0.3s ease;
    }
    .monte-carlo-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: #2A3555;
    }
    .monte-carlo-table th, .monte-carlo-table td {
        padding: 12px;
        text-align: center;
        color: #FFFFFF;
        border: 1px solid #2A3555;
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        font-weight: 500;
    }
    .monte-carlo-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .disclaimer {
        border: 2px solid #FF4D4D;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
        font-style: italic;
    }
    .large-logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        max-width: 90%;
        padding-top: 20px;
        padding-bottom: 30px;
    }
    @media (max-width: 768px) {
        .metric-tile { flex-direction: column; align-items: flex-start; }
        .metric-title, .metric-value, .metric-desc { width: 100%; min-width: 0; }
        .metric-value { font-size: 18px; }
        .metric-desc { max-height: 120px; }
        .proj-table th, .proj-table td { font-size: 12px; padding: 8px; }
        .monte-carlo-table th, .monte-carlo-table td { font-size: 12px; padding: 8px; }
    }
    </style>
""", unsafe_allow_html=True)

# Title and Introduction
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

# Cache CoinGecko asset list (top 1,000 by market cap)
@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_coingecko_assets():
    try:
        # Fetch top 1,000 assets by market cap
        assets = cg.get_coins_markets(vs_currency='usd', per_page=1000, page=1, order='market_cap_desc')
        return {asset['name']: asset['id'] for asset in assets}
    except Exception as e:
        st.error(f"Error fetching asset list: {e}")
        return None  # Return None to trigger fallback

# Cache asset data with retry mechanism
@st.cache_data
def get_asset_data(asset_id):
    for _ in range(3):  # Retry up to 3 times
        try:
            data = cg.get_coins_markets(vs_currency='usd', ids=[asset_id, 'bitcoin'])
            if not data:
                st.warning(f"No data returned for asset ID: {asset_id}")
                return None
            asset_data = next((item for item in data if item['id'] == asset_id), None)
            btc_data = next((item for item in data if item['id'] == 'bitcoin'), None)
            if not asset_data:
                st.warning(f"Asset ID {asset_id} not found in CoinGecko response")
                return None
            if not btc_data:
                st.warning("Bitcoin data not found in CoinGecko response")
                return None
            return {
                'price': asset_data['current_price'],
                'market_cap': asset_data['market_cap'],
                'fdv': asset_data.get('fully_diluted_valuation', asset_data['market_cap']),
                'vol_24h': asset_data['total_volume'],
                'btc_price': btc_data['current_price']
            }
        except Exception as e:
            st.warning(f"Error fetching data for {asset_id}: {e}. Retrying...")
            time.sleep(1)  # Wait before retrying
    return None  # Return None if all retries fail

# Cache Fear and Greed Index with retry mechanism
@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_fear_and_greed():
    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            data = response.json()['data'][0]
            return float(data['value'])
        except Exception:
            time.sleep(1)  # Wait before retrying
    return 50.0  # Default to neutral if all retries fail

# Initialize session state
if 'selected_asset' not in st.session_state:
    st.session_state.selected_asset = ""
if 'asset_data' not in st.session_state:
    st.session_state.asset_data = None
if 'use_manual_inputs' not in st.session_state:
    st.session_state.use_manual_inputs = False

# Sidebar form to batch inputs
with st.sidebar.form(key='config_form'):
    st.header("Configure your Crypto Asset")

    # Check if asset list fetch failed
    assets = get_coingecko_assets()
    if assets is None:
        st.session_state.use_manual_inputs = True
        st.warning("Failed to fetch asset list from CoinGecko. Falling back to manual inputs. Please enter the asset details below.")
        selected_asset = None
        asset_names = []
    else:
        st.session_state.use_manual_inputs = False
        asset_names = sorted(list(assets.keys()))
        selected_asset = st.selectbox("Select Asset", [""] + asset_names, key='asset_select')

    # Fetch data only if asset changes and not using manual inputs
    if not st.session_state.use_manual_inputs and selected_asset and selected_asset != st.session_state.selected_asset:
        with st.spinner("Fetching asset data..."):
            st.session_state.selected_asset = selected_asset
            asset_id = assets[selected_asset]
            st.session_state.asset_data = get_asset_data(asset_id)
            if st.session_state.asset_data is None:
                st.session_state.use_manual_inputs = True
                st.warning(f"Failed to fetch data for {selected_asset} (ID: {asset_id}). Falling back to manual inputs. Please enter the asset details below.")

    # Input fields based on mode (autofill or manual)
    if st.session_state.use_manual_inputs or not st.session_state.asset_data:
        # Manual inputs
        asset_price = st.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
        market_cap = st.number_input("Current Market Cap ($)", min_value=0.0, value=0.0, format="%.0f")
        fdv = st.number_input("Fully Diluted Valuation (FDV) ($)", min_value=0.0, value=0.0, format="%.0f")
        vol_mkt_cap = st.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        btc_price = st.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0, format="%.2f")
    else:
        # Autofill fields
        asset_price = st.session_state.asset_data['price']
        market_cap = st.session_state.asset_data['market_cap']
        fdv = st.session_state.asset_data['fdv']
        vol_mkt_cap = (st.session_state.asset_data['vol_24h'] / market_cap * 100) if market_cap > 0 else 0
        btc_price = st.session_state.asset_data['btc_price']
        st.number_input("Current Asset Price ($)", value=asset_price, disabled=True, format="%.4f")
        st.number_input("Current Market Cap ($)", value=market_cap, disabled=True, format="%.0f")
        st.number_input("Fully Diluted Valuation (FDV) ($)", value=fdv, disabled=True, format="%.0f")
        st.number_input("Vol/Mkt Cap (24h) %", value=vol_mkt_cap, disabled=True, format="%.2f")
        st.number_input("Current Bitcoin Price ($)", value=btc_price, disabled=True, format="%.2f")

    # Manual inputs (always editable)
    investor_profile = st.selectbox(
        "Investor Profile",
        ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
        index=0
    )
    certik_score = st.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
    st.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")
    fear_and_greed = st.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=get_fear_and_greed())
    growth_rate = st.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
    initial_investment = st.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
    btc_growth = st.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
    risk_free_rate = st.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

    calculate = st.form_submit_button("Calculate")

# --- End of Part 1 ---

# --- Start of Part 2 ---

# Main content
if calculate:
    if asset_price == 0 or initial_investment == 0:
        st.error("Please enter an Initial Investment greater than 0 and ensure the asset price is valid.")
    else:
        with st.spinner("Calculating..."):
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
            break_even_percentage = (max_drawdown / (100 - max_drawdown)) * 100

            if total_supply > 0 and market_cap > 0 and asset_price > 0:
                circulating_supply = market_cap / asset_price
                dilution_ratio = 100 * (1 - (circulating_supply / total_supply))
                dilution_text = "✓ Low dilution risk" if dilution_ratio < 20 else "⚠ Moderate dilution risk" if dilution_ratio < 50 else "⚠ High dilution risk"
            else:
                dilution_ratio = 0
                dilution_text = "⚠ FDV not provided"

            def format_supply(value):
                if value >= 1_000_000_000:
                    return f"{value / 1_000_000_000:.2f}B"
                elif value >= 1_000_000:
                    return f"{value / 1_000_000:.2f}M"
                elif value >= 1_000:
                    return f"{value / 1_000:.2f}K"
                else:
                    return f"{value:,.0f}"

            circulating_supply_display = format_supply(circulating_supply) if 'circulating_supply' in locals() else "N/A"
            max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

            if total_supply > 0 and market_cap > 0 and asset_price > 0:
                supply_ratio = (circulating_supply / total_supply) * 100
                supply_concentration_text = "⚠ High risk" if supply_ratio < 20 else "⚠ Moderate risk" if supply_ratio < 50 else "✓ Low risk"
            else:
                supply_ratio = 0
                supply_concentration_text = "⚠ FDV not provided"

            projected_price = asset_projections[-1]
            projected_mcap = market_cap * (projected_price / asset_price)
            btc_mcap = btc_price * 21_000_000
            mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0
            mcap_text = "✓ Plausible growth" if mcap_vs_btc <= 1 else "⚠ Ambitious growth" if mcap_vs_btc <= 5 else "⚠ Very ambitious"

            if total_supply > 0:
                projected_mcap_max = projected_price * total_supply
                mcap_vs_btc_max = (projected_mcap_max / btc_mcap) * 100 if btc_mcap > 0 else 0
            else:
                projected_mcap_max = 0
                mcap_vs_btc_max = 0

            annual_return = (asset_values[-1] / initial_investment - 1)
            rf_annual = risk_free_rate / 100
            std_dev = np.std(simulations) / initial_investment
            sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0
            negative_returns = [r for r in all_monthly_returns if r < 0]
            downside_std = np.std(negative_returns) if negative_returns else 0
            sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

            hurdle_rate = (risk_free_rate + 6) * 2
            asset_vs_hurdle = growth_rate - hurdle_rate
            hurdle_label = "Strong Outperformance" if asset_vs_hurdle >= 20 else "Moderate Outperformance" if asset_vs_hurdle >= 0 else "Below Hurdle"
            hurdle_color = "green-text" if asset_vs_hurdle >= 20 else "yellow-text" if asset_vs_hurdle >= 0 else "red-text"

            # Define individual scores
            scores = {
                'Max Drawdown': 100 if max_drawdown < 30 else 50 if max_drawdown < 50 else 0,
                'Dilution Risk': 100 if dilution_ratio < 20 else 50 if dilution_ratio < 50 else 0,
                'Supply Concentration': 0 if supply_ratio < 20 else 50 if supply_ratio < 50 else 100,
                'MCap Growth': 100 if mcap_vs_btc < 1 else 50 if mcap_vs_btc < 5 else 0,
                'Sharpe Ratio': 100 if sharpe_ratio > 1 else 50 if sharpe_ratio > 0 else 0,
                'Sortino Ratio': 100 if sortino_ratio > 1 else 50 if sortino_ratio > 0 else 0,
                'CertiK Score': 100 if (50 if certik_score == 0 else certik_score) >= 70 else 50 if (50 if certik_score == 0 else certik_score) >= 40 else 0,
                'Market Cap': 100 if market_cap >= 1_000_000_000 else 50 if market_cap >= 10_000_000 else 0,
                'Fear and Greed': 100 if fear_and_greed <= 24 else 75 if fear_and_greed <= 49 else 50 if fear_and_greed == 50 else 25 if fear_and_greed <= 74 else 0,
                'Liquidity': 0 if vol_mkt_cap < 1 else 50 if vol_mkt_cap <= 5 else 100
            }

            # Define weights based on investor profile
            weights = {
                "Conservative Investor": {"Max Drawdown": 1.5, "Dilution Risk": 1.5, "Supply Concentration": 1.2, "MCap Growth": 0.5, "Sharpe Ratio": 1.0, "Sortino Ratio": 1.0, "CertiK Score": 1.5, "Market Cap": 1.2, "Fear and Greed": 0.8, "Liquidity": 1.5},
                "Bitcoin Strategist": {"Max Drawdown": 1.0, "Dilution Risk": 1.0, "Supply Concentration": 1.0, "MCap Growth": 1.5, "Sharpe Ratio": 1.0, "Sortino Ratio": 1.0, "CertiK Score": 1.0, "Market Cap": 1.0, "Fear and Greed": 0.5, "Liquidity": 1.0},
                "Growth Crypto Investor": {"Max Drawdown": 1.0, "Dilution Risk": 1.0, "Supply Concentration": 1.0, "MCap Growth": 1.2, "Sharpe Ratio": 1.2, "Sortino Ratio": 1.2, "CertiK Score": 1.0, "Market Cap": 1.0, "Fear and Greed": 1.0, "Liquidity": 1.0},
                "Aggressive Crypto Investor": {"Max Drawdown": 0.5, "Dilution Risk": 0.8, "Supply Concentration": 0.8, "MCap Growth": 1.5, "Sharpe Ratio": 1.2, "Sortino Ratio": 1.2, "CertiK Score": 1.0, "Market Cap": 1.0, "Fear and Greed": 1.0, "Liquidity": 0.8}
            }

            # Calculate weighted composite score
            weighted_sum = sum(scores[metric] * weights[investor_profile][metric] for metric in scores)
            total_weight = sum(weights[investor_profile].values())
            composite_score = weighted_sum / total_weight if total_weight > 0 else 0

            return_to_hurdle_ratio = min((growth_rate / hurdle_rate) if hurdle_rate > 0 else 1, 3)
            risk_adjusted_score = min(composite_score * return_to_hurdle_ratio, 100)

            fear_greed_classification = "Extreme Fear" if fear_and_greed <= 24 else "Fear" if fear_and_greed <= 49 else "Neutral" if fear_and_greed == 50 else "Greed" if fear_and_greed <= 74 else "Extreme Greed"
            bg_class = "risk-green" if composite_score >= 70 else "risk-yellow" if composite_score >= 40 else "risk-red"
            insight = (
                f"Low risk profile. Strong returns vs. risk-free rate." if composite_score >= 70 else
                f"Moderate risk. Check drawdown, dilution, or growth." if composite_score >= 40 else
                f"High risk. Reassess due to drawdown or dilution."
            )
            summary = "Low Risk" if composite_score >= 70 else "Moderate Risk" if composite_score >= 40 else "High Risk"

            # Risk Assessment with Progress Bar
            with st.expander("Composite Risk Assessment", expanded=True):
                progress_color = "#32CD32" if composite_score >= 70 else "#FFC107" if composite_score >= 40 else "#FF4D4D"
                st.markdown(f"""
                    <div class="risk-assessment {bg_class}">
                        <div style="font-size: 24px; font-weight: bold; color: white;">Composite Risk Score: {composite_score:.1f}/100</div>
                        <div style="font-size: 16px; margin-top: 5px; color: white;">Summary: {summary}</div>
                        <div class="progress-bar"><div class="progress-fill" style="width: {composite_score}%; background-color: {progress_color};"></div></div>
                        <div style="font-size: 16px; margin-top: 10px; color: #A9A9A9;">{insight}</div>
                        <div style="font-size: 14px; margin-top: 5px; color: #A9A9A9; font-style: italic;">Fear and Greed: {fear_and_greed} ({fear_greed_classification})</div>
                    </div>
                """, unsafe_allow_html=True)

            # Key Metrics with Simplified Tiles
            with st.expander("Key Metrics", expanded=False):
                roi = ((asset_values[-1] / initial_investment) - 1) * 100
                investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

                st.markdown("### Investment Returns and Risk-Adjusted Metrics")
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">💰 Value (1 Yr)<span class="tooltip" title="Projected value after 12 months. Insight: {'Lock in profits.' if roi > 50 else 'Hold and monitor.' if roi >= 0 else 'Reassess.'}">?</span></div>
                        <div class="metric-value">${asset_values[-1]:,.2f}<br>({investment_multiple:.2f}x)</div>
                        <div class="metric-desc">From ${initial_investment:,.2f} investment.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Sortino<span class="tooltip" title="Return per downside risk. Insight: {'Proceed confidently.' if sortino_ratio > 1 else 'Allocate to stable assets.' if sortino_ratio >= 0 else 'Shift to stable assets.'}">?</span></div>
                        <div class="metric-value {'red-text' if sortino_ratio < 0 else 'green-text' if sortino_ratio > 1 else 'yellow-text'}">{sortino_ratio:.2f}</div>
                        <div class="metric-desc">Downside risk-adjusted return.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📊 Sharpe<span class="tooltip" title="Return per total risk. Insight: {'Proceed confidently.' if sharpe_ratio > 1 else 'Consider safer assets.' if sharpe_ratio >= 0 else 'Shift to stablecoins.'}">?</span></div>
                        <div class="metric-value {'red-text' if sharpe_ratio < 0 else 'green-text' if sharpe_ratio > 1 else 'yellow-text'}">{sharpe_ratio:.2f}</div>
                        <div class="metric-desc">Total risk-adjusted return.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("### Risk Metrics")
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📉 Max DD<span class="tooltip" title="Largest potential loss. Insight: {'Minimal action.' if max_drawdown < 30 else f'Set stop-loss at {max_drawdown:.2f}%.' if max_drawdown <= 50 else 'Reduce exposure.'}">?</span></div>
                        <div class="metric-value {'red-text' if max_drawdown > 50 else 'yellow-text' if max_drawdown > 30 else 'green-text'}">{max_drawdown:.2f}%</div>
                        <div class="metric-desc">Worst-case loss scenario.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">⚖️ Dilution<span class="tooltip" title="{dilution_text}. Insight: {'Minimal action.' if dilution_ratio < 20 else 'Check unlock schedule.' if dilution_ratio <= 50 else 'Reduce position.'}">?</span></div>
                        <div class="metric-value {'red-text' if dilution_ratio > 50 else 'yellow-text' if dilution_ratio > 20 else 'green-text'}">{dilution_ratio:.2f}%</div>
                        <div class="metric-desc">Uncirculated token risk.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">🛡️ Supply<span class="tooltip" title="{supply_concentration_text}. Insight: {'Monitor whales.' if supply_ratio < 20 else 'Be cautious.' if supply_ratio < 50 else 'Proceed confidently.'}">?</span></div>
                        <div class="metric-value {'red-text' if supply_ratio < 20 else 'yellow-text' if supply_ratio < 50 else 'green-text'}">{supply_ratio:.2f}%</div>
                        <div class="metric-desc">Circulating supply ratio.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("### Market Metrics")
                mcap_max_note = f"Using Total Supply ({max_supply_display}), projected market cap would be {mcap_vs_btc_max:.2f}% of BTC’s." if total_supply > 0 else "Total Supply not provided."
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 MCap<span class="tooltip" title="{mcap_text}. Insight: {'Proceed confidently.' if mcap_vs_btc < 1 else 'Adjust growth rate.' if mcap_vs_btc <= 5 else 'Focus on realistic targets.'}">?</span></div>
                        <div class="metric-value {'red-text' if mcap_vs_btc > 5 else 'yellow-text' if mcap_vs_btc > 1 else 'green-text'}">{mcap_vs_btc:.2f}%</div>
                        <div class="metric-desc">Projected vs. BTC MCap.</div>
                    </div>
                """, unsafe_allow_html=True)

                supply_volatility_note = f"Total Supply: {max_supply_display}." if total_supply > 0 else "Total Supply not provided."
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">💧 Liquidity<span class="tooltip" title="24h volume/MCap. Insight: {'Use limit orders.' if vol_mkt_cap < 1 else 'Limit small trades.' if vol_mkt_cap <= 5 else 'Trade confidently.'}">?</span></div>
                        <div class="metric-value {'red-text' if vol_mkt_cap < 1 else 'yellow-text' if vol_mkt_cap <= 5 else 'green-text'}">{vol_mkt_cap:.2f}%</div>
                        <div class="metric-desc">{supply_volatility_note}</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("### Comparative Metrics")
                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">📈 Hurdle<span class="tooltip" title="Growth vs. hurdle. Insight: {'Favor this asset.' if asset_vs_hurdle >= 20 else 'Balance with BTC.' if asset_vs_hurdle >= 0 else 'Increase BTC.'}">?</span></div>
                        <div class="metric-value {hurdle_color}">{asset_vs_hurdle:.2f}%<br>({hurdle_label})</div>
                        <div class="metric-desc">Vs. risk-free + 12%.</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-title">🎯 Risk-Adj<span class="tooltip" title="Risk-adjusted score. Insight: {'Diversify confidently.' if risk_adjusted_score >= 70 else 'Small position.' if risk_adjusted_score >= 40 else 'Explore safer assets.'}">?</span></div>
                        <div class="metric-value {'green-text' if risk_adjusted_score >= 70 else 'yellow-text' if risk_adjusted_score >= 40 else 'red-text'}">{risk_adjusted_score:.1f}</div>
                        <div class="metric-desc">Risk vs. return score.</div>
                    </div>
                """, unsafe_allow_html=True)

            # Projections
            with st.expander("Projected Investment Value Over Time", expanded=False):
                st.markdown("**Note**: Projected values reflect growth of your initial investment.")
                proj_data = {
                    "Metric": ["Asset Value ($)", "Asset ROI (%)", "BTC Value ($)", "BTC ROI (%)", "Stablecoin Value ($)", "Stablecoin ROI (%)"],
                    "Month 0": [asset_values[0], ((asset_values[0] / initial_investment) - 1) * 100, btc_values[0], ((btc_values[0] / initial_investment) - 1) * 100, rf_projections[0], ((rf_projections[0] / initial_investment) - 1) * 100],
                    "Month 3": [asset_values[3], ((asset_values[3] / initial_investment) - 1) * 100, btc_values[3], ((btc_values[3] / initial_investment) - 1) * 100, rf_projections[3], ((rf_projections[3] / initial_investment) - 1) * 100],
                    "Month 6": [asset_values[6], ((asset_values[6] / initial_investment) - 1) * 100, btc_values[6], ((btc_values[6] / initial_investment) - 1) * 100, rf_projections[6], ((rf_projections[6] / initial_investment) - 1) * 100],
                    "Month 12": [asset_values[12], ((asset_values[12] / initial_investment) - 1) * 100, btc_values[12], ((btc_values[12] / initial_investment) - 1) * 100, rf_projections[12], ((rf_projections[12] / initial_investment) - 1) * 100]
                }
                proj_df = pd.DataFrame(proj_data)

                def color_roi(val, row_idx):
                    if "ROI" in proj_df.iloc[row_idx]["Metric"]:
                        return 'color: #32CD32' if val > 0 else 'color: #FF4D4D' if val < 0 else 'color: #A9A9A9'
                    return ''

                styled_proj_df = proj_df.style.set_table_attributes('class="proj-table"').format({
                    "Month 0": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 0'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
                    "Month 3": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 3'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
                    "Month 6": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 6'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
                    "Month 12": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 12'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x)
                }).apply(lambda row: [color_roi(row["Month 0"], row.name), color_roi(row["Month 3"], row.name), color_roi(row["Month 6"], row.name), color_roi(row["Month 12"], row.name), ''], axis=1)
                
                st.markdown('<div class="proj-table-container">', unsafe_allow_html=True)
                st.table(styled_proj_df)
                st.markdown('</div>', unsafe_allow_html=True)

                with st.spinner("Generating chart..."):
                    df_proj = pd.DataFrame({'Month': range(months + 1), 'Asset Value': asset_values, 'Bitcoin Value': btc_values, 'Stablecoin Value': rf_projections})
                    plt.figure(figsize=(10, 6))
                    sns.set_style("whitegrid")
                    sns.lineplot(data=df_proj, x='Month', y='Asset Value', label='Asset', color='#4B5EAA', linewidth=2.5, marker='o')
                    sns.lineplot(data=df_proj, x='Month', y='Bitcoin Value', label='Bitcoin', color='#FFC107', linewidth=2.5, marker='o')
                    sns.lineplot(data=df_proj, x='Month', y='Stablecoin Value', label='Stablecoin', color='#A9A9A9', linewidth=2.5, marker='o')
                    plt.axhline(y=initial_investment, color='#FF4D4D', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
                    plt.fill_between(df_proj['Month'], initial_investment, df_proj['Asset Value'], where=(df_proj['Asset Value'] < initial_investment), color='#FF4D4D', alpha=0.1, label='Loss Zone')
                    plt.title('Projected Investment Value Over 12 Months')
                    plt.xlabel('Months')
                    plt.ylabel('Value ($)')
                    plt.legend()
                    st.pyplot(plt)
                    plt.clf()

            # Monte Carlo Analysis
            with st.expander("Simplified Monte Carlo Analysis", expanded=False):
                st.markdown("Simulates 200 scenarios over 12 months using Fear and Greed volatility.")
                st.markdown("- **Expected**: Average | **Best**: 90th percentile | **Worst**: 10th percentile")
                mc_data = {
                    "Scenario": ["Worst Case", "Expected Case", "Best Case"],
                    "Projected Value ($)": [worst_case, expected_case, best_case],
                    "ROI (%)": [((worst_case / initial_investment) - 1) * 100, ((expected_case / initial_investment) - 1) * 100, ((best_case / initial_investment) - 1) * 100]
                }
                mc_df = pd.DataFrame(mc_data)
                def highlight_rows(row):
                    return ['background: #D32F2F'] * len(row) if row['Scenario'] == 'Worst Case' else ['background: #FFB300'] * len(row) if row['Scenario'] == 'Expected Case' else ['background: #388E3C'] * len(row)
                styled_mc_df = mc_df.style.apply(highlight_rows, axis=1).set_table_attributes('class="monte-carlo-table"')
                st.table(styled_mc_df)

                with st.spinner("Generating chart..."):
                    plt.figure(figsize=(10, 6))
                    sns.histplot(simulations, bins=50, color='#A9A9A9')
                    plt.axvline(worst_case, color='#D32F2F', label='Worst Case', linewidth=2)
                    plt.axvline(expected_case, color='#FFB300', label='Expected Case', linewidth=2)
                    plt.axvline(best_case, color='#388E3C', label='Best Case', linewidth=2)
                    plt.axvline(initial_investment, color='#1E2A44', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
                    plt.title("Simplified Monte Carlo Analysis - 12 Month Investment Value")
                    plt.xlabel("Value ($)")
                    plt.ylabel("Frequency")
                    plt.legend()
                    st.pyplot(plt)
                    plt.clf()

            # Portfolio Structure
            with st.expander("Suggested Portfolio Structure", expanded=False):
                st.markdown(f"Based on your profile: **{investor_profile}**")
                portfolios = {
                    "Conservative Investor": {"Stablecoin Liquidity Pools": 50.0, "BTC": 40.0, "Blue Chips": 8.0, "High Risk Assets": 2.0},
                    "Growth Crypto Investor": {"Mixed Liquidity Pools": 30.0, "BTC": 30.0, "Blue Chips": 30.0, "High Risk Assets": 10.0},
                    "Aggressive Crypto Investor": {"Mixed Liquidity Pools": 20.0, "BTC": 30.0, "Blue Chips": 30.0, "High Risk Assets": 20.0},
                    "Bitcoin Strategist": {"Mixed Liquidity Pools": 10.0, "BTC": 80.0, "Blue Chips": 8.0, "High Risk Assets": 2.0}
                }
                labels = list(portfolios[investor_profile].keys())
                sizes = list(portfolios[investor_profile].values())
                colors = ['#4B5EAA', '#FFC107', '#32CD32', '#FF4D4D']
                explode = (0.05, 0, 0, 0)
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
                plt.title(f"Portfolio Allocation for {investor_profile}")
                st.pyplot(plt)
                plt.clf()

                st.markdown("""
                ### Understanding the Asset Classes
                - **Stablecoin Liquidity Pools**: Low volatility, 5–10% returns.
                - **Mixed Liquidity Pools**: Moderate risk, 10–20% returns.
                - **BTC**: Stable anchor, long-term growth.
                - **Blue Chips**: Lower volatility, established ecosystems.
                - **High Risk Assets**: High growth potential, high risk.
                """)

        st.success("Calculations complete! Check the expanders below for results.")

# --- End of Part 2 ---
