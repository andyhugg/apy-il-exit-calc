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
        max-width: 300px;
        min-height: 180px;
    }
    .metric-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-desc {
        font-size: 12px;
        color: #A9A9A9;
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
    .risk-assessment {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
        margin: 0 auto;
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
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background: linear-gradient(to bottom, #1E2A44, #4B5EAA);
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
    .proj-table td {
        background: rgba(255, 255, 255, 0.05);
    }
    .disclaimer {
        border: 2px solid #FF4D4D;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Arta Crypto Valuations - Know the Price. Master the Risk.")

# Introduction and Disclaimer
st.markdown("""
Arta means "wealth" in Indonesian — and that's exactly what this tool is built to help you understand and protect. Whether you're trading, investing, or strategizing, Arta gives you fast, accurate insights into token prices, profit margins, and portfolio risk. Run scenarios, test your assumptions, and sharpen your edge — all in real time. - Arta: Know the Price. Master the Risk.
""")

st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
**Instructions**: To get started, visit <a href="https://coingecko.com" target="_blank">coingecko.com</a> to find your asset’s current price, market cap, fully diluted valuation (FDV), and Bitcoin’s price. Visit <a href="https://certik.com" target="_blank">certik.com</a> for the asset’s CertiK security score. Enter the values below and adjust growth rates as needed.
""", unsafe_allow_html=True)

st.sidebar.header("Input Parameters")

# Function to parse MCap and FDV inputs
def parse_market_value(value_str):
    try:
        # Remove commas and convert to lowercase
        value_str = value_str.replace(",", "").lower()
        # Handle suffixes (b, m, k)
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
volatility = st.sidebar.number_input("Asset Volatility % (Annual)", min_value=0.0, max_value=100.0, value=0.0)
certik_score = st.sidebar.number_input("CertiK Score (0–100)", min_value=0.0, max_value=100.0, value=0.0)
st.sidebar.markdown("**Note**: Enter 0 if no CertiK score is available; this will default to a neutral score of 50.")
growth_rate = st.sidebar.number_input("Expected Growth Rate % (Annual)", min_value=-100.0, value=0.0)
market_cap_input = st.sidebar.text_input("Current Market Cap ($)", value="")
market_cap = parse_market_value(market_cap_input)
st.sidebar.markdown("**Note**: Enter values as shorthand (e.g., 67b for 67 billion, 500m for 500 million, 1.5k for 1,500) or full numbers (e.g., 67,000,000,000). Commas are optional.")
fdv_input = st.sidebar.text_input("Fully Diluted Valuation (FDV) ($)", value="")
fdv = parse_market_value(fdv_input)
initial_investment = st.sidebar.number_input("Initial Investment Amount ($)", min_value=0.0, value=0.0)
btc_price = st.sidebar.number_input("Current Bitcoin Price ($)", min_value=0.0, value=0.0)
btc_growth = st.sidebar.number_input("Bitcoin Expected Growth Rate % (12 months)", min_value=-100.0, value=0.0)
risk_free_rate = st.sidebar.number_input("Risk-Free Rate % (Stablecoin Pool)", min_value=0.0, value=0.0)

calculate = st.sidebar.button("Calculate")

# Main content
if calculate:
    # Validation check for critical inputs
    if asset_price == 0 or initial_investment == 0:
        st.error("Please enter valid values for Asset Price and Initial Investment (greater than 0).")
    else:
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
        
        # Monte Carlo Simulation with capped returns
        n_simulations = 200
        max_annual_return = growth_rate / 100  # User-specified max return (e.g., 50% = 0.5)
        monthly_volatility = volatility / 100 / np.sqrt(12) if volatility > 0 else 0.1  # Default to 10% if volatility is 0
        monthly_expected_return = asset_monthly_rate
        simulations = []
        sim_paths = []
        all_monthly_returns = []
        
        for _ in range(n_simulations):
            # Generate annual return between -volatility and +max_annual_return
            annual_return = np.random.uniform(-volatility/100, max_annual_return)
            # Distribute the annual return across months with some variation
            monthly_base_return = (1 + annual_return) ** (1/12) - 1
            monthly_returns = np.random.normal(monthly_base_return, monthly_volatility/2, months)
            sim_prices = [initial_investment]
            for i in range(months):
                sim_prices.append(sim_prices[-1] * (1 + monthly_returns[i]))
            # Cap the final value to ensure it doesn't exceed the max return
            max_allowed_value = initial_investment * (1 + max_annual_return)
            sim_prices[-1] = min(sim_prices[-1], max_allowed_value)
            simulations.append(sim_prices[-1])
            sim_paths.append(sim_prices)
            all_monthly_returns.extend(monthly_returns)
        
        # Use percentiles for worst, expected, and best cases
        worst_case = np.percentile(simulations, 10)  # 10th percentile
        expected_case = np.mean(simulations)
        best_case = np.percentile(simulations, 90)  # 90th percentile
        
        # Max Drawdown on worst-case Monte Carlo scenario
        worst_path = sim_paths[np.argmin([p[-1] for p in sim_paths])]
        peak = np.maximum.accumulate(worst_path)
        drawdowns = (peak - worst_path) / peak
        max_drawdown = max(drawdowns) * 100

        # Dilution Risk (remaining dilution percentage)
        if fdv > 0:
            dilution_ratio = 100 - (market_cap / fdv) * 100
            if dilution_ratio < 20:
                dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
            elif dilution_ratio < 50:
                dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
            else:
                dilution_text = "⚠ High dilution risk: Significant token releases expected."
        else:
            dilution_ratio = 0
            dilution_text = "⚠ FDV not provided, cannot assess dilution risk."

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

        # Composite Risk Score
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

        composite_score = sum(scores.values()) / len(scores)
        if composite_score >= 70:
            bg_class = "risk-green"
            insight = (
                "This asset shows a low overall risk profile, making it a relatively safe investment option. "
                "The projected returns are strong compared to the risk-free rate, with a good balance of reward and risk (Sharpe and Sortino ratios). "
                "Dilution risk is minimal, meaning future token releases are unlikely to significantly impact the price. "
                "The market cap growth is plausible, and the CertiK score indicates solid security. "
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
                f"{', and a concerning CertiK score' if certik_adjusted < 40 else ''}. "
                "You might consider a smaller position in this asset while diversifying across other investments to mitigate these risks. "
                "Keep an eye on token unlock schedules and security updates to reassess your position."
            )
        else:
            bg_class = "risk-red"
            insight = (
                "This asset carries a high overall risk profile, indicating significant challenges for potential investors. "
                f"Key issues include {'extreme drawdown risk' if max_drawdown > 50 else 'high drawdown risk' if max_drawdown > 30 else ''}"
                f"{', high dilution risk from future token releases' if dilution_ratio > 50 else ''}"
                f"{', unrealistic market cap growth expectations' if mcap_vs_btc > 5 else ''}"
                f"{', poor risk-adjusted returns' if sharpe_ratio < 0 or sortino_ratio < 0 else ''}"
                f"{', and a low CertiK score indicating security concerns' if certik_adjusted < 40 else ''}. "
                "Proceed with caution—consider waiting for better entry points, improved security scores, or more favorable market conditions. "
                "Alternatively, explore safer assets with stronger fundamentals to protect your capital."
            )

        # Composite Risk Score
        st.subheader("Composite Risk Assessment")
        st.markdown(f"""
            <div class="risk-assessment {bg_class}">
                <div style="font-size: 20px; font-weight: bold; color: white;">Composite Risk Score: <span style="color: #333;">{composite_score:.1f}</span></div>
                <div style="font-size: 14px; margin-top: 5px; color: white;">{insight}</div>
            </div>
        """, unsafe_allow_html=True)

        # Key Metrics (3x2 grid)
        st.subheader("Key Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">💰 Investment Value (1 Year)</div>
                    <div class="metric-value">${asset_values[-1]:,.2f}</div>
                    <div class="metric-desc">This is how much your ${initial_investment:,.2f} investment could be worth in 12 months, based on the expected growth rate you provided. It shows the potential reward if the asset grows as expected.</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Max Drawdown</div>
                    <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                    <div class="metric-desc">This shows the biggest potential loss you might face in a worst-case scenario over 12 months. A higher percentage means more risk of losing value during a market dip.</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📊 Sharpe Ratio</div>
                    <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                    <div class="metric-desc">This measures how much extra return you get for the risk you're taking. Above 1 is good—it means you're getting a nice reward for the risk. Below 0 means the risk might not be worth it.</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">⚖️ Dilution Risk</div>
                    <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                    <div class="metric-desc">This shows how much the token's value might drop if more tokens are released. A higher percentage means more new tokens could flood the market, lowering the price.</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📈 MCap Growth Plausibility</div>
                    <div class="metric-value {'red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                    <div class="metric-desc">This checks if the asset's projected growth is realistic compared to Bitcoin's market size. A high percentage means the asset would need a huge market share, which might be hard to achieve.</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Sortino Ratio</div>
                    <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                    <div class="metric-desc">This focuses on the risk of losing money (downside risk). Above 1 means you're getting good returns compared to the chance of losses. Below 0 suggests the risk of losing money might outweigh the gains.</div>
                </div>
            """, unsafe_allow_html=True)

        # Price Projections
        st.subheader("Projected Investment Value Over Time")
        st.markdown("**Note**: The projected value reflects the growth of your initial investment, adjusted for expected price changes.")
        
        # Table for months 0, 3, 6, 12 with styled gradient
        proj_data = {
            "Time Period (Months)": [0, 3, 6, 12],
            "Projected Value ($)": [asset_values[i] for i in [0, 3, 6, 12]],
            "ROI (%)": [((asset_values[i] / initial_investment) - 1) * 100 for i in [0, 3, 6, 12]]
        }
        proj_df = pd.DataFrame(proj_data)
        styled_proj_df = proj_df.style.set_table_attributes('class="proj-table"').format({
            "Projected Value ($)": "${:,.2f}",
            "ROI (%)": "{:.2f}%"
        })
        st.table(styled_proj_df)

        # Line Plot
        df_proj = pd.DataFrame({
            'Month': range(months + 1),
            'Asset Value': asset_values,
            'Bitcoin Value': btc_values,
            'Stablecoin Value': rf_projections
        })
        
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        sns.lineplot(data=df_proj, x='Month', y='Asset Value', label='Asset', color='teal', linewidth=2.5, marker='o')
        sns.lineplot(data=df_proj, x='Month', y='Bitcoin Value', label='Bitcoin', color='gold', linewidth=2.5, marker='o')
        sns.lineplot(data=df_proj, x='Month', y='Stablecoin Value', label='Stablecoin', color='gray', linewidth=2.5, marker='o')
        plt.axhline(y=initial_investment, color='red', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
        plt.fill_between(df_proj['Month'], initial_investment, df_proj['Asset Value'], where=(df_proj['Asset Value'] < initial_investment), color='red', alpha=0.1, label='Loss Zone')
        plt.title('Projected Investment Value Over 12 Months')
        plt.xlabel('Months')
        plt.ylabel('Value ($)')
        plt.legend()
        st.pyplot(plt)
        plt.clf()

        # Monte Carlo Results
        st.subheader("Monte Carlo Scenarios - 12 Month Investment Value")
        st.markdown("""
        - **Expected Case**: The result using your inputs (growth rate), with randomization.  
        - **Best Case**: The 90th percentile (20th highest of 200 runs)—a strong outcome, not the absolute best.  
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
        plt.figure(figsize=(10, 6))
        sns.histplot(simulations, bins=50, color='gray')
        plt.axvline(worst_case, color='red', label='Worst Case', linewidth=2)
        plt.axvline(expected_case, color='yellow', label='Expected Case', linewidth=2)
        plt.axvline(best_case, color='green', label='Best Case', linewidth=2)
        plt.axvline(initial_investment, color='black', linestyle='--', label=f'Initial Investment (${initial_investment:,.2f})')
        plt.title("Monte Carlo Scenarios - 12 Month Investment Value")
        plt.xlabel("Value ($)")
        plt.ylabel("Frequency")
        plt.legend()
        st.pyplot(plt)
        plt.clf()
