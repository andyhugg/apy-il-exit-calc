import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import csv

# [Previous functions remain unchanged: calculate_il, calculate_pool_value, calculate_future_value, etc.]

def check_exit_conditions(initial_investment: float, apy: float, il: float, tvl_decline: float,
                         initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
                         current_tvl: float, risk_free_rate: float, trust_score: int, months: int = 12, 
                         expected_price_change_asset1: float = 0.0, expected_price_change_asset2: float = 0.0, 
                         is_new_pool: bool = False, btc_growth_rate: float = 0.0):
    pool_value, il_impact = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                       current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    value_if_held = (initial_investment / 2 / initial_price_asset1 * current_price_asset1) + (initial_investment / 2 / initial_price_asset2 * current_price_asset2)
    
    future_value, future_il = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
                                                    current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                    expected_price_change_asset2, is_new_pool)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    
    # Simplified Hurdle Rate: Risk-Free Rate + 6% global inflation
    hurdle_rate = risk_free_rate + 6.0
    
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
    volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)
    protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    # Core Metrics Section with Evenly Sized Blocks
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>Core Metrics</h1>", unsafe_allow_html=True)

    # Custom CSS for metric cards with fixed height
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1f2a44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
        min-height: 120px; /* Fixed height to ensure uniformity */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Distribute content evenly within the card */
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-title {
        font-weight: bold;
        font-size: 16px;
        color: #ffffff;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 20px;
        font-weight: 500;
    }
    .metric-value.green {
        color: #00cc00;
    }
    .metric-value.red {
        color: #ff3333;
    }
    .metric-value.neutral {
        color: #ffffff;
    }
    .metric-note {
        font-size: 12px;
        color: #b0b0b0;
        margin-top: 5px;
        line-height: 1.2; /* Ensure notes wrap cleanly */
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2; /* Limit notes to 2 lines */
        -webkit-box-orient: vertical;
    }
    </style>
    """, unsafe_allow_html=True)

    # Split into two columns
    col1, col2 = st.columns(2)

    # Helper function to determine value color
    def get_value_color(metric_name, value):
        if metric_name in ["Impermanent Loss", "TVL Decline", "Projected Impermanent Loss"]:
            return "red" if value > 0 else "green"
        elif metric_name == "Net Return":
            return "green" if value > 1 else "red"
        elif metric_name in ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"]:
            return "green" if value <= 12 else "red"
        elif metric_name == "Pool Share":
            return "green" if value < 5 else "red"
        return "neutral"

    # Metrics for Column 1
    with col1:
        if initial_tvl <= 0:
            if is_new_pool:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">(new pool, IL starts at 0)</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                    <div class="metric-note">(based on expected price changes)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if is_new_pool:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">(new pool, IL starts at 0)</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il)}">{future_il:.2f}%</div>
                    <div class="metric-note">(based on expected price changes)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Against IL</div>
            <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months)}">{break_even_months} months</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Including Expected Price Changes</div>
            <div class="metric-value {get_value_color('Months to Breakeven Including Expected Price Changes', break_even_months_with_price)}">{break_even_months_with_price} months</div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics for Column 2
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Net Return</div>
            <div class="metric-value {get_value_color('Net Return', net_return)}">{net_return:.2f}x</div>
            <div class="metric-note">(includes expected price changes for Asset 1 and Asset 2)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Hurdle Rate</div>
            <div class="metric-value {get_value_color('Hurdle Rate', hurdle_rate)}">{hurdle_rate:.2f}%</div>
            <div class="metric-note">(Your {risk_free_rate}% risk-free rate + 6% avg global inflation, 2025 est.)</div>
        </div>
        """, unsafe_allow_html=True)

        if initial_tvl <= 0:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 TVL Decline</div>
                <div class="metric-value">Cannot calculate</div>
                <div class="metric-note">Set Initial TVL to Current TVL for new pool entry.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 TVL Decline</div>
                <div class="metric-value {get_value_color('TVL Decline', tvl_decline)}">{tvl_decline:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔗 Pool Share</div>
            <div class="metric-value {get_value_color('Pool Share', pool_share)}">{pool_share:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h1>Margin of Safety</h1>", unsafe_allow_html=True)
    st.write(f"**APY Margin of Safety:** {apy_mos:.2f}% (APY can decrease by this percentage before breakeven exceeds 12 months)  ")
    mos_assessment = "✅ High" if apy_mos > 50 else "⚠️ Low"
    st.write(f"**Margin of Safety Assessment:** {mos_assessment} Margin of Safety  ")

    st.markdown("---")
    st.markdown("<h1>Risk Management</h1>", unsafe_allow_html=True)
    if pool_share < 5:
        st.success(f"✅ **Pool Share Risk:** Low ({pool_share:.2f}%). Minimal impact expected on pool prices due to small share.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ **Pool Share Risk:** Moderate ({pool_share:.2f}%). Potential for price impact due to moderate pool share.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ **Pool Share Risk:** High ({pool_share:.2f}%). Significant price impact possible due to high pool share.")
    else:
        st.error(f"⚠️ **Pool Share Risk:** Critical ({pool_share:.2f}%). High risk of severe price impact due to very large pool share.")

    if initial_tvl > 0:
        if tvl_decline >= 50:
            st.error(f"⚠️ **TVL Decline Risk:** Critical ({tvl_decline:.2f}% decline). High risk of significant loss due to substantial TVL reduction.")
        elif tvl_decline >= 30:
            st.warning(f"⚠️ **TVL Decline Risk:** High ({tvl_decline:.2f}% decline). Elevated risk due to significant TVL reduction.")
        elif tvl_decline >= 15:
            st.warning(f"⚠️ **TVL Decline Risk:** Moderate ({tvl_decline:.2f}% decline). Potential risk due to moderate TVL reduction.")
        else:
            st.success(f"✅ **TVL Decline Risk:** Low ({tvl_decline:.2f}% decline). Pool health appears stable with minimal TVL reduction.")
    
    if protocol_risk_category == "Critical":
        st.error(f"⚠️ **Protocol Risk:** {protocol_risk_message.split('⚠️ Protocol Risk: ')[1]}")
    elif protocol_risk_category in ["High", "Advisory"]:
        st.warning(f"⚠️ **Protocol Risk:** {protocol_risk_message.split('⚠️ Protocol Risk: ')[1]}")
    else:
        st.success(f"✅ **Protocol Risk:** {protocol_risk_message.split('✅ Protocol Risk: ')[1]}")

    if volatility_score > 25:
        st.warning(f"⚠️ **Volatility Score:** {volatility_message.split('⚠️ Volatility Score: ')[1]}")
    else:
        st.success(f"✅ **Volatility Score:** {volatility_message.split('✅ Volatility Score: ')[1]}")

    st.markdown("---")
    st.markdown("<h1>Investment Risk Alert</h1>", unsafe_allow_html=True)
    if initial_tvl > 0:
        if net_return < 1.0 or tvl_decline >= 50 or protocol_risk_score >= 75:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x, TVL Decline {tvl_decline:.2f}%, Protocol Risk {protocol_risk_score:.0f}% indicate severe risks.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        elif apy < hurdle_rate or net_return < 1.1 or volatility_score > 25:
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            if volatility_score > 25:
                reasons.append(f"moderate volatility ({volatility_score:.0f}%)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability with low risk.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
    else:
        if net_return < 1.0:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x indicates a loss.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        elif apy < hurdle_rate or net_return < 1.1:
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos

# [Rest of the Streamlit app code remains unchanged]
