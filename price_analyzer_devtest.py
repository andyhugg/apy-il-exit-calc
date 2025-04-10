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
        rf_monthly_rate = (1 + risk_free_rate/100) ** (1/12) - 1
        
        asset_projections = [asset_price * (1 + asset_monthly_rate) ** i for i in range(months + 1)]
        btc_values = [initial_investment * (1 + 0.25) ** (i / 12) for i in range(months + 1)]  # Hardcoded 25% CAGR
        rf_projections = [initial_investment * (1 + rf_monthly_rate) ** i for i in range(months + 1)]
        
        asset_values = [initial_investment * p / asset_price for p in asset_projections]
        
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
        btc_mcap = 21_000_000 * 100_000  # Approximate BTC price for MCap comparison (not used directly)
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

        # Define individual scores
        scores = {
            'Max Drawdown': 100 if max_drawdown < 20 else 50 if max_drawdown < 40 else 0,  # Adjusted thresholds
            'Dilution Risk': 100 if dilution_ratio < 20 else 50 if dilution_ratio < 50 else 0,
            'Supply Concentration': 0 if supply_ratio < 20 else 50 if supply_ratio < 50 else 100,
            'MCap Growth': 100 if mcap_vs_btc < 1 else 50 if mcap_vs_btc < 5 else 0,
            'Sharpe Ratio': 100 if sharpe_ratio > 1 else 50 if sharpe_ratio > 0 else 0,
            'Sortino Ratio': 100 if sortino_ratio > 1 else 50 if sortino_ratio > 0 else 0,
            'CertiK Score': 100 if (50 if certik_score == 0 else certik_score) >= 70 else 50 if (50 if certik_score == 0 else certik_score) >= 40 else 0,
            'Market Cap': 100 if market_cap >= 1_000_000_000 else 50 if market_cap >= 10_000_000 else 0,
            'Fear and Greed': 100 if fear_and_greed <= 24 else 75 if fear_and_greed <= 49 else 50 if fear_and_greed == 50 else 25 if fear_and_greed <= 74 else 0,
            'Liquidity': 0 if vol_mkt_cap < 1 else 50 if vol_mkt_cap <= 5 else 100,
            'Fear and Greed Penalty': 100 - abs(50 - fear_and_greed) * 2  # Added parabolic penalty
        }

        # Define weights based on investor profile
        weights = {
            "Conservative Investor": {
                "Max Drawdown": 2.0, "Dilution Risk": 1.5, "Supply Concentration": 1.2, "MCap Growth": 0.5,
                "Sharpe Ratio": 1.0, "Sortino Ratio": 1.0, "CertiK Score": 3.0, "Market Cap": 1.2,
                "Fear and Greed": 0.8, "Liquidity": 1.5, "Fear and Greed Penalty": 2.5
            },
            "Bitcoin Strategist": {
                "Max Drawdown": 1.0, "Dilution Risk": 1.0, "Supply Concentration": 1.0, "MCap Growth": 2.0,
                "Sharpe Ratio": 1.0, "Sortino Ratio": 1.0, "CertiK Score": 2.5, "Market Cap": 1.0,
                "Fear and Greed": 0.5, "Liquidity": 1.0, "Fear and Greed Penalty": 1.5
            },
            "Growth Crypto Investor": {
                "Max Drawdown": 1.0, "Dilution Risk": 1.0, "Supply Concentration": 1.0, "MCap Growth": 1.2,
                "Sharpe Ratio": 1.5, "Sortino Ratio": 1.5, "CertiK Score": 2.5, "Market Cap": 1.0,
                "Fear and Greed": 1.0, "Liquidity": 1.0, "Fear and Greed Penalty": 2.0
            },
            "Aggressive Crypto Investor": {
                "Max Drawdown": 0.3, "Dilution Risk": 0.8, "Supply Concentration": 0.8, "MCap Growth": 2.0,
                "Sharpe Ratio": 1.2, "Sortino Ratio": 1.2, "CertiK Score": 2.5, "Market Cap": 1.0,
                "Fear and Greed": 1.0, "Liquidity": 0.8, "Fear and Greed Penalty": 1.5
            }
        }

        # Calculate weighted composite score
        weighted_sum = sum(scores[metric] * weights[investor_profile][metric] for metric in scores)
        total_weight = sum(weights[investor_profile].values())
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Calculate Baseline Score (Using Growth Investor Weights for Comparison)
        baseline_weighted_sum = sum(scores[metric] * weights["Growth Crypto Investor"][metric] for metric in scores)
        baseline_total_weight = sum(weights["Growth Crypto Investor"].values())
        baseline_score = baseline_weighted_sum / baseline_total_weight if baseline_total_weight > 0 else 0
        profile_adjustment = composite_score - baseline_score
        profile_adjustment_text = f"Profile Adjustment: {'+' if profile_adjustment >= 0 else ''}{profile_adjustment:.1f} points"

        return_to_hurdle_ratio = min((growth_rate / hurdle_rate) if hurdle_rate > 0 else 1, 3)
        risk_adjusted_score = min(composite_score * return_to_hurdle_ratio, 100)

        fear_greed_classification = "Extreme Fear" if fear_and_greed <= 24 else "Fear" if fear_and_greed <= 49 else "Neutral" if fear_and_greed == 50 else "Greed" if fear_and_greed <= 74 else "Extreme Greed"
        bg_class = "risk-green" if composite_score >= 70 else "risk-yellow" if composite_score >= 40 else "risk-red"
        
        # Actionable Insights for Composite Score
        certik_low = (50 if certik_score == 0 else certik_score) < 40
        if composite_score >= 70:
            insight = "✅ Low risk—good to invest. Add this asset to your portfolio."
            if investor_profile == "Conservative Investor":
                insight += " As a Conservative Investor, mix with stablecoins for extra safety."
            if composite_score > 80 and investor_profile == "Aggressive Crypto Investor":
                insight += " Note: This asset’s low risk may not match your Aggressive Investor profile’s growth goals."
        elif composite_score >= 40:
            insight = "⚠️ Moderate risk—invest a small amount. Watch for high drawdown or dilution."
            if certik_low:
                insight += " Low CertiK score adds security concerns—consider BTC instead."
            if investor_profile in ["Conservative Investor", "Bitcoin Strategist"]:
                insight += f" As a {investor_profile}, lean toward BTC or stablecoins."
            if investor_profile == "Conservative Investor" and composite_score < 50:
                insight += " Warning: This asset’s risk level may not suit your Conservative Investor profile."
        else:
            insight = "🚨 High risk—avoid or invest very little. High drawdown or dilution makes this risky."
            if certik_low:
                insight += " Low CertiK score adds security concerns."
            insight += " Switch to BTC or stablecoins for safety."
            if investor_profile == "Conservative Investor":
                insight += " Warning: This asset’s risk level may not suit your Conservative Investor profile."

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
                    <div style="font-size: 14px; margin-top: 5px; color: #A9A9A9; font-style: italic;">{profile_adjustment_text}</div>
                    <div style="font-size: 14px; margin-top: 5px; color: #A9A9A9; font-style: italic;">Fear and Greed: {fear_and_greed} ({fear_greed_classification})</div>
                </div>
            """, unsafe_allow_html=True)

        # Key Metrics with Updated Tooltips
        with st.expander("Key Metrics", expanded=False):
            roi = ((asset_values[-1] / initial_investment) - 1) * 100
            investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

            st.markdown("### Investment Returns and Risk-Adjusted Metrics")
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">💰 Value (1 Yr)<span class="tooltip" title="Your money’s expected value in a year. What to do: Above 1.5x, take profits. At 1-1.5x, keep watching. Below 1x, rethink this asset.">?</span></div>
                    <div class="metric-value">${asset_values[-1]:,.2f}<br>({investment_multiple:.2f}x)</div>
                    <div class="metric-desc">From ${initial_investment:,.2f} investment.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Sortino<span class="tooltip" title="Earnings compared to bad losses. What to do: Above 1, stay in. At 0-1, add stable assets. Below 0, switch to stable assets.">?</span></div>
                    <div class="metric-value {'red-text' if sortino_ratio < 0 else 'green-text' if sortino_ratio > 1 else 'yellow-text'}">{sortino_ratio:.2f}</div>
                    <div class="metric-desc">Downside risk-adjusted return.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📊 Sharpe<span class="tooltip" title="Earnings compared to all risks. What to do: Above 1, stay in. At 0-1, look at safer assets. Below 0, switch to stablecoins.">?</span></div>
                    <div class="metric-value {'red-text' if sharpe_ratio < 0 else 'green-text' if sharpe_ratio > 1 else 'yellow-text'}">{sharpe_ratio:.2f}</div>
                    <div class="metric-desc">Total risk-adjusted return.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### Risk Metrics")
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Max DD<span class="tooltip" title="Biggest possible loss after 12 months in a worst case. What to do: Below 20%, stay in. Above 20%, set a stop-loss—or hold if you trust the asset’s future value.">?</span></div>
                    <div class="metric-value {'yellow-text' if max_drawdown > 20 else 'green-text'}">{max_drawdown:.2f}%</div>
                    <div class="metric-desc">Worst-case loss scenario.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">⚖️ Dilution<span class="tooltip" title="Risk from unreleased tokens. What to do: Below 20%, stay in. 20-50%, check token release dates. Above 50%, lower your investment.">?</span></div>
                    <div class="metric-value {'red-text' if dilution_ratio > 50 else 'yellow-text' if dilution_ratio > 20 else 'green-text'}">{dilution_ratio:.2f}%</div>
                    <div class="metric-desc">Uncirculated token risk.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">🛡️ Supply<span class="tooltip" title="How many tokens are in use. What to do: Below 20%, watch for big sellers. 20-50%, be careful. Above 50%, stay in.">?</span></div>
                    <div class="metric-value {'red-text' if supply_ratio < 20 else 'yellow-text' if supply_ratio < 50 else 'green-text'}">{supply_ratio:.2f}%</div>
                    <div class="metric-desc">Circulating supply ratio.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### Market Metrics")
            mcap_max_note = f"Using Total Supply ({max_supply_display}), projected market cap would be {mcap_vs_btc_max:.2f}% of BTC’s." if total_supply > 0 else "Total Supply not provided."
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📈 MCap<span class="tooltip" title="How big the asset might grow compared to BTC. What to do: Below 1%, stay in. 1-5%, lower your growth guess. Above 5%, set a realistic goal.">?</span></div>
                    <div class="metric-value {'red-text' if mcap_vs_btc > 5 else 'yellow-text' if mcap_vs_btc > 1 else 'green-text'}">{mcap_vs_btc:.2f}%</div>
                    <div class="metric-desc">Projected vs. BTC MCap.</div>
                </div>
            """, unsafe_allow_html=True)

            supply_volatility_note = f"Total Supply: {max_supply_display}." if total_supply > 0 else "Total Supply not provided."
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">💧 Liquidity<span class="tooltip" title="How easy it is to trade. What to do: Below 1%, trade small amounts carefully. 1-5%, trade small amounts. Above 5%, trade freely.">?</span></div>
                    <div class="metric-value {'red-text' if vol_mkt_cap < 1 else 'yellow-text' if vol_mkt_cap <= 5 else 'green-text'}">{vol_mkt_cap:.2f}%</div>
                    <div class="metric-desc">{supply_volatility_note}</div>
                </div>
            """, unsafe_allow_html=True)

        # How Does This Compare? Section
        st.markdown("### How Does This Compare?")
        asset_return = asset_values[-1] / initial_investment if initial_investment > 0 else 0
        btc_return = 1.25  # 25% CAGR
        stablecoin_return = 1 + (risk_free_rate / 100)

        asset_vs_hurdle = growth_rate >= hurdle_rate
        asset_vs_btc = asset_return >= btc_return
        asset_vs_stablecoin = asset_return >= stablecoin_return

        # Dynamically construct the tooltip message
        if asset_vs_btc and asset_vs_stablecoin:
            tooltip_text = (
                f"Your asset’s growth ({asset_return:.2f}x) is better than BTC ({btc_return:.2f}x) and stablecoins ({stablecoin_return:.2f}x). "
                f"It also {'beats' if asset_vs_hurdle else 'does not beat'} the safe target. Stay in. If risks are high, add stablecoins or switch to BTC."
            )
        elif asset_vs_btc:
            tooltip_text = (
                f"Your asset’s growth ({asset_return:.2f}x) is better than BTC ({btc_return:.2f}x) but not stablecoins ({stablecoin_return:.2f}x). "
                f"It also {'beats' if asset_vs_hurdle else 'does not beat'} the safe target. Stay in. If risks are high, add stablecoins or switch to BTC."
            )
        elif asset_vs_stablecoin:
            tooltip_text = (
                f"Your asset’s growth ({asset_return:.2f}x) is better than stablecoins ({stablecoin_return:.2f}x) but not BTC ({btc_return:.2f}x). "
                f"It also {'beats' if asset_vs_hurdle else 'does not beat'} the safe target. Stay in. If risks are high, add stablecoins or switch to BTC."
            )
        else:
            tooltip_text = (
                f"Your asset’s growth ({asset_return:.2f}x) is not better than BTC ({btc_return:.2f}x) or stablecoins ({stablecoin_return:.2f}x). "
                f"It also {'beats' if asset_vs_hurdle else 'does not beat'} the safe target. If risks are high, add stablecoins or switch to BTC."
            )

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Asset vs Safe Target<span class="tooltip" title="{tooltip_text}">?</span></div>
                <div class="metric-value">{growth_rate:.1f}% vs {hurdle_rate:.1f}% <span class="{'arrow-up' if asset_vs_hurdle else 'arrow-down'}">{'▲' if asset_vs_hurdle else '▼'}</span></div>
                <div class="metric-desc">Growth compared to safe target (risk-free rate + 12%).</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Asset vs BTC<span class="tooltip" title="{tooltip_text}">?</span></div>
                <div class="metric-value">{asset_return:.2f}x vs {btc_return:.2f}x <span class="{'arrow-up' if asset_vs_btc else 'arrow-down'}">{'▲' if asset_vs_btc else '▼'}</span></div>
                <div class="metric-desc">12-month growth compared to BTC (25% CAGR).</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">📈 Asset vs Stablecoin<span class="tooltip" title="{tooltip_text}">?</span></div>
                <div class="metric-value">{asset_return:.2f}x vs {stablecoin_return:.2f}x <span class="{'arrow-up' if asset_vs_stablecoin else 'arrow-down'}">{'▲' if asset_vs_stablecoin else '▼'}</span></div>
                <div class="metric-desc">12-month growth compared to stablecoin ({risk_free_rate:.1f}%).</div>
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
            st.markdown("Tests 200 possible outcomes over 12 months based on market mood.")
            st.markdown("- **Expected**: Average | **Best**: One of the highest outcomes | **Worst**: One of the lowest outcomes")
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
