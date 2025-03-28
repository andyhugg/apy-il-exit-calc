def run_crypto_valuations():
    # Ensure introduction and disclaimer are present
    st.markdown(
        f'<div><img src="https://raw.githubusercontent.com/andyhugg/apy-il-exit-calc/main/Arta.png" class="arta-large-logo" width="600"></div>',
        unsafe_allow_html=True
    )
    st.write("Arta Crypto Valuations - Know the Price. Master the Risk.")
    st.markdown("""
    Whether you're trading, investing, or strategizing, Arta gives you fast, accurate insights into token prices, profit margins, and portfolio risk. Run scenarios, test your assumptions, and sharpen your edge — all in real time. **Arta: Know the Price. Master the Risk.**
    """)
    st.markdown("""
    <div class="arta-disclaimer">
    ⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
    </div>
    """, unsafe_allow_html=True)

    if 'arta_calculate' in st.session_state and st.session_state.arta_calculate:
        # Parse inputs
        market_cap = parse_market_value(market_cap_input)
        fdv = parse_market_value(fdv_input)
        circulating_supply = parse_market_value(circulating_supply_input)
        max_supply = 0  # Removed Max Supply input, set to 0 to derive from FDV
        volatility = 0  # Removed Volatility input, set to 0 to use Fear and Greed Index defaults

        # Validation checks
        if asset_price == 0 or initial_investment == 0:
            st.error("Please enter valid values for Asset Price and Initial Investment (greater than 0).")
            return
        elif market_cap == 0 and (circulating_supply == 0 or asset_price == 0):
            st.error("Please provide either Market Cap or both Circulating Supply and Asset Price to calculate Market Cap.")
            return

        # Validate Circulating Supply vs. Total Supply (derived from FDV if Max Supply not provided)
        if max_supply > 0 and circulating_supply > 0:
            supply_ratio_check = circulating_supply / max_supply
            if supply_ratio_check < 0.01:
                st.warning("The Circulating Supply appears to be much smaller than the Max Supply (less than 1%). Did you mean to enter the Circulating Supply in millions (e.g., '555.54m' for 555.54 million)? Please double-check your inputs.")
        elif fdv > 0 and asset_price > 0 and circulating_supply > 0:
            total_supply = fdv / asset_price
            supply_ratio_check = circulating_supply / total_supply
            if supply_ratio_check < 0.01:
                st.warning("The Circulating Supply appears to be much smaller than the Total Supply derived from FDV (less than 1%). Did you mean to enter the Circulating Supply in millions (e.g., '555.54m' for 555.54 million)? Please double-check your inputs.")

        # Calculate Market Cap if not provided
        if market_cap == 0 and circulating_supply > 0 and asset_price > 0:
            market_cap = circulating_supply * asset_price

        # Calculate Total Supply (Max Supply) if not provided
        if max_supply == 0 and fdv > 0 and asset_price > 0:
            total_supply = fdv / asset_price
        else:
            total_supply = max_supply

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

        # Monte Carlo Simulation
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

        # Dilution Risk
        if total_supply > 0 and circulating_supply > 0:
            dilution_ratio = 100 * (1 - (circulating_supply / total_supply))
            if dilution_ratio < 20:
                dilution_text = "✓ Low dilution risk: Only a small portion of tokens remain to be released."
            elif dilution_ratio < 50:
                dilution_text = "⚠ Moderate dilution risk: A notable portion of tokens may be released."
            else:
                dilution_text = "⚠ High dilution risk: Significant token releases expected."
        else:
            dilution_ratio = 0
            dilution_text = "⚠ Circulating Supply or FDV not provided, cannot assess dilution risk."

        # Format supply values for display
        def format_supply(value):
            if value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"{value / 1_000_000:.2f}M"
            elif value >= 1_000:
                return f"{value / 1_000:.2f}K"
            else:
                return f"{value:,.0f}"

        circulating_supply_display = format_supply(circulating_supply) if circulating_supply > 0 else "N/A"
        max_supply_display = format_supply(total_supply) if total_supply > 0 else "N/A"

        # Supply Concentration Risk
        if total_supply > 0 and circulating_supply > 0:
            supply_ratio = (circulating_supply / total_supply) * 100
            if supply_ratio < 20:
                supply_concentration_text = "⚠ High risk: Very low circulating supply relative to total supply increases the risk of price manipulation by large holders."
            elif supply_ratio < 50:
                supply_concentration_text = "⚠ Moderate risk: A significant portion of tokens is not yet circulating, which may allow large holders to influence price."
            else:
                supply_concentration_text = "✓ Low risk: A large portion of tokens is circulating, reducing the risk of price manipulation by large holders."
        else:
            supply_ratio = 0
            supply_concentration_text = "⚠ Circulating Supply or FDV not provided, cannot assess supply concentration risk."

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

        # Calculate projected market cap using Total Supply (derived from FDV)
        if total_supply > 0:
            projected_mcap_max = projected_price * total_supply
            mcap_vs_btc_max = (projected_mcap_max / btc_mcap) * 100 if btc_mcap > 0 else 0
        else:
            projected_mcap_max = 0
            mcap_vs_btc_max = 0

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
        asset_vs_hurdle = growth_rate - hurdle_rate

        # Determine label and color for Hurdle Rate vs. Bitcoin
        if asset_vs_hurdle >= 20:
            hurdle_label = "Strong Outperformance"
            hurdle_color = "arta-green-text"
        elif asset_vs_hurdle >= 0:
            hurdle_label = "Moderate Outperformance"
            hurdle_color = "arta-yellow-text"
        else:
            hurdle_label = "Below Hurdle"
            hurdle_color = "arta-red-text"

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

        # Supply Concentration
        if supply_ratio < 20:
            scores['Supply Concentration'] = 0
        elif supply_ratio < 50:
            scores['Supply Concentration'] = 50
        else:
            scores['Supply Concentration'] = 100

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
            scores['Fear and Greed'] = 100
        elif fear_and_greed <= 49:
            scores['Fear and Greed'] = 75
        elif fear_and_greed == 50:
            scores['Fear and Greed'] = 50
        elif fear_and_greed <= 74:
            scores['Fear and Greed'] = 25
        else:
            scores['Fear and Greed'] = 0

        # Liquidity (based on Vol/Mkt Cap 24h)
        if vol_mkt_cap < 1:
            scores['Liquidity'] = 0
        elif vol_mkt_cap <= 5:
            scores['Liquidity'] = 50
        else:
            scores['Liquidity'] = 100

        composite_score = sum(scores.values()) / len(scores)

        # Risk-Adjusted Return Score
        return_to_hurdle_ratio = (growth_rate / hurdle_rate) if hurdle_rate > 0 else 1
        return_to_hurdle_ratio = min(return_to_hurdle_ratio, 3)
        risk_adjusted_score = composite_score * return_to_hurdle_ratio
        risk_adjusted_score = min(risk_adjusted_score, 100)

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
            bg_class = "arta-risk-green"
            insight = (
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction'}."
            )
        elif composite_score >= 40:
            bg_class = "arta-risk-yellow"
            insight = (
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction'}."
            )
        else:
            bg_class = "arta-risk-red"
            insight = (
                f"The Fear and Greed Index is currently at {fear_and_greed} ({fear_greed_classification}), "
                f"which {'suggests a potential buying opportunity despite the high risk due to market overselling' if fear_and_greed <= 49 else 'indicates a neutral market sentiment' if fear_and_greed == 50 else 'warns of a potentially overheated market due for a correction, adding to the risk'}."
            )

        # Composite Risk Score
        st.subheader("Composite Risk Assessment")
        st.markdown(f"""
            <div class="arta-risk-assessment {bg_class}">
                <div style="font-size: 20px; font-weight: bold; color: #333;">Composite Risk Score: <span style="color: #333;">{composite_score:.1f}</span></div>
                <div style="font-size: 14px; margin-top: 5px; color: #333;">{insight}</div>
            </div>
        """, unsafe_allow_html=True)

        # Key Metrics
        st.subheader("Key Metrics")

        # Calculate ROI for Investment Value
        roi = ((asset_values[-1] / initial_investment) - 1) * 100

        # Card 1: Investment Value
        insight_investment = (
            "Lock in profits by setting a sell target if the price reaches this level." if roi > 50
            else "Hold your position but monitor market trends for any changes." if roi >= 0
            else "Reassess this investment—it may not meet your growth expectations."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">💰 Investment Value (1 Year)</div>
                <div class="arta-metric-value">${asset_values[-1]:,.2f}</div>
                <div class="arta-metric-desc">This shows your ${initial_investment:,.2f} investment’s potential value in 12 months based on the expected growth rate. It reflects the reward if the asset grows as projected.<br>
                <b>Actionable Insight:</b> {insight_investment}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 2: Max Drawdown
        insight_drawdown = (
            "Minimal action needed—drawdown risk is low." if max_drawdown < 30
            else f"Set a stop-loss at {max_drawdown:.2f}% below your entry to limit losses." if max_drawdown <= 50
            else "Reduce exposure or set a tight stop-loss to protect against significant losses."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">📉 Max Drawdown</div>
                <div class="arta-metric-value {'arta-red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
                <div class="arta-metric-desc">From the Monte Carlo Analysis, this is the largest potential loss in a worst-case scenario over 12 months. A higher percentage means greater risk of a price drop.<br>
                <b>Actionable Insight:</b> {insight_drawdown}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 3: Sharpe Ratio
        insight_sharpe = (
            "Proceed with confidence—risk-reward balance is strong." if sharpe_ratio > 1
            else "Be cautious and consider safer assets like Bitcoin to improve your risk-reward." if sharpe_ratio >= 0
            else "Shift to safer assets like stablecoins to reduce overall risk exposure."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">📊 Sharpe Ratio</div>
                <div class="arta-metric-value {'arta-red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
                <div class="arta-metric-desc">This measures your return per unit of risk taken. Below 0 means the risk may outweigh the reward.<br>
                <b>Actionable Insight:</b> {insight_sharpe}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 4: Dilution Risk
        insight_dilution = (
            "Minimal action needed—dilution risk is low." if dilution_ratio < 20
            else "Research the token’s unlock schedule to anticipate price impacts." if dilution_ratio <= 50
            else "Reduce your position due to high dilution risk from future token releases."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">⚖️ Dilution Risk</div>
                <div class="arta-metric-value {'arta-red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
                <div class="arta-metric-desc">This shows the percentage of tokens yet to be released, which could lower the price (Circulating: {circulating_supply_display}, Total: {max_supply_display}). A higher percentage means greater risk of dilution.<br>
                <b>Actionable Insight:</b> {insight_dilution}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 5: MCap Growth Plausibility
        insight_mcap = (
            "Proceed with confidence—growth is realistic." if mcap_vs_btc < 1
            else "Adjust your growth rate assumption to make it more achievable." if mcap_vs_btc <= 5
            else "Focus on assets with more realistic growth targets to reduce risk."
        )
        mcap_max_note = f"Using Total Supply ({max_supply_display}), the projected market cap would be {mcap_vs_btc_max:.2f}% of BTC’s, making growth {'less plausible' if mcap_vs_btc_max > mcap_vs_btc else 'more plausible'}." if total_supply > 0 else "Total Supply not provided, cannot assess impact on growth plausibility."
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">📈 MCap Growth Plausibility</div>
                <div class="arta-metric-value {'arta-red-text' if mcap_vs_btc > 5 else ''}">{mcap_vs_btc:.2f}% of BTC MCap</div>
                <div class="arta-metric-desc">This compares the asset’s projected market cap to Bitcoin’s to assess growth realism. {mcap_max_note}<br>
                <b>Actionable Insight:</b> {insight_mcap}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 6: Sortino Ratio
        insight_sortino = (
            "Proceed with confidence—downside risk is well-managed." if sortino_ratio > 1
            else "Allocate more to stable assets to reduce downside risk." if sortino_ratio >= 0
            else "Shift to stable assets to minimize the risk of significant losses."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">📉 Sortino Ratio</div>
                <div class="arta-metric-value {'arta-red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
                <div class="arta-metric-desc">This measures return per unit of downside risk. Below 0 suggests losses may outweigh gains.<br>
                <b>Actionable Insight:</b> {insight_sortino}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 7: Hurdle Rate vs. Bitcoin
        insight_hurdle = (
            "Favor this asset over Bitcoin for potentially higher returns." if asset_vs_hurdle >= 20
            else "Consider a balanced allocation between this asset and Bitcoin." if asset_vs_hurdle >= 0
            else "Increase your Bitcoin allocation for better risk-adjusted returns."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">📈 Hurdle Rate vs. Bitcoin</div>
                <div class="arta-metric-value {hurdle_color}">{asset_vs_hurdle:.2f}%<br>({hurdle_label})</div>
                <div class="arta-metric-desc">This shows how the asset’s growth compares to the minimum return needed to beat Bitcoin. A negative value means Bitcoin may be a better choice.<br>
                <b>Actionable Insight:</b> {insight_hurdle}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 8: Risk-Adjusted Return Score
        insight_risk_adj = (
            "Proceed with confidence but diversify to manage risks." if risk_adjusted_score >= 70
            else "Take a small position and diversify to balance risk and reward." if risk_adjusted_score >= 40
            else "Explore safer assets with better risk-adjusted returns."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">🎯 Risk-Adjusted Return Score</div>
                <div class="arta-metric-value {'arta-green-text' if risk_adjusted_score >= 70 else 'arta-yellow-text' if risk_adjusted_score >= 40 else 'arta-red-text'}">{risk_adjusted_score:.1f}</div>
                <div class="arta-metric-desc">This score combines the Composite Risk Score with the asset’s expected return relative to the hurdle rate (stablecoin pool risk-free rate plus 6% inflation, doubled). A score below 40 indicates high risk with insufficient returns to justify it.<br>
                <b>Actionable Insight:</b> {insight_risk_adj}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 9: Liquidity
        insight_liquidity = (
            "Use limit orders and monitor volume trends for better entry/exit points." if vol_mkt_cap < 1
            else "Use limit orders for smaller trades to minimize slippage risks." if vol_mkt_cap <= 5
            else "Trade with confidence but use stop-loss orders to manage volatility."
        )
        supply_volatility_note = f"Low Circulating Supply ({circulating_supply_display}) relative to Total Supply ({max_supply_display}) may increase price volatility." if total_supply > 0 and circulating_supply > 0 else "Circulating Supply or Total Supply not provided, cannot assess impact on volatility."
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">💧 Liquidity (Vol/Mkt Cap 24h)</div>
                <div class="arta-metric-value {'arta-red-text' if vol_mkt_cap < 1 else 'arta-green-text' if vol_mkt_cap > 5 else 'arta-yellow-text'}">{vol_mkt_cap:.2f}%</div>
                <div class="arta-metric-desc">This measures the 24-hour trading volume as a percentage of the asset’s market cap, indicating how easily you can buy or sell. {supply_volatility_note}<br>
                <b>Actionable Insight:</b> {insight_liquidity}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Card 10: Supply Concentration Risk
        insight_supply_concentration = (
            "Monitor for whale activity—large holders may influence price." if supply_ratio < 20
            else "Be cautious of potential price influence by large holders." if supply_ratio < 50
            else "Proceed with confidence—supply distribution reduces manipulation risk."
        )
        st.markdown(f"""
            <div class="arta-metric-tile">
                <div class="arta-metric-title">🛡️ Supply Concentration Risk</div>
                <div class="arta-metric-value {'arta-red-text' if supply_ratio < 20 else 'arta-yellow-text' if supply_ratio < 50 else 'arta-green-text'}">{supply_ratio:.2f}%</div>
                <div class="arta-metric-desc">This shows the percentage of circulating supply relative to total supply (Circulating: {circulating_supply_display}, Total: {max_supply_display}). A lower percentage increases the risk of price manipulation by large holders.<br>
                <b>Actionable Insight:</b> {insight_supply_concentration}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Price Projections
        st.subheader("Projected Investment Value Over Time")
        st.markdown("**Note**: The projected values reflect the growth of your initial investment in the asset, Bitcoin, and a stablecoin pool, adjusted for their respective expected growth rates.")
        
        # Transposed table: Metrics as rows, Time Periods as columns
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

        # Apply conditional formatting to ROI rows
        def color_roi(val, row_idx):
            if "ROI" in proj_df.iloc[row_idx]["Metric"]:
                if val > 0:
                    return 'color: #32CD32'
                elif val < 0:
                    return 'color: #FF4D4D'
                else:
                    return 'color: #A9A9A9'
            return ''

        # Apply formatting and styling
        styled_proj_df = proj_df.style.set_table_attributes('class="arta-proj-table"').format({
            "Month 0": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 0'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
            "Month 3": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 3'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
            "Month 6": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 6'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x),
            "Month 12": lambda x: "${:,.2f}".format(x) if "Value" in proj_df.iloc[proj_df.index[proj_df['Month 12'] == x].tolist()[0]]["Metric"] else "{:.2f}%".format(x)
        }).apply(lambda row: [color_roi(row["Month 0"], row.name), color_roi(row["Month 3"], row.name), color_roi(row["Month 6"], row.name), color_roi(row["Month 12"], row.name), ''], axis=1)
        
        # Wrap the table in a container with horizontal scrolling
        st.markdown('<div class="arta-proj-table-container">', unsafe_allow_html=True)
        st.table(styled_proj_df)
        st.markdown('</div>', unsafe_allow_html=True)

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
        The **Simplified Monte Carlo Analysis** helps you understand the range of potential outcomes for your investment over the next 12 months by simulating 200 different scenarios. We generate random price paths based on volatility derived from the Fear and Greed Index and your expected growth rate, with monthly variations to reflect market uncertainty. The Fear and Greed Index adjusts the distribution of returns: a fearful market (≤ 49) skews returns towards the lower end (reflecting higher downside risk but potential for recovery), while a greedy market (> 50) skews returns higher (reflecting speculative growth but risk of corrections). To keep results realistic, we cap the maximum return at your inputted price projection plus volatility. This analysis is crucial in crypto investing as it highlights the best-case, expected-case, and worst-case scenarios, helping you assess risk and make informed decisions in a highly volatile market.
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
