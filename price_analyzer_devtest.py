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
    .red-text {
        color: #FF4D4D;
    }
    .green-text {
        color: #32CD32;
    }
    .yellow-text {
        color: #FFD700;
    }
    /* ... (rest of your CSS remains unchanged) */
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Configure your Crypto Asset")
investor_profile = st.sidebar.selectbox(
    "Investor Profile",
    ["Conservative Investor", "Growth Crypto Investor", "Aggressive Crypto Investor", "Bitcoin Strategist"],
    index=0
)
asset_price = st.sidebar.number_input("Current Asset Price ($)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
fear_and_greed = st.sidebar.number_input("Fear and Greed Index (0–100)", min_value=0.0, max_value=100.0, value=50.0)
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
market_cap = parse_market_value(market_cap_input)
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
fdv = parse_market_value(fdv_input)
vol_mkt_cap = st.sidebar.number_input("Vol/Mkt Cap (24h) %", min_value=0.0, value=0.0, step=0.01, format="%.2f")
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

# Define calculate button
calculate = st.sidebar.button("Calculate")

# Helper function
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

# Main content
if calculate:
    if asset_price == 0 or initial_investment == 0:
        st.error("Please enter valid values for Asset Price and Initial Investment (greater than 0).")
    elif market_cap == 0:
        st.error("Please provide Market Cap to proceed with calculations.")
    else:
        # Basic calculations (from your original code)
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

        # Monte Carlo simulation (simplified from your original)
        @st.cache_data
        def run_monte_carlo(initial_investment, growth_rate, fear_and_greed, months, n_simulations=200):
            expected_annual_return = growth_rate / 100
            volatility_value = 0.40 if fear_and_greed == 50 else 0.75 if fear_and_greed <= 24 else 0.60 if fear_and_greed <= 49 else 0.50 if fear_and_greed <= 74 else 0.70
            monthly_volatility = volatility_value / np.sqrt(12) or 0.1
            simulations = []
            sim_paths = []
            for _ in range(n_simulations):
                monthly_returns = np.random.normal(expected_annual_return/12, monthly_volatility, months)
                sim_prices = [initial_investment]
                for i in range(months):
                    sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
                simulations.append(sim_prices[-1])
                sim_paths.append(sim_prices)
            return simulations, sim_paths, monthly_returns

        simulations, sim_paths, all_monthly_returns = run_monte_carlo(initial_investment, growth_rate, fear_and_greed, months)
        worst_case = np.percentile(simulations, 10)
        expected_case = np.mean(simulations)
        best_case = np.percentile(simulations, 90)
        worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
        peak = np.maximum.accumulate(worst_path)
        drawdowns = (peak - worst_path) / peak
        max_drawdown = max(drawdowns) * 100

        # Dilution and supply
        circulating_supply = market_cap / asset_price if total_supply > 0 and market_cap > 0 and asset_price > 0 else 0
        dilution_ratio = 100 * (1 - (circulating_supply / total_supply)) if total_supply > 0 else 0
        dilution_text = "✓ Low dilution risk" if dilution_ratio < 20 else "⚠ Moderate dilution risk" if dilution_ratio < 50 else "⚠ High dilution risk" if dilution_ratio > 0 else "⚠ FDV not provided"
        supply_ratio = (circulating_supply / total_supply) * 100 if total_supply > 0 else 0
        supply_concentration_text = "⚠ High risk" if supply_ratio < 20 else "⚠ Moderate risk" if supply_ratio < 50 else "✓ Low risk" if supply_ratio > 0 else "⚠ FDV not provided"

        def format_supply(value):
            if value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"{value / 1_000_000:.2f}M"
            elif value >= 1_000:
                return f"{value / 1_000:.2f}K"
            else:
                return f"{value:,.0f}"
        max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

        # Market cap growth
        projected_price = asset_projections[-1]
        projected_mcap = market_cap * (projected_price / asset_price)
        btc_mcap = btc_price * 21_000_000
        mcap_vs_btc = (projected_mcap / btc_mcap) * 100 if btc_mcap > 0 else 0
        mcap_vs_btc_max = (projected_price * total_supply / btc_mcap) * 100 if total_supply > 0 and btc_mcap > 0 else 0

        # Ratios
        annual_return = (asset_values[-1] / initial_investment - 1)
        rf_annual = risk_free_rate / 100
        std_dev = np.std(simulations) / initial_investment
        sharpe_ratio = (annual_return - rf_annual) / std_dev if std_dev > 0 else 0
        negative_returns = [r for r in all_monthly_returns if r < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino_ratio = (annual_return - rf_annual) / downside_std if downside_std > 0 else 0
        hurdle_rate = (risk_free_rate + 6) * 2
        asset_vs_hurdle = growth_rate - hurdle_rate
        hurdle_label = "Strong Outperformance" if asset_vs_hurdle >= 20 else "Moderate Outperformance" if asset_vs_hurdle >= 0 else "Below Hurdle"
        hurdle_color = "green-text" if asset_vs_hurdle >= 20 else "yellow-text" if asset_vs_hurdle >= 0 else "red-text"

        # Composite score (simplified)
        scores = {
            'Max Drawdown': 100 if max_drawdown < 30 else 50 if max_drawdown < 50 else 0,
            'Dilution Risk': 100 if dilution_ratio < 20 else 50 if dilution_ratio < 50 else 0,
            'Supply Concentration': 0 if supply_ratio < 20 else 50 if supply_ratio < 50 else 100,
            'MCap Growth': 100 if mcap_vs_btc < 1 else 50 if mcap_vs_btc < 5 else 0,
            'Sharpe Ratio': 100 if sharpe_ratio > 1 else 50 if sharpe_ratio > 0 else 0,
            'Sortino Ratio': 100 if sortino_ratio > 1 else 50 if sortino_ratio > 0 else 0,
            'CertiK Score': 100 if certik_score >= 70 else 50 if certik_score >= 40 else 0,
            'Market Cap': 100 if market_cap >= 1_000_000_000 else 50 if market_cap >= 10_000_000 else 0,
            'Fear and Greed': 100 if fear_and_greed <= 24 else 75 if fear_and_greed <= 49 else 50 if fear_and_greed == 50 else 25 if fear_and_greed <= 74 else 0,
            'Liquidity': 0 if vol_mkt_cap < 1 else 50 if vol_mkt_cap <= 5 else 100
        }
        weights = {
            "Conservative Investor": {k: 1.0 for k in scores.keys()},
            "Growth Crypto Investor": {k: 1.0 for k in scores.keys()},
            "Aggressive Crypto Investor": {k: 1.0 for k in scores.keys()},
            "Bitcoin Strategist": {k: 1.0 for k in scores.keys()}
        }
        weighted_sum = sum(scores[k] * weights[investor_profile][k] for k in scores)
        total_weight = sum(weights[investor_profile].values())
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0
        return_to_hurdle_ratio = min((growth_rate / hurdle_rate) if hurdle_rate > 0 else 1, 3)
        risk_adjusted_score = min(composite_score * return_to_hurdle_ratio, 100)

        # Key Metrics section
        st.subheader("Key Metrics")
        roi = ((asset_values[-1] / initial_investment) - 1) * 100
        investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

        st.markdown("""
            <script>
            function toggleDesc(metricId) {
                var desc = document.getElementById(metricId);
                if (desc.style.display === "none" || desc.style.display === "") {
                    desc.style.display = "block";
                } else {
                    desc.style.display = "none";
                }
            }
            </script>
        """, unsafe_allow_html=True)

        st.markdown("### Investment Returns and Risk-Adjusted Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💰 Investment Value (1 Year) 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-investment')">?</span>
                </div>
                <div class="metric-value">${asset_values[-1]:,.2f}<br>({investment_multiple:.2f}x)</div>
                <div id="desc-investment" class="metric-desc" style="display: none;">
                    Potential value of your ${initial_investment:,.2f} investment in 12 months.<br>
                    <b>Insight:</b> {'Lock in profits if reached.' if roi > 50 else 'Hold and monitor.' if roi >= 0 else 'Reassess investment.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Sortino Ratio 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-sortino')">?</span>
                </div>
                <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                <div id="desc-sortino" class="metric-desc" style="display: none;">
                    Return per unit of downside risk.<br>
                    <b>Insight:</b> {'Proceed confidently.' if sortino_ratio > 1 else 'Allocate to stable assets.' if sortino_ratio >= 0 else 'Shift to stable assets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📊 Sharpe Ratio 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-sharpe')">?</span>
                </div>
                <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                <div id="desc-sharpe" class="metric-desc" style="display: none;">
                    Return per unit of risk.<br>
                    <b>Insight:</b> {'Proceed confidently.' if sharpe_ratio > 1 else 'Consider safer assets.' if sharpe_ratio >= 0 else 'Shift to stablecoins.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Risk Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📉 Max Drawdown 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-drawdown')">?</span>
                </div>
                <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                <div id="desc-drawdown" class="metric-desc" style="display: none;">
                    Largest potential loss in a worst-case scenario.<br>
                    <b>Insight:</b> {'Minimal action needed.' if max_drawdown < 30 else f'Set stop-loss at {max_drawdown:.2f}%.' if max_drawdown <= 50 else 'Reduce exposure.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">⚖️ Dilution Risk 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-dilution')">?</span>
                </div>
                <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                <div id="desc-dilution" class="metric-desc" style="display: none;">
                    {dilution_text}<br>
                    <b>Insight:</b> {'Minimal action needed.' if dilution_ratio < 20 else 'Check unlock schedule.' if dilution_ratio <= 50 else 'Reduce position.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">🛡️ Supply Concentration Risk 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-supply')">?</span>
                </div>
                <div class="metric-value {'red-text' if supply_ratio < 20 else 'yellow-text' if supply_ratio < 50 else 'green-text'}">{supply_ratio:.2f}%</div>
                <div id="desc-supply" class="metric-desc" style="display: none;">
                    {supply_concentration_text}<br>
                    <b>Insight:</b> {'Monitor whale activity.' if supply_ratio < 20 else 'Be cautious of large holders.' if supply_ratio < 50 else 'Proceed confidently.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Market Metrics")
        mcap_max_note = f"Using Total Supply ({max_supply_display}), projected market cap would be {mcap_vs_btc_max:.2f}% of BTC’s." if total_supply > 0 else "Total Supply not provided."
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 MCap Growth Plausibility 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-mcap')">?</span>
                </div>
                <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                <div id="desc-mcap" class="metric-desc" style="display: none;">
                    {mcap_max_note}<br>
                    <b>Insight:</b> {'Proceed confidently.' if mcap_vs_btc < 1 else 'Adjust growth rate.' if mcap_vs_btc <= 5 else 'Focus on realistic targets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        supply_volatility_note = f"Total Supply: {max_supply_display}." if total_supply > 0 else "Total Supply not provided."
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">💧 Liquidity (Vol/Mkt Cap 24h) 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-liquidity')">?</span>
                </div>
                <div class="metric-value {'red-text' if vol_mkt_cap < 1 else 'green-text' if vol_mkt_cap > 5 else 'yellow-text'}">{vol_mkt_cap:.2f}%</div>
                <div id="desc-liquidity" class="metric-desc" style="display: none;">
                    {supply_volatility_note}<br>
                    <b>Insight:</b> {'Use limit orders, monitor volume.' if vol_mkt_cap < 1 else 'Limit orders for small trades.' if vol_mkt_cap <= 5 else 'Trade confidently with stop-loss.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Comparative Metrics")
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Hurdle Rate vs. Bitcoin 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-hurdle')">?</span>
                </div>
                <div class="metric-value {hurdle_color}">{asset_vs_hurdle:.2f}%<br>({hurdle_label})</div>
                <div id="desc-hurdle" class="metric-desc" style="display: none;">
                    Growth vs. minimum return to beat Bitcoin.<br>
                    <b>Insight:</b> {'Favor this asset.' if asset_vs_hurdle >= 20 else 'Balance with Bitcoin.' if asset_vs_hurdle >= 0 else 'Increase Bitcoin allocation.'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">🎯 Risk-Adjusted Return Score 
                    <span style="cursor: pointer; color: #A9A9A9; font-size: 16px;" onclick="toggleDesc('desc-risk-adjusted')">?</span>
                </div>
                <div class="metric-value {'green-text' if risk_adjusted_score >= 70 else 'yellow-text' if risk_adjusted_score >= 40 else 'red-text'}">{risk_adjusted_score:.1f}</div>
                <div id="desc-risk-adjusted" class="metric-desc" style="display: none;">
                    Combines risk and return.<br>
                    <b>Insight:</b> {'Diversify confidently.' if risk_adjusted_score >= 70 else 'Small position, diversify.' if risk_adjusted_score >= 40 else 'Explore safer assets.'}
                </div>
            </div>
        """, unsafe_allow_html=True)
