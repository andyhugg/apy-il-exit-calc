# ... (Previous imports, CSS, sidebar, and calculations remain unchanged)

# Main content (only updating the "Key Metrics" section)
if calculate:
    # ... (Previous calculations and risk assessment remain unchanged)

    st.subheader("Key Metrics")
    roi = ((asset_values[-1] / initial_investment) - 1) * 100
    investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

    # JavaScript for toggling the description visibility
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

    # ... (Rest of the code—projections, Monte Carlo, portfolio—remains unchanged)
