import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
        min-height: 100px;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-title {
        font-size: 18px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
        white-space: normal;
        word-wrap: break-word;
    }
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 120px;
        line-height: 1.4;
    }
    .tooltip {
        cursor: help;
        color: #FFD700;
        font-size: 16px;
        margin-left: 5px;
    }
    .red-text {
        color: #FF4D4D;
    }
    .green-text {
        color: #32CD32;
    }
    .yellow-text {
        color: #FFD700;
    }
    .neutral-text {
        color: #A9A9A9;
    }
    .risk-assessment {
        background-color: #1E2A44;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .risk-red {
        border: 2px solid #FF4D4D;
    }
    .risk-yellow {
        border: 2px solid #FFD700;
    }
    .risk-green {
        border: 2px solid #32CD32;
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
        color: white;
        border: 1px solid #2A3555;
        font-size: 14px;
    }
    .proj-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .proj-table tr:nth-child(even) td {
        background: rgba(255, 255, 255, 0.05);
    }
    .proj-table tr:nth-child(odd) td {
        background: rgba(255, 255, 255, 0.1);
    }
    .proj-table tr:hover td {
        background: rgba(255, 255, 255, 0.2);
        transition: background 0.3s ease;
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
        .metric-tile {
            flex-direction: column;
            align-items: flex-start;
        }
        .metric-title, .metric-value, .metric-desc {
            width: 100%;
            min-width: 0;
        }
        .metric-value {
            font-size: 20px;
        }
        .metric-desc {
            max-height: 150px;
        }
        .proj-table th, .proj-table td {
            font-size: 12px;
            padding: 8px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Display the logo (unchanged)
#st.markdown(
#    f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="large-logo" width="600"></div>',
#    unsafe_allow_html=True
#)

Title and Introduction
st.title("Arta - Know the Price. Master the Risk.")
st.markdown("""
Arta - Indonesian for "wealth" - was the name of my cat and now the name of my app! It's perfect for fast, accurate insights into price projections, potential profits, and crypto asset or liquidity pool risk. You can run scenarios, test your assumptions, and sharpen your edge — all in real time. **Know the Price. Master the Risk.**
""")

st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar (unchanged)
st.sidebar.markdown("""
**Looking to analyze a Liquidity Pool?**  
If you want to analyze a liquidity pool for potential returns, risks, or impermanent loss, click the link below to use our Pool Analyzer tool:  
<a href="https://crypto-pool-analyzer.onrender.com" target="_self">Go to Pool Analyzer</a>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
**Instructions**: To get started, visit <a href="https://coinmarketcap.com" target="_blank">coinmarketcap.com</a> to find your asset’s current price, market cap, fully diluted valuation (FDV), 24h trading volume, Vol/Mkt Cap (24h) %, and Bitcoin’s price. Ensure these values are up-to-date, as they directly impact metrics like MCap Growth Plausibility and Liquidity. Visit <a href="https://certik.com" target="_blank">certik.com</a> for the asset’s CertiK security score. Enter the values below and adjust growth rates as needed.
""", unsafe_allow_html=True)

st.sidebar.header("Configure your Crypto Asset")

investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
    index=0
)
st.sidebar.markdown("**Note**: Your investor profile adjusts the composite score based on your risk tolerance.")

def parse_market_value(value_str):
    try:
        value_str = value_str.replace(",", "").lower()
        if value_str.endswith("b"):
            return float(value_str[:-1]) * 1_000_000_000
        elif value_str.endswith("m"):
            return float(value_str[:-1]) * 1_000_000
        elif value_str.endswith("k"):
            return float(value_str[:-1]) * 1_000
        else:
            return float(value_str)
    except:
        return 0.0

asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
st.sidebar.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")
fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0)
st.sidebar.markdown(
    "**Note**: Find the current Fear and Greed Index on <a href='https://coinmarketcap.com' target='_blank'>coinmarketcap.com</a>. Enter 50 if unavailable (neutral sentiment). Volatility is derived as: Extreme Fear (≤ 24): 75%, Fear (25–49): 60%, Neutral (50): 40%, Greed (51–74): 50%, Extreme Greed (≥ 75): 70%.",
    unsafe_allow_html=True
)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
market_cap = parse_market_value(market_cap_input)
st.sidebar.markdown("**Note**: Enter values as shorthand (e.g., 67b for 67 billion, 500m for 500 million, 1.5k for 1,500) or full numbers (e.g., 67,000,000,000). Commas are optional.")
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
fdv = parse_market_value(fdv_input)
vol_mkt_cap = st.sidebar.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")
st.sidebar.markdown("**Note**: Find the Vol/Mkt Cap (24h) % on CoinMarketCap (e.g., 1.94% for AVAX).")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    if asset_price == 0 or initial_investment == 0:
        st.error("Please enter valid values for Asset Price and Initial Investment (greater than 0).")
    elif market_cap == 0:
        st.error("Please provide Market Cap to proceed with calculations.")
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
            
            if fear_and_greed <= 49:
                volatility_adjustment = 1.2
            elif fear_and_greed > 50:
                volatility_adjustment = 1.1
            else:
                volatility_adjustment = 1.0
            adjusted_volatility = volatility_value * volatility_adjustment
            monthly_volatility = adjusted_volatility / np.sqrt(12) if adjusted_volatility > 0 else 0.1
            
            lower_bound = expected_annual_return - adjusted_volatility
            upper_bound = expected_annual_return + adjusted_volatility
            
            monthly_expected_return = (1 + expected_annual_return) ** (1/12) - 1
            simulations = []
            sim_paths = []
            all_monthly_returns = []
            
            for _ in range(n_simulations):
                if fear_and_greed <= 49:
                    alpha, beta = 2, 5
                elif fear_and_greed > 50:
                    alpha, beta = 5, 2
                else:
                    alpha, beta = 2, 2
                
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

        simulations, sim_paths, all_monthly_returns = run_monte_carlo(initial_investment, growth_rate, fear_and_greed, months, n_simulations=200)
        
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
            if dilution_ratio < 20:
                dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
            elif dilution_ratio < 50:
                dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
            else:
                dilution_text = "⚠ High dilution risk: Significant token releases expected."
        else:
            dilution_ratio = 0
            dilution_text = "⚠ FDV not provided, cannot assess dilution risk."

        def format_supply(value):
            if value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"{value / 1_000_000:.2f}M"
            elif value >= 1_000:
                return f"{value / 1_000:.2f}K"
            else:
                return f"{value:,.0f}"

        circulating_supply_display = format_supply(circulating_supply) if 'circulating_supply' in locals() and circulating_supply > 0 else "N/A"
        max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

        if total_supply > 0 and market_cap > 0 and asset_price > 0:
            circulating_supply = market_cap / asset_price
            supply_ratio = (circulating_supply / total_supply) * 100
            if supply_ratio < 20:
                supply_concentration_text = "⚠ High risk: Very low circulating supply relative to total supply increases the risk of price manipulation by large holders."
            elif supply_ratio < 50:
                supply_concentration_text = "⚠ Moderate risk: A significant portion of tokens is not yet circulating, which may allow large holders to influence price."
            else:
                supply_concentration_text = "✓ Low risk: A large portion of tokens is circulating, reducing the risk of price manipulation by large holders."
        else:
            supply_ratio = 0
            supply_concentration_text = "⚠ FDV not provided, cannot assess supply concentration risk."

        projected_price = asset_projections[-1]
        projected_mcap = market_cap * (projected_price / asset_price)
        btc_mcap = btc_price * 21_000_000
        mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0
        if mcap_vs_btc <= 1:
            mcap_text = "✓ Plausible growth: Small market share needed."
        elif mcap_vs_btc <= 5:
            mcap_text = "⚠ Ambitious growth: Significant market share needed."
        else:
            mcap_text = "⚠ Very ambitious: Large market share required."

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
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

        hurdle_rate = (risk_free_rate + 6) * 2
        asset_vs_hurdle = growth_rate - hurdle_rate

        if asset_vs_hurdle >= 20:
            hurdle_label = "Strong Outperformance"
            hurdle_color = "green-text"
        elif asset_vs_hurdle >= 0:
            hurdle_label = "Moderate Outperformance"
            hurdle_color = "yellow-text"
        else:
            hurdle_label = "Below Hurdle"
            hurdle_color = "red-text"

        # Define individual scores (unchanged)
        scores = {}
        if max_drawdown < 30:
            scores['Max Drawdown'] = 100
        elif max_drawdown < 50:
            scores['Max Drawdown'] = 50
        else:
            scores['Max Drawdown'] = 0
        
        if dilution_ratio < 20:
            scores['Dilution Risk'] = 100
        elif dilution_ratio < 50:
            scores['Dilution Risk'] = 50
        else:
            scores['Dilution Risk'] = 0
        
        if supply_ratio < 20:
            scores['Supply Concentration'] = 0
        elif supply_ratio < 50:
            scores['Supply Concentration'] = 50
        else:
            scores['Supply Concentration'] = 100
        
        if mcap_vs_btc < 1:
            scores['MCap Growth'] = 100
        elif mcap_vs_btc < 5:
            scores['MCap Growth'] = 50
        else:
            scores['MCap Growth'] = 0
        
        if sharpe_ratio > 1:
            scores['Sharpe Ratio'] = 100
        elif sharpe_ratio > 0:
            scores['Sharpe Ratio'] = 50
        else:
            scores['Sharpe Ratio'] = 0
        
        if sortino_ratio > 1:
            scores['Sortino Ratio'] = 100
        elif sortino_ratio > 0:
            scores['Sortino Ratio'] = 50
        else:
            scores['Sortino Ratio'] = 0
        
        certik_adjusted = 50 if certik_score == 0 else certik_score
        if certik_adjusted >= 70:
            scores['CertiK Score'] = 100
        elif certik_adjusted >= 40:
            scores['CertiK Score'] = 50
        else:
            scores['CertiK Score'] = 0
        
        if market_cap >= 1_000_000_000:
            scores['Market Cap'] = 100
        elif market_cap >= 10_000_000:
            scores['Market Cap'] = 50
        else:
            scores['Market Cap'] = 0

        if fear_and_greed <= 24:
            scores['Fear and Greed'] = 100
        elif fear_and_greed <= 49:
            scores['Fear and Greed'] = 75
        elif fear_and_greed == 50:
            scores['Fear and Greed'] = 50
        elif fear_and_greed <= 74:
            scores['Fear and Greed'] = 25
        else:
            scores['Fear and Greed'] = 0

        if vol_mkt_cap < 1:
            scores['Liquidity'] = 0
        elif vol_mkt_cap <= 5:
            scores['Liquidity'] = 50
        else:
            scores['Liquidity'] = 100

        # Define weights based on investor profile (unchanged)
        weights = {
            "Conservative Investor": {
                "Max Drawdown": 1.5,
                "Dilution Risk": 1.5,
                "Supply Concentration": 1.2,
                "MCap Growth": 0.5,
                "Sharpe Ratio": 1.0,
                "Sortino Ratio": 1.0,
                "CertiK Score": 1.5,
                "Market Cap": 1.2,
                "Fear and Greed": 0.8,
                "Liquidity": 1.5
            },
            "Bitcoin Strategist": {
                "Max Drawdown": 1.0,
                "Dilution Risk": 1.0,
                "Supply Concentration": 1.0,
                "MCap Growth": 1.5,
                "Sharpe Ratio": 1.0,
                "Sortino Ratio": 1.0,
                "CertiK Score": 1.0,
                "Market Cap": 1.0,
                "Fear and Greed": 0.5,
                "Liquidity": 1.0
            },
            "Growth Crypto Investor": {
                "Max Drawdown": 1.0,
                "Dilution Risk": 1.0,
                "Supply Concentration": 1.0,
                "MCap Growth": 1.2,
                "Sharpe Ratio": 1.2,
                "Sortino Ratio": 1.2,
                "CertiK Score": 1.0,
                "Market Cap": 1.0,
                "Fear and Greed": 1.0,
                "Liquidity": 1.0
            },
            "Aggressive Crypto Investor": {
                "Max Drawdown": 0.5,
                "Dilution Risk": 0.8,
                "Supply Concentration": 0.8,
                "MCap Growth": 1.5,
                "Sharpe Ratio": 1.2,
                "Sortino Ratio": 1.2,
                "CertiK Score": 1.0,
                "Market Cap": 1.0,
                "Fear and Greed": 1.0,
                "Liquidity": 0.8
            }
        }

        # Calculate weighted composite score (unchanged)
        weighted_sum = 0
        total_weight = 0
        for metric, score in scores.items():
            weight = weights[investor_profile][metric]
            weighted_sum += score * weight
            total_weight += weight
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0

        return_to_hurdle_ratio = (growth_rate / hurdle_rate) if hurdle_rate > 0 else 1
        return_to_hurdle_ratio = min(return_to_hurdle_ratio, 3)
        risk_adjusted_score = composite_score * return_to_hurdle_ratio
        risk_adjusted_score = min(risk_adjusted_score, 100)

        fear_greed_classification = "Neutral"
        if fear_and_greed <= 24:
            fear_greed_classification = "Extreme Fear"
        elif fear_and_greed <= 49:
            fear_greed_classification = "Fear"
        elif fear_and_greed <= 74:
            fear_greed_classification = "Greed"
        else:
            fear_greed_classification = "Extreme Greed"

        if composite_score >= 70:
            bg_class = "risk-green"
            insight = (
                f"Low risk profile. Strong returns vs. risk-free rate. Minimal dilution risk. Plausible market cap growth. Solid CertiK score. "
                f"Fear and Greed Index: {fear_and_greed} ({fear_greed_classification})—"
                f"{'potential buying opportunity' if fear_and_greed <= 49 else 'neutral sentiment' if fear_and_greed == 50 else 'potential correction risk'}."
            )
        elif composite_score >= 40:
            bg_class = "risk-yellow"
            insight = (
                f"Moderate risk. Concerns: {'high drawdown' if max_drawdown > 50 else ''}"
                f"{', dilution' if dilution_ratio > 50 else ''}"
                f"{', supply concentration' if supply_ratio < 20 else ''}"
                f"{', ambitious growth' if mcap_vs_btc > 5 else ''}"
                f"{', low liquidity' if vol_mkt_cap < 1 else ''}. "
                f"Fear and Greed Index: {fear_and_greed} ({fear_greed_classification})."
            )
        else:
            bg_class = "risk-red"
            insight = (
                f"High risk. Issues: {'extreme drawdown' if max_drawdown > 50 else ''}"
                f"{', high dilution' if dilution_ratio > 50 else ''}"
                f"{', supply concentration' if supply_ratio < 20 else ''}"
                f"{', unrealistic growth' if mcap_vs_btc > 5 else ''}"
                f"{', low liquidity' if vol_mkt_cap < 1 else ''}. "
                f"Fear and Greed Index: {fear_and_greed} ({fear_greed_classification})."
            )

        st.subheader("Composite Risk Assessment")
        st.markdown(f"""
            <div class="risk-assessment {bg_class}">
                <div style="font-size: 24px; font-weight: bold; color: white;">Composite Risk Score: {composite_score:.1f}/100</div>
                <div style="font-size: 16px; margin-top: 10px; color: #A9A9A9;">{insight}</div>
                <div style="font-size: 14px; margin-top: 5px; color: #A9A9A9; font-style: italic;">Score adjusted based on your investor profile.</div>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("Key Metrics")
        roi = ((asset_values[-1] / initial_investment) - 1) * 100
        investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

        st.markdown("### Investment Returns and Risk-Adjusted Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💰 Investment Value (1 Year)<span class="tooltip" title="Shows the projected value of your initial investment after 12 months based on the expected growth rate.">?</span></div>
                <div class="metric-value">${asset_values[-1]:,.2f}<br>({investment_multiple:.2f}x)</div>
                <div class="metric-desc">Potential value of your ${initial_investment:,.2f} investment in 12 months.<br>
                <b>Insight:</b> {'Lock in profits if reached.' if roi > 50 else 'Hold and monitor.' if roi >= 0 else 'Reassess investment.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Sortino Ratio<span class="tooltip" title="Measures return per unit of downside risk (negative returns only). A value > 1 is considered good, indicating strong returns relative to bad volatility.">?</span></div>
                <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                <div class="metric-desc">Return per unit of downside risk.<br>
                <b>Insight:</b> {'Proceed confidently.' if sortino_ratio > 1 else 'Allocate to stable assets.' if sortino_ratio >= 0 else 'Shift to stable assets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📊 Sharpe Ratio<span class="tooltip" title="Measures return per unit of total risk (both upside and downside). A value > 1 is good, showing strong risk-adjusted returns.">?</span></div>
                <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                <div class="metric-desc">Return per unit of risk.<br>
                <b>Insight:</b> {'Proceed confidently.' if sharpe_ratio > 1 else 'Consider safer assets.' if sharpe_ratio >= 0 else 'Shift to stablecoins.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Risk Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Max Drawdown<span class="tooltip" title="The largest potential loss from peak to trough in a worst-case scenario. Below 30% is low risk, above 50% is high risk.">?</span></div>
                <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                <div class="metric-desc">Largest potential loss in a worst-case scenario.<br>
                <b>Insight:</b> {'Minimal action needed.' if max_drawdown < 30 else f'Set stop-loss at {max_drawdown:.2f}%.' if max_drawdown <= 50 else 'Reduce exposure.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">⚖️ Dilution Risk<span class="tooltip" title="Percentage of total supply not yet circulating. Below 20% is low risk, above 50% suggests significant future selling pressure.">?</span></div>
                <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                <div class="metric-desc">{dilution_text}<br>
                <b>Insight:</b> {'Minimal action needed.' if dilution_ratio < 20 else 'Check unlock schedule.' if dilution_ratio <= 50 else 'Reduce position.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">🛡️ Supply Concentration Risk<span class="tooltip" title="Percentage of total supply currently circulating. Below 20% indicates high risk of manipulation by large holders, above 50% is safer.">?</span></div>
                <div class="metric-value {'red-text' if supply_ratio < 20 else 'yellow-text' if supply_ratio < 50 else 'green-text'}">{supply_ratio:.2f}%</div>
                <div class="metric-desc">{supply_concentration_text}<br>
                <b>Insight:</b> {'Monitor whale activity.' if supply_ratio < 20 else 'Be cautious of large holders.' if supply_ratio < 50 else 'Proceed confidently.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Market Metrics")
        mcap_max_note = f"Using Total Supply ({max_supply_display}), projected market cap would be {mcap_vs_btc_max:.2f}% of BTC’s." if total_supply > 0 else "Total Supply not provided."
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 MCap Growth Plausibility<span class="tooltip" title="Compares projected market cap to Bitcoin’s. Below 1% is plausible, above 5% is ambitious and may be unrealistic.">?</span></div>
                <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                <div class="metric-desc">{mcap_max_note}<br>
                <b>Insight:</b> {'Proceed confidently.' if mcap_vs_btc < 1 else 'Adjust growth rate.' if mcap_vs_btc <= 5 else 'Focus on realistic targets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        supply_volatility_note = f"Total Supply: {max_supply_display}." if total_supply > 0 else "Total Supply not provided."
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💧 Liquidity (Vol/Mkt Cap 24h)<span class="tooltip" title="24-hour trading volume as a percentage of market cap. Above 5% is high liquidity, below 1% suggests difficulty trading.">?</span></div>
                <div class="metric-value {'red-text' if vol_mkt_cap < 1 else 'green-text' if vol_mkt_cap > 5 else 'yellow-text'}">{vol_mkt_cap:.2f}%</div>
                <div class="metric-desc">{supply_volatility_note}<br>
                <b>Insight:</b> {'Use limit orders, monitor volume.' if vol_mkt_cap < 1 else 'Limit orders for small trades.' if vol_mkt_cap <= 5 else 'Trade confidently with stop-loss.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Comparative Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Hurdle Rate vs. Bitcoin<span class="tooltip" title="Compares asset growth to a benchmark (risk-free rate + 12%). Positive values beat the hurdle, above 20% is strong.">?</span></div>
                <div class="metric-value {hurdle_color}">{asset_vs_hurdle:.2f}%<br>({hurdle_label})</div>
                <div class="metric-desc">Growth vs. minimum return to beat Bitcoin.<br>
                <b>Insight:</b> {'Favor this asset.' if asset_vs_hurdle >= 20 else 'Balance with Bitcoin.' if asset_vs_hurdle >= 0 else 'Increase Bitcoin allocation.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">🎯 Risk-Adjusted Return Score<span class="tooltip" title="Combines composite score with return-to-hurdle ratio. Above 70 is strong, below 40 suggests caution.">?</span></div>
                <div class="metric-value {'green-text' if risk_adjusted_score >= 70 else 'yellow-text' if risk_adjusted_score >= 40 else 'red-text'}">{risk_adjusted_score:.1f}</div>
                <div class="metric-desc">Combines risk and return.<br>
                <b>Insight:</b> {'Diversify confidently.' if risk_adjusted_score >= 70 else 'Small position, diversify.' if risk_adjusted_score >= 40 else 'Explore safer assets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("Projected Investment Value Over Time")
        st.markdown("**Note**: Projected values reflect growth of your initial investment.")
        
        proj_data = {
            "Metric": ["Asset Value ($)", "Asset ROI (%)", "BTC Value ($)", "BTC ROI (%)", "Stablecoin Value ($)", "Stablecoin ROI (%)"],
            "Month 0": [
                asset_values[0], ((asset_values[0] / initial_investment) - 1) * 100,
                btc_values[0], ((btc_values[0] / initial_investment) - 1) * 100,
                rf_projections[0], ((rf_projections[0] / initial_investment) - 1) * 100
            ],
            "Month 3": [
                asset_values[3], ((asset_values[3] / initial_investment) - 1) * 100,
                btc_values[3], ((btc_values[3] / initial_investment) - 1) * 100,
                rf_projections[3], ((rf_projections[3] / initial_investment) - 1) * 100
            ],
            "Month 6": [
                asset_values[6], ((asset_values[6] / initial_investment) - 1) * 100,
                btc_values[6], ((btc_values[6] / initial_investment) - 1) * 100,
                rf_projections[6], ((rf_projections[6] / initial_investment) - 1) * 100
            ],
            "Month 12": [
                asset_values[12], ((asset_values[12] / initial_investment) - 1) * 100,
                btc_values[12], ((btc_values[12] / initial_investment) - 1) * 100,
                rf_projections[12], ((rf_projections[12] / initial_investment) - 1) * 100
            ]
        }
        proj_df = pd.DataFrame(proj_data)

        def color_roi(val, row_idx):
            if "ROI" in proj_df.iloc[row_idx]["Metric"]:
                if val > 0:
                    return 'color: #32CD32'
                elif val < 0:
                    return 'color: #FF4D4D'
                else:
                    return 'color: #A9A9A9'
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
            df_proj = pd.DataFrame({
                'Month': range(months + 1),
                'Asset Value': asset_values,
                'Bitcoin Value': btc_values,
                'Stablecoin Value': rf_projections
            })
            
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            sns.lineplot(data=df_proj, x='Month', y='Asset Value', label='Asset', color='#4B5EAA', linewidth=2.5, marker='o')
            sns.lineplot(data=df_proj, x='Month', y='Bitcoin Value', label='Bitcoin', color='#FFD700', linewidth=2.5, marker='o')
            sns.lineplot(data=df_proj, x='Month', y='Stablecoin Value', label='Stablecoin', color='#A9A9A9', linewidth=2.5, marker='o')
            plt.axhline(y=initial_investment, color='#FF4D4D', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
            plt.fill_between(df_proj['Month'], initial_investment, df_proj['Asset Value'], where=(df_proj['Asset Value'] < initial_investment), color='#FF4D4D', alpha=0.1, label='Loss Zone')
            plt.title('Projected Investment Value Over 12 Months')
            plt.xlabel('Months')
            plt.ylabel('Value ($)')
            plt.legend()
            st.pyplot(plt)
            plt.clf()

        st.subheader("Simplified Monte Carlo Analysis")
        st.markdown("""
        The **Simplified Monte Carlo Analysis** simulates 200 scenarios over 12 months using volatility derived from the Fear and Greed Index.
        """)
        st.markdown("""
        - **Expected Case**: Average result.
        - **Best Case**: 90th percentile.
        - **Worst Case**: 10th percentile.
        """)
        
        mc_data = {
            "Scenario": ["Worst Case", "Expected Case", "Best Case"],
            "Projected Value ($)": [worst_case, expected_case, best_case],
            "ROI (%)": [((worst_case / initial_investment) - 1) * 100, ((expected_case / initial_investment) - 1) * 100, ((best_case / initial_investment) - 1) * 100]
        }
        mc_df = pd.DataFrame(mc_data)
        
        def highlight_rows(row):
            if row['Scenario'] == 'Worst Case':
                return ['background: #FF4D4D'] * len(row)
            elif row['Scenario'] == 'Expected Case':
                return ['background: #FFD700'] * len(row)
            else:
                return ['background: #32CD32'] * len(row)

        styled_mc_df = mc_df.style.apply(highlight_rows, axis=1)
        st.table(styled_mc_df)

        with st.spinner("Generating chart..."):
            plt.figure(figsize=(10, 6))
            sns.histplot(simulations, bins=50, color='#A9A9A9')
            plt.axvline(worst_case, color='#FF4D4D', label='Worst Case', linewidth=2)
            plt.axvline(expected_case, color='#FFD700', label='Expected Case', linewidth=2)  # Fixed typo here
            plt.axvline(best_case, color='#32CD32', label='Best Case', linewidth=2)
            plt.axvline(initial_investment, color='#1E2A44', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
            plt.title("Simplified Monte Carlo Analysis - 12 Month Investment Value")
            plt.xlabel("Value ($)")
            plt.ylabel("Frequency")
            plt.legend()
            st.pyplot(plt)
            plt.clf()

        st.subheader("Suggested Portfolio Structure")
        st.markdown(f"Based on your selected investor profile: **{investor_profile}**")

        portfolios = {
            "Conservative Investor": {"Stablecoin Liquidity Pools": 50.0, "BTC": 40.0, "Blue Chips": 8.0, "High Risk Assets": 2.0},
            "Growth Crypto Investor": {"Mixed Liquidity Pools": 30.0, "BTC": 30.0, "Blue Chips": 30.0, "High Risk Assets": 10.0},
            "Aggressive Crypto Investor": {"Mixed Liquidity Pools": 20.0, "BTC": 30.0, "Blue Chips": 30.0, "High Risk Assets": 20.0},
            "Bitcoin Strategist": {"Mixed Liquidity Pools": 10.0, "BTC": 80.0, "Blue Chips": 8.0, "High Risk Assets": 2.0}
        }

        labels = list(portfolios[investor_profile].keys())
        sizes = list(portfolios[investor_profile].values())
        colors = ['#4B5EAA', '#FFD700', '#32CD32', '#FF4D4D']
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
