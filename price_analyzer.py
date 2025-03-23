import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom CSS for styling
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
        font-size: 28px;
        font-weight: bold;
        width: 20%;
        min-width: 100px;
    }
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 100px;
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
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
    }
    .risk-red {
        background-color: #FF4D4D;
    }
    .risk-yellow {
        background-color: #FFD700;
    }
    .risk-green {
        background-color: #32CD32;
    }
    .proj-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 620px;
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
        .metric-desc {
            max-height: 150px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Display the logo using the raw URL
st.markdown(
    f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="large-logo" width="600"></div>',
    unsafe_allow_html=True
)

# Title
st.title("Arta Crypto Valuations - Know the Price. Master the Risk.")

# Introduction and Disclaimer
st.markdown("""
Arta means "wealth" in Indonesian — and that's exactly what this tool is built to help you understand and protect.  
Whether you're trading, investing, or strategizing, Arta gives you fast, accurate insights into token prices, profit margins, and portfolio risk.  
Run scenarios, test your assumptions, and sharpen your edge — all in real time.  
**Arta: Know the Price. Master the Risk.**
""")

st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
**Instructions**: To get started, visit <a href="https://coinmarketcap.com" target="_blank">coinmarketcap.com</a> to find your asset’s current price, market cap, circulating supply, fully diluted valuation (FDV), 24h trading volume, Vol/Mkt Cap (24h) %, and Bitcoin’s price. Ensure these values are up-to-date, as they directly impact metrics like MCap Growth Plausibility and Liquidity. Visit <a href="https://certik.com" target="_blank">certik.com</a> for the asset’s CertiK security score. Enter the values below and adjust growth rates as needed.
""", unsafe_allow_html=True)

st.sidebar.header("Input Parameters")

# Function to parse MCap, FDV, and Circulating Supply inputs
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
volatility = st.sidebar.number_input(
    "Asset Volatility % (Annual) [Optional]",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    help="Enter the asset's annual volatility (e.g., 50% for AVAX). Leave as 0 to derive volatility from the Fear and Greed Index."
)
st.sidebar.markdown(
    "**Note**: If Asset Volatility is not provided (left as 0), it will default based on the Fear and Greed Index: "
    "Extreme Fear (≤ 24): 75%, Fear (25–49): 60%, Neutral (50): 40%, Greed (51–74): 50%, Extreme Greed (≥ 75): 70%. "
    "These defaults reflect typical crypto market volatility under different sentiment conditions."
)
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
st.sidebar.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")
fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0)
st.sidebar.markdown(
    "**Note**: Find the current Fear and Greed Index on <a href='https://coinmarketcap.com' target='_blank'>coinmarketcap.com</a>. Enter 50 if unavailable (neutral sentiment).",
    unsafe_allow_html=True
)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
market_cap = parse_market_value(market_cap_input)
st.sidebar.markdown("**Note**: Enter values as shorthand (e.g., 67b for 67 billion, 500m for 500 million, 1.5k for 1,500) or full numbers (e.g., 67,000,000,000). Commas are optional. Leave blank if providing Circulating Supply.")
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
fdv = parse_market_value(fdv_input)
circulating_supply_input = st.sidebar.text_input("Circulating Supply (Tokens)", value="")
circulating_supply = parse_market_value(circulating_supply_input)
st.sidebar.markdown("**Note**: Find the Circulating Supply on CoinMarketCap under the asset’s details (e.g., 414.73M for AVAX). Enter as shorthand (e.g., 414.73m for 414.73 million) or full numbers (e.g., 414,730,000). Used to calculate Market Cap if not provided.")
vol_mkt_cap = st.sidebar.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")
st.sidebar.markdown("**Note**: Find the Vol/Mkt Cap (24h) % directly on CoinMarketCap under the asset’s details (e.g., 1.94% for AVAX). This measures the 24h trading volume as a percentage of the market cap.")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

# Investor Profile Selector
investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
    index=0
)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Validation check for critical inputs
    if asset_price == 0 or initial_investment == 0:
        st.error("Please enter valid values for Asset Price and Initial Investment (greater than 0).")
    elif market_cap == 0 and (circulating_supply == 0 or asset_price == 0):
        st.error("Please provide either Market Cap or both Circulating Supply and Asset Price to calculate Market Cap.")
    else:
        # Calculate Market Cap if not provided
        if market_cap == 0 and circulating_supply > 0 and asset_price > 0:
            market_cap = circulating_supply * asset_price

        # Calculate the implied 24h trading volume for the Liquidity metric card
        trading_volume = (vol_mkt_cap / 100) * market_cap if market_cap > 0 else 0

        # Calculations
        months = 12
        asset_monthly_rate = (1 + growth_rate/100) ** (1/12) - 1
        btc_monthly_rate = (1 + btc_growth/100) ** (1/12) - 1
        rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
        
        # Price projections
        asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
        btc_projections = [btc_price * (1 + btc_monthly_rate) ** i for i in range(months + 1)]
        rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
        
        # Investment value projections
        asset_values = [initial_investment * p / asset_price for p in asset_projections]
        btc_values = [initial_investment * p / btc_price for p in btc_projections]
        
        # Monte Carlo Simulation with caching
        @st.cache_data
        def run_monte_carlo(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200):
            expected_annual_return = growth_rate / 100
            
            # If volatility is not provided (0), derive from Fear and Greed
            if volatility == 0:
                if fear_and_greed <= 24:
                    volatility_value = 0.75  # Extreme Fear: 75%
                elif fear_and_greed <= 49:
                    volatility_value = 0.60  # Fear: 60%
                elif fear_and_greed == 50:
                    volatility_value = 0.40  # Neutral: 40%
                elif fear_and_greed <= 74:
                    volatility_value = 0.50  # Greed: 50%
                else:
                    volatility_value = 0.70  # Extreme Greed: 70%
            else:
                volatility_value = volatility / 100
            
            # Adjust volatility based on Fear and Greed
            if fear_and_greed <= 49:
                volatility_adjustment = 1.2
            elif fear_and_greed > 50:
                volatility_adjustment = 1.1
            else:
                volatility_adjustment = 1.0
            adjusted_volatility = volatility_value * volatility_adjustment
            monthly_volatility = adjusted_volatility / np.sqrt(12) if adjusted_volatility > 0 else 0.1
            
            # Center the return distribution around the expected growth rate
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

        simulations, sim_paths, all_monthly_returns = run_monte_carlo(initial_investment, growth_rate, volatility, months, fear_and_greed, n_simulations=200)
        
        # Use percentiles for worst, expected, and best cases
        worst_case = np.percentile(simulations, 10)  # 10th percentile
        expected_case = np.mean(simulations)
        best_case = np.percentile(simulations, 90)  # 90th percentile
        
        # Max Drawdown on worst-case Monte Carlo scenario
        worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
        peak = np.maximum.accumulate(worst_path)
        drawdowns = (peak - worst_path) / peak
        max_drawdown = max(drawdowns) * 100

        # Calculate break-even percentage for Max Drawdown
        break_even_percentage = (max_drawdown / (100 - max_drawdown)) * 100

        # Dilution Risk (using Circulating Supply and Total Supply)
        if fdv > 0 and asset_price > 0:
            total_supply = fdv / asset_price
            if total_supply > 0 and circulating_supply > 0:
                dilution_ratio = 100 * (1 - (circulating_supply / total_supply))
            else:
                dilution_ratio = 0
            if dilution_ratio < 20:
                dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
            elif dilution_ratio < 50:
                dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
            else:
                dilution_text = "⚠ High dilution risk: Significant token releases expected."
        else:
            dilution_ratio = 0
            dilution_text = "⚠ FDV or Asset Price not provided, cannot assess dilution risk."

        # MCap Growth Plausibility
        projected_price = asset_projections[-1]
        projected_mcap = market_cap * (projected_price / asset_price)
        btc_mcap = btc_price * 21_000_000  # Bitcoin's total supply
        mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0
        if mcap_vs_btc <= 1:
            mcap_text = "✓ Plausible growth: Small market share needed."
        elif mcap_vs_btc <= 5:
            mcap_text = "⚠ Ambitious growth: Significant market share needed."
        else:
            mcap_text = "⚠ Very ambitious: Large market share required."

        # Sharpe and Sortino Ratios
        annual_return = (asset_values[-1] / initial_investment - 1)  # 12-month return
        rf_annual = risk_free_rate / 100
        std_dev = np.std(simulations) / initial_investment  # Standard deviation of final values
        sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0

        # Downside standard deviation for Sortino
        negative_returns = [r for r in all_monthly_returns if r < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0

        # Hurdle Rate vs. Bitcoin
        hurdle_rate = (risk_free_rate + 6) * 2  # (Risk-Free Rate + 6% inflation) * 2
        asset_vs_hurdle = growth_rate - hurdle_rate  # Difference between crypto asset growth and hurdle rate

        # Determine label and color for Hurdle Rate vs. Bitcoin
        if asset_vs_hurdle >= 20:
            hurdle_label = "Strong Outperformance"
            hurdle_color = "green-text"
        elif asset_vs_hurdle >= 0:
            hurdle_label = "Moderate Outperformance"
            hurdle_color = "yellow-text"
        else:
            hurdle_label = "Below Hurdle"
            hurdle_color = "red-text"

        # Composite Risk Score (including Liquidity)
        scores = {}
        # Max Drawdown
        if max_drawdown < 30:
            scores['Max Drawdown'] = 100
        elif max_drawdown < 50:
            scores['Max Drawdown'] = 50
        else:
            scores['Max Drawdown'] = 0
        
        # Dilution Risk
        if dilution_ratio < 20:
            scores['Dilution Risk'] = 100
        elif dilution_ratio < 50:
            scores['Dilution Risk'] = 50
        else:
            scores['Dilution Risk'] = 0
        
        # MCap Growth Plausibility
        if mcap_vs_btc < 1:
            scores['MCap Growth'] = 100
        elif mcap_vs_btc < 5:
            scores['MCap Growth'] = 50
        else:
            scores['MCap Growth'] = 0
        
        # Sharpe Ratio
        if sharpe_ratio > 1:
            scores['Sharpe Ratio'] = 100
        elif sharpe_ratio > 0:
            scores['Sharpe Ratio'] = 50
        else:
            scores['Sharpe Ratio'] = 0
        
        # Sortino Ratio
        if sortino_ratio > 1:
            scores['Sortino Ratio'] = 100
        elif sortino_ratio > 0:
            scores['Sortino Ratio'] = 50
        else:
            scores['Sortino Ratio'] = 0
        
        # CertiK Score
        certik_adjusted = 50 if certik_score == 0 else certik_score
        if certik_adjusted >= 70:
            scores['CertiK Score'] = 100
        elif certik_adjusted >= 40:
            scores['CertiK Score'] = 50
        else:
            scores['CertiK Score'] = 0
        
        # Market Cap
        if market_cap >= 1_000_000_000:
            scores['Market Cap'] = 100
        elif market_cap >= 10_000_000:
            scores['Market Cap'] = 50
        else:
            scores['Market Cap'] = 0

        # Fear and Greed Index
        if fear_and_greed <= 24:
            scores['Fear and Greed'] = 100  # Extreme Fear: potential buying opportunity
        elif fear_and_greed <= 49:
            scores['Fear and Greed'] = 75   # Fear
        elif fear_and_greed == 50:
            scores['Fear and Greed'] = 50   # Neutral
        elif fear_and_greed <= 74:
            scores['Fear and Greed'] = 25   # Greed
        else:
            scores['Fear and Greed'] = 0    # Extreme Greed: potential correction

        # Liquidity (based on Vol/Mkt Cap 24h)
        if vol_mkt_cap < 1:
            scores['Liquidity'] = 0
        elif vol_mkt_cap <= 5:
            scores['Liquidity'] = 50
        else:
            scores['Liquidity'] = 100

        composite_score = sum(scores.values()) / len(scores)

        # Risk-Adjusted Return Score
        return_to_hurdle_ratio = (growth_rate / hurdle_rate) if hurdle_rate > 0 else 1  # Avoid division by zero
        return_to_hurdle_ratio = min(return_to_hurdle_ratio, 3)  # Cap the ratio at 3
        risk_adjusted_score = composite_score * return_to_hurdle_ratio
        risk_adjusted_score = min(risk_adjusted_score, 100)  # Cap the final score at 100

        # Composite Risk Score Assessment with Fear and Greed Insight
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
                "This asset shows a low overall risk profile, making it a relatively safe investment option. "
                "The projected returns are strong compared to the risk-free rate, with a good balance of reward and risk (Sharpe and Sortino ratios). "
                "Dilution risk is minimal, meaning future token releases are unlikely to significantly impact the price. "
                "The market cap growth is plausible, and the CertiK score indicates solid security. "
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction'}. "
                "Consider allocating a portion of your portfolio to this asset, but always monitor market conditions and diversify to manage any unexpected risks."
            )
        elif composite_score >= 40:
            bg_class = "risk-yellow"
            insight = (
                "This asset has a moderate overall risk profile, suggesting a balanced but cautious approach. "
                f"Key concerns include {'high drawdown risk' if max_drawdown > 50 else 'moderate drawdown risk' if max_drawdown > 30 else ''}"
                f"{', significant dilution risk' if dilution_ratio > 50 else ', moderate dilution risk' if dilution_ratio > 20 else ''}"
                f"{', ambitious market cap growth' if mcap_vs_btc > 5 else ''}"
                f"{', low risk-adjusted returns' if sharpe_ratio < 0 or sortino_ratio < 0 else ''}"
                f"{', low liquidity' if vol_mkt_cap < 1 else ', moderate liquidity' if vol_mkt_cap <= 5 else ''}"
                f"{', and a concerning CertiK score' if certik_adjusted < 40 else ''}. "
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction'}. "
                "You might consider a smaller position in this asset while diversifying across other investments to mitigate these risks. "
                "Keep an eye on token unlock schedules, trading volume trends, and security updates to reassess your position."
            )
        else:
            bg_class = "risk-red"
            insight = (
                "This asset carries a high overall risk profile, indicating significant challenges for potential investors. "
                f"Key issues include {'extreme drawdown risk' if max_drawdown > 50 else 'high drawdown risk' if max_drawdown > 30 else ''}"
                f"{', high dilution risk from future token releases' if dilution_ratio > 50 else ''}"
                f"{', unrealistic market cap growth expectations' if mcap_vs_btc > 5 else ''}"
                f"{', poor risk-adjusted returns' if sharpe_ratio < 0 or sortino_ratio < 0 else ''}"
                f"{', low liquidity increasing slippage risk' if vol_mkt_cap < 1 else ''}"
                f"{', and a low CertiK score indicating security concerns' if certik_adjusted < 40 else ''}. "
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity despite the high risk due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction, adding to the risk'}. "
                "Proceed with caution—consider waiting for better entry points, improved security scores, higher liquidity, or more favorable market conditions. "
                "Alternatively, explore safer assets with stronger fundamentals to protect your capital."
            )

        # Composite Risk Score
        st.subheader("Composite Risk Assessment")
        st.markdown(f"""
            <div class="risk-assessment {bg_class}">
                <div style="font-size: 20px; font-weight: bold; color: #333;">Composite Risk Score: <span style="color: #333;">{composite_score:.1f}</span></div>
                <div style="font-size: 14px; margin-top: 5px; color: #333;">{insight}</div>
            </div>
        """, unsafe_allow_html=True)

        # Key Metrics (single column with horizontal cards)
        st.subheader("Key Metrics")

        # Card 1: Investment Value
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💰 Investment Value (1 Year)</div>
                <div class="metric-value">${asset_values[-1]:,.2f}</div>
                <div class="metric-desc">This is how much your ${initial_investment:,.2f} investment could be worth in 12 months, based on the expected growth rate you provided. It shows the potential reward if the asset grows as expected.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 2: Max Drawdown
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Max Drawdown</div>
                <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                <div class="metric-desc">Derived from the Simplified Monte Carlo Analysis, this shows the biggest potential loss you might face in a worst-case scenario over 12 months. A higher percentage means more risk of losing value during a market dip. To recover from this drawdown, your investment would need to increase by {break_even_percentage:.2f}% from its lowest point.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 3: Sharpe Ratio
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📊 Sharpe Ratio</div>
                <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                <div class="metric-desc">This measures how much extra return you get for the risk you're taking. Above 1 is good—it means you're getting a nice reward for the risk. Below 0 means the risk might not be worth it.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 4: Dilution Risk
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">⚖️ Dilution Risk</div>
                <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                <div class="metric-desc">This shows the percentage of tokens yet to be released, which could dilute the value of your investment by flooding the market and lowering the price. A higher percentage indicates greater risk of price drops due to future token releases.<br>
                <b>Actionable Insight:</b><br>
                - <b>Low Risk (<20%)</b>: Minimal dilution expected—proceed with confidence but monitor for unexpected token releases.<br>
                - <b>Moderate Risk (20–50%)</b>: Be cautious. Research the token’s unlock schedule on platforms like TokenUnlocks or the project’s whitepaper to understand release timelines. Consider reducing your position size if large unlocks are imminent.<br>
                - <b>High Risk (>50%)</b>: Significant dilution risk. Prioritize assets with lower dilution risk or wait for token releases to occur and stabilize before investing. If you hold this asset, monitor market reactions to unlocks closely and be prepared for price volatility.
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 5: MCap Growth Plausibility
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 MCap Growth Plausibility</div>
                <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                <div class="metric-desc">This measures the asset’s projected market cap as a percentage of Bitcoin’s market cap to assess if the expected growth is realistic. A high percentage means the asset would need to capture a large market share, which may be challenging.<br>
                <b>Actionable Insight:</b><br>
                - <b>Plausible (<1%)</b>: The projected growth is realistic, requiring only a small market share. This asset may be a safer bet for achieving your growth expectations.<br>
                - <b>Ambitious (1–5%)</b>: The growth is possible but requires significant adoption. Compare this asset to similar projects (e.g., on CoinMarketCap) to see if others in its category have achieved this market share. Consider diversifying to reduce risk.<br>
                - <b>Very Ambitious (>5%)</b>: The growth is highly ambitious and may be unrealistic without major catalysts (e.g., partnerships, adoption). Reassess your growth rate assumption—try lowering it in the input to see if the projection becomes more plausible. Alternatively, focus on assets with more achievable growth targets.<br>
                <b>Context:</b> For reference, top altcoins like Ethereum typically have a market cap around 20–25% of Bitcoin’s, while projects like BNB are around 5–7% (based on early 2025 data). If this is a layer-1 blockchain, compare it to projects like Solana or Avalanche on CoinMarketCap to gauge if this market share is achievable.
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 6: Sortino Ratio
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Sortino Ratio</div>
                <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                <div class="metric-desc">This focuses on the risk of losing money (downside risk). Above 1 means you're getting good returns compared to the chance of losses. Below 0 suggests the risk of losing money might outweigh the gains.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 7: Hurdle Rate vs. Bitcoin
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Hurdle Rate vs. Bitcoin</div>
                <div class="metric-value {hurdle_color}">{asset_vs_hurdle:.2f}% ({hurdle_label})</div>
                <div class="metric-desc">This shows how much your asset’s expected growth ({growth_rate:.2f}%) beats—or falls short of—the minimum return needed to justify its risk compared to holding Bitcoin (hurdle rate: {hurdle_rate:.2f}%). Your asset {'exceeds' if asset_vs_hurdle >= 0 else 'falls short of'} the hurdle by {abs(asset_vs_hurdle):.2f}% ({hurdle_label}), making it a {'potentially better choice than Bitcoin' if asset_vs_hurdle >= 0 else 'less attractive option compared to Bitcoin'}. Bitcoin has an expected growth of {btc_growth:.2f}%. A value above 20% indicates a strong case for choosing this asset over Bitcoin, while 0–20% suggests a moderate case. Below 0% means Bitcoin is likely the safer choice with less risk.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 8: Risk-Adjusted Return Score
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">🎯 Risk-Adjusted Return Score</div>
                <div class="metric-value {'green-text' if risk_adjusted_score >= 70 else 'yellow-text' if risk_adjusted_score >= 40 else 'red-text'}">{risk_adjusted_score:.1f}</div>
                <div class="metric-desc">This score combines the Composite Risk Score with the asset’s expected return relative to the hurdle rate (stablecoin pool risk-free rate plus 6% inflation, doubled). A higher score means a better balance of risk and reward. Below 40 indicates a high-risk asset with insufficient returns to justify the risk—a potential gamble.</div>
            </div>
        """, unsafe_allow_html=True)

        # Card 9: Liquidity
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💧 Liquidity (Vol/Mkt Cap 24h)</div>
                <div class="metric-value {'red-text' if vol_mkt_cap < 1 else 'green-text' if vol_mkt_cap > 5 else 'yellow-text'}">{vol_mkt_cap:.2f}%</div>
                <div class="metric-desc">This measures the 24-hour trading volume as a percentage of the asset’s market cap, indicating liquidity and market activity. {'With a market cap of ${market_cap:,.2f}, this percentage means ${trading_volume:,.2f} was traded in the last 24 hours.' if market_cap > 0 else 'Market cap not provided, cannot calculate trading volume.'} A higher percentage means better liquidity (easier to buy/sell without impacting the price), but can also signal volatility or speculative trading.<br>
                <b>Why It Matters:</b> Liquidity affects how easily you can enter or exit positions. Low liquidity can lead to slippage (price changes when you trade), while high liquidity may indicate speculative activity.<br>
                <b>Actionable Insight:</b><br>
                - <b>Low (<1%)</b>: Very low liquidity—use limit orders and stick to smaller trades to avoid slippage. Consider waiting for higher volume to reduce manipulation risk.<br>
                - <b>Moderate (1–5%)</b>: Reasonable liquidity, but larger trades may cause slippage. {'For a large-cap asset like this (market cap > $1B), this level is on the lower end. Suitable for retail-sized trades (e.g., $10k–$100k); avoid large trades (e.g., $1M+) to minimize price impact. Monitor volume trends on CoinMarketCap for signs of growing interest, especially during market uptrends or after news like network upgrades.' if market_cap >= 1_000_000_000 else 'Suitable for smaller positions; avoid large trades to minimize slippage. Monitor volume trends on CoinMarketCap for signs of growing interest.'}<br>
                - <b>High (>5%)</b>: Strong liquidity, good for larger trades. Watch for price swings due to speculative trading—use stop-loss orders and check for news driving the volume.<br>
                <b>Risk Alert:</b> {'High risk of price manipulation due to low volume. Watch for sudden price spikes or dumps (e.g., pump-and-dump schemes).' if vol_mkt_cap < 1 else 'Moderate risk of volatility. For a large-cap asset, this liquidity level suggests potential price swings during market stress. Be cautious during bear markets or low-volume periods.' if vol_mkt_cap <= 5 and market_cap >= 1_000_000_000 else 'Moderate risk of volatility. The asset may experience price swings during market stress due to relatively low trading activity.' if vol_mkt_cap <= 5 else 'Potential for speculative trading. High volume may be driven by short-term hype, increasing the risk of volatility or a price correction.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Price Projections
        st.subheader("Projected Investment Value Over Time")
        st.markdown("**Note**: The projected value reflects the growth of your initial investment, adjusted for expected price changes.")
        
        # Table for months 0, 3, 6, 12 with enhanced styling
        proj_data = {
            "Time Period (Months)": [0, 3, 6, 12],
            "Projected Value ($)": [asset_values[i] for i in [0, 3, 6, 12]],
            "ROI (%)": [((asset_values[i] / initial_investment) - 1) * 100 for i in [0, 3, 6, 12]]
        }
        proj_df = pd.DataFrame(proj_data)

        # Apply conditional formatting to ROI column
        def color_roi(val):
            if val > 0:
                return 'color: #32CD32'
            elif val < 0:
                return 'color: #FF4D4D'
            else:
                return 'color: #A9A9A9'

        styled_proj_df = proj_df.style.set_table_attributes('class="proj-table"').format({
            "Projected Value ($)": "${:,.2f}",
            "ROI (%)": "{:.2f}%"
        }).applymap(color_roi, subset=["ROI (%)"])
        st.table(styled_proj_df)

        # Line Plot
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

        # Simplified Monte Carlo Analysis
        st.subheader("Simplified Monte Carlo Analysis")
        st.markdown("""
        The **Simplified Monte Carlo Analysis** helps you understand the range of potential outcomes for your investment over the next 12 months by simulating 200 different scenarios. We generate random price paths based on your inputted volatility (or a default derived from the Fear and Greed Index) and expected growth rate, with monthly variations to reflect market uncertainty. The Fear and Greed Index adjusts the distribution of returns: a fearful market (≤ 49) skews returns towards the lower end (reflecting higher downside risk but potential for recovery), while a greedy market (> 50) skews returns higher (reflecting speculative growth but risk of corrections). To keep results realistic, we cap the maximum return at your inputted price projection plus volatility. This analysis is crucial in crypto investing as it highlights the best-case, expected-case, and worst-case scenarios, helping you assess risk and make informed decisions in a highly volatile market.
        """)
        st.markdown("""
        - **Expected Case**: The average result across all simulations, adjusted for market sentiment via the Fear and Greed Index.  
        - **Best Case**: The 90th percentile (20th highest of 200 runs)—a strong outcome, not the absolute best.  
        - **Worst Case**: The 10th percentile (20th lowest of 200 runs)—a pessimistic but realistic scenario.  
        This gives you a practical snapshot of your investment’s potential over the next year.
        """)
        
        # Table
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

        # Histogram
        with st.spinner("Generating chart..."):
            plt.figure(figsize=(10, 6))
            sns.histplot(simulations, bins=50, color='#A9A9A9')
            plt.axvline(worst_case, color='#FF4D4D', label='Worst Case', linewidth=2)
            plt.axvline(expected_case, color='#FFD700', label='Expected Case', linewidth=2)
            plt.axvline(best_case, color='#32CD32', label='Best Case', linewidth=2)
            plt.axvline(initial_investment, color='#1E2A44', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
            plt.title("Simplified Monte Carlo Analysis - 12 Month Investment Value")
            plt.xlabel("Value ($)")
            plt.ylabel("Frequency")
            plt.legend()
            st.pyplot(plt)
            plt.clf()

        # Suggested Portfolio Structure
        st.subheader("Suggested Portfolio Structure")
        st.markdown(f"Based on your selected investor profile: **{investor_profile}**")

        # Portfolio allocations
        portfolios = {
            "Conservative Investor": {
                "Stablecoin Liquidity Pools": 50.0,
                "BTC": 40.0,
                "Blue Chips": 8.0,
                "High Risk Assets": 2.0
            },
            "Growth Crypto Investor": {
                "Mixed Liquidity Pools": 30.0,
                "BTC": 30.0,
                "Blue Chips": 30.0,
                "High Risk Assets": 10.0
            },
            "Aggressive Crypto Investor": {
                "Mixed Liquidity Pools": 20.0,
                "BTC": 30.0,
                "Blue Chips": 30.0,
                "High Risk Assets": 20.0
            },
            "Bitcoin Strategist": {
                "Mixed Liquidity Pools": 10.0,
                "BTC": 80.0,
                "Blue Chips": 8.0,
                "High Risk Assets": 2.0
            }
        }

        # Pie chart for the selected portfolio
        labels = list(portfolios[investor_profile].keys())
        sizes = list(portfolios[investor_profile].values())
        colors = ['#4B5EAA', '#FFD700', '#32CD32', '#FF4D4D']
        explode = (0.05, 0, 0, 0)  # Slightly explode the first slice

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
        plt.title(f"Portfolio Allocation for {investor_profile}")
        st.pyplot(plt)
        plt.clf()

        # Explanations and Insights
        st.markdown("""
        ### Understanding the Asset Classes
        - **Stablecoin Liquidity Pools**: These are pools like USDT/USDC that provide steady returns (average 5–10% annually) with low volatility. They’re great for preserving capital during market downturns.
        - **Mixed Liquidity Pools**: These combine stablecoins with volatile assets (e.g., ETH/USDT), offering higher returns (10–20% annually) but with moderate risk due to price swings.
        - **BTC**: Bitcoin acts as an anchor in your portfolio, offering stability compared to altcoins and long-term growth potential. However, it can still face significant drawdowns (30–50%) in bear markets.
        - **Blue Chips**: Large market cap assets like ETH or BNB with established ecosystems. They have lower volatility than small caps (20–40% drawdowns) but still carry market risk.
        - **High Risk Assets**: Low market cap assets with high growth potential (100%+ returns) but also high risk of failure or extreme volatility (50–80% drawdowns).

        ### Why Balance Matters
        Diversifying across these asset classes helps reduce major drawdowns. For example, stablecoin LPs and BTC can offset losses from high-risk assets during market crashes. Higher allocations to high-risk assets increase potential returns but also the likelihood of significant losses. Balancing your portfolio ensures you can weather market volatility while still capturing upside potential.

        ### Actionable Risk Management Insights
        - **Rebalance Regularly**: Adjust your portfolio periodically to maintain your target allocation, especially after large price movements.
        - **Monitor Market Conditions**: Reduce exposure to high-risk assets during bear markets and increase stablecoin allocations for safety.
        - **Use Protective Strategies**: Consider stop-loss orders or hedging to limit losses during sudden market drops.
        - **Maintain Liquidity**: Keep a portion in stable assets to ensure you have funds available during market crashes, allowing you to buy opportunities at lower prices.
        """)
