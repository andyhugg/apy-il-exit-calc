import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Pool Profit and Risk Analyzer Functions
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float, initial_investment: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    return round(il_percentage, 2) if il_percentage > 0.01 else il_percentage

def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                        current_price_asset1: float, current_price_asset2: float) -> tuple[float, float]:
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    
    il_impact = (value_if_held - pool_value) / value_if_held * 100 if value_if_held > 0 else 0
    return pool_value, il_impact

def calculate_future_value(initial_investment: float, apy: float, months: int, initial_price_asset1: float, initial_price_asset2: float,
                          current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                          expected_price_change_asset2: float, is_new_pool: bool = False) -> tuple[float, float]:
    if months < 0:
        return initial_investment, 0.0

    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12

    if is_new_pool:
        starting_price_asset1 = current_price_asset1
        starting_price_asset2 = current_price_asset2
        initial_adjusted_price_asset1 = current_price_asset1
        initial_adjusted_price_asset2 = current_price_asset2
        initial_pool_value, _ = calculate_pool_value(initial_investment, starting_price_asset1, starting_price_asset2,
                                                    initial_adjusted_price_asset1, initial_adjusted_price_asset2)
        pool_value = initial_pool_value
    else:
        pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                            current_price_asset1, current_price_asset2)
        starting_price_asset1 = initial_price_asset1
        starting_price_asset2 = initial_price_asset2

    if months == 0:
        return round(pool_value, 2), calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)

    apy_compounded_value = pool_value * (1 + monthly_apy) ** months

    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)

    new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                           final_price_asset1, final_price_asset2)

    future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
    current_value = apy_compounded_value + (new_pool_value - pool_value)

    return round(current_value, 2), future_il

def calculate_break_even_months(apy: float, il: float, initial_pool_value: float, value_if_held: float) -> float:
    if apy <= 0 or initial_pool_value <= 0 or value_if_held <= initial_pool_value:
        return 0
    
    monthly_apy = (apy / 100) / 12
    months = 0
    current_value = initial_pool_value
    
    while current_value < value_if_held and months < 1000:
        current_value *= (1 + monthly_apy)
        months += 1
    
    return round(months, 2) if months < 1000 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment: float, apy: float, pool_value: float,
                                                  initial_price_asset1: float, initial_price_asset2: float,
                                                  current_price_asset1: float, current_price_asset2: float,
                                                  expected_price_change_asset1: float, expected_price_change_asset2: float,
                                                  value_if_held: float, is_new_pool: bool = False) -> float:
    if apy <= 0:
        return float('inf')

    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    months = 0
    current_value = pool_value

    while current_value < value_if_held and months < 1000:
        months += 1
        final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                               final_price_asset1, final_price_asset2)
        current_value = pool_value * (1 + monthly_apy) ** months + (new_pool_value - pool_value)

    return round(months, 2) if months < 1000 else float('inf')

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_change = (current_tvl - initial_tvl) / initial_tvl * 100
    return round(tvl_change, 2)

def calculate_apy_margin_of_safety(initial_pool_value: float, value_if_held: float, current_apy: float, months: int = 12) -> float:
    target_value = value_if_held * 1.02
    min_apy = ((target_value / initial_pool_value) ** (12 / months) - 1) * 100
    apy_mos = ((current_apy - min_apy) / current_apy) * 100 if current_apy > 0 else 0
    return max(0, min(apy_mos, 100))

def calculate_volatility_score(il_percentage: float, tvl_decline: float) -> tuple[float, str]:
    il_factor = min(il_percentage / 5, 1.0)
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)
    volatility_score = (il_factor + tvl_factor) * 25
    final_score = min(volatility_score, 50)

    if final_score <= 25:
        message = f"✅ Volatility Score: Low ({final_score:.0f}%). Stable conditions with low IL and TVL decline."
    else:
        message = f"⚠️ Volatility Score: Moderate ({final_score:.0f}%). Moderate IL or TVL decline may impact returns."
    
    return final_score, message

def calculate_protocol_risk_score(apy: float, tvl_decline: float, current_tvl: float, trust_score: int) -> tuple[float, str, str]:
    base_score = 0
    # APY-based risk
    if apy < 10:
        base_score += 40
    elif apy <= 15:
        base_score += 20

    # TVL decline-based risk (only penalize declines, i.e., negative tvl_decline)
    if tvl_decline < -50:  # Major decline
        base_score += 40
    elif tvl_decline < -30:  # Significant decline
        base_score += 30
    elif tvl_decline < -15:  # Moderate decline
        base_score += 15

    # TVL size-based risk
    if current_tvl < 50000:
        base_score += 40
    elif current_tvl <= 200000:
        base_score += 20
    
    base_score = min(base_score, 100)
    
    # Adjust score based on trust_score
    if trust_score == 1:
        adjusted_score = base_score * 1.5
    elif trust_score == 2:
        adjusted_score = base_score * 1.25
    elif trust_score == 3:
        adjusted_score = base_score * 0.9
    elif trust_score == 4:
        adjusted_score = base_score * 0.75
    else:
        adjusted_score = base_score * 0.5
    
    adjusted_score = min(adjusted_score, 100)
    
    # Identify risk factors
    risk_factors = []
    if apy < 10:
        risk_factors.append("low yield")
    elif apy <= 15:
        risk_factors.append("moderate yield")
    if tvl_decline < -50:
        risk_factors.append("major TVL decline")
    elif tvl_decline < -30:
        risk_factors.append("significant TVL decline")
    elif tvl_decline < -15:
        risk_factors.append("moderate TVL decline")
    if current_tvl < 50000:
        risk_factors.append("tiny pool size")
    elif current_tvl <= 200000:
        risk_factors.append("small pool size")
    
    # Determine risk category
    category = None
    if adjusted_score > 75:
        category = "Critical"
    elif adjusted_score > 50:
        category = "High"
    elif trust_score in [1, 2]:
        category = "Advisory"
    elif adjusted_score > 25:
        category = "Advisory"
    else:
        category = "Low"
    
    if category == "Advisory" and trust_score >= 3 and adjusted_score <= 50 and tvl_decline >= -15 and current_tvl > 200000:
        category = "Low"

    # Generate message
    if category == "Low":
        if trust_score >= 3:
            message = f"✅ Protocol Risk: Low ({adjusted_score:.0f}%). Minimal risk due to moderate/good/excellent trust score, stable TVL, and adequate yield."
        else:
            message = f"✅ Protocol Risk: Low ({adjusted_score:.0f}%). Minimal risk of protocol failure due to high yield, stable TVL, large pool size, or excellent trust score."
    elif category == "Advisory":
        if not risk_factors and trust_score in [1, 2]:
            message = f"⚠️ Protocol Risk: Advisory ({adjusted_score:.0f}%). Potential protocol risk due to low trust score."
        else:
            risk_message = " and ".join(risk_factors)
            message = f"⚠️ Protocol Risk: Advisory ({adjusted_score:.0f}%). Potential protocol risk due to {risk_message}"
            if trust_score in [1, 2]:
                message += " and low trust score"
            message += "."
    elif category == "High":
        risk_message = " and ".join(risk_factors)
        message = f"⚠️ Protocol Risk: High ({adjusted_score:.0f}%). Elevated risk of protocol failure due to {risk_message}"
        if trust_score in [1, 2]:
            message += " and low trust score"
        message += "."
    else:
        risk_message = " and ".join(risk_factors)
        message = f"⚠️ Protocol Risk: Critical ({adjusted_score:.0f}%). High risk of protocol failure due to {risk_message}"
        if trust_score in [1, 2]:
            message += " and low trust score"
        message += "."
    
    return adjusted_score, message, category

def simplified_monte_carlo_analysis(initial_investment: float, apy: float, initial_price_asset1: float, initial_price_asset2: float,
                                   current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                                   expected_price_change_asset2: float, is_new_pool: bool, num_simulations: int = 200) -> dict:
    apy_range = [max(apy * 0.5, 0), apy * 1.5]  # Floor APY at 0%
    price_change_asset1_range = [expected_price_change_asset1 * 0.5, expected_price_change_asset1 * 1.5] if expected_price_change_asset1 >= 0 else [expected_price_change_asset1 * 1.5, expected_price_change_asset1 * 0.5]
    price_change_asset2_range = [expected_price_change_asset2 * 0.5, expected_price_change_asset2 * 1.5] if expected_price_change_asset2 >= 0 else [expected_price_change_asset2 * 1.5, expected_price_change_asset2 * 0.5]

    # Generate 200 random scenarios
    apy_samples = np.random.uniform(apy_range[0], apy_range[1], num_simulations)
    price_change_asset1_samples = np.random.uniform(price_change_asset1_range[0], price_change_asset1_range[1], num_simulations)
    price_change_asset2_samples = np.random.uniform(price_change_asset2_range[0], price_change_asset2_range[1], num_simulations)

    values = []
    ils = []
    for i in range(num_simulations):
        value, il = calculate_future_value(initial_investment, apy_samples[i], 12, initial_price_asset1, initial_price_asset2,
                                          current_price_asset1, current_price_asset2, price_change_asset1_samples[i],
                                          price_change_asset2_samples[i], is_new_pool)
        values.append(value)
        ils.append(il)
    
    # Percentiles and exact expected case
    worst_value, worst_il = sorted(zip(values, ils))[19]  # 10th percentile (20th of 200)
    best_value, best_il = sorted(zip(values, ils))[179]   # 90th percentile (180th of 200)
    expected_value, expected_il = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    
    return {
        "worst": {"value": worst_value, "il": worst_il},
        "expected": {"value": expected_value, "il": expected_il},
        "best": {"value": best_value, "il": best_il}
    }

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
    
    # Calculate ARIL (Annualized Return After Impermanent Loss)
    aril = ((future_value / initial_investment) - 1) * 100  # Since it's over 12 months, this is already annualized
    
    # Simplified Hurdle Rate: Risk-Free Rate + 6% global inflation
    hurdle_rate = risk_free_rate + 6.0
    target_aril = hurdle_rate * 2  # Double the Hurdle Rate for risk compensation
    
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)
    volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)
    protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    # Core Metrics Section with Updated Styling
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>Core Metrics</h1>", unsafe_allow_html=True)

    # Custom CSS for metric cards with increased height to fit all text
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1f2a44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
        height: 250px;  /* Increased height to fit all text */
        display: flex;
        flex-direction: column;
        justify-content: space-between;  /* Distribute content vertically */
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
        flex: 1;  /* Allow note to take remaining space */
        white-space: normal;  /* Allow text wrapping */
        overflow-wrap: break-word;  /* Break long words */
    }
    </style>
    """, unsafe_allow_html=True)

    # Split into two columns
    col1, col2 = st.columns(2)

    # Helper function to determine value color
    def get_value_color(metric_name, value):
        if metric_name in ["Impermanent Loss", "TVL Decline", "Projected Impermanent Loss"]:
            return "red" if value > 0 else "green"
        elif metric_name == "TVL Growth":
            return "green" if value >= 0 else "red"
        elif metric_name == "Net Return":
            return "green" if value > 1 else "red"
        elif metric_name in ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"]:
            return "green" if value <= 12 else "red"
        elif metric_name == "Pool Share":
            return "green" if value < 5 else "red"
        elif metric_name == "ARIL":
            if value < 0:
                return "red"
            elif value >= target_aril:
                return "green"
            else:
                return "neutral"
        return "neutral"

    # Metrics for Column 1 (4 cards)
    with col1:
        # Impermanent Loss (at current time) with Actionable Note
        if initial_tvl <= 0:
            if is_new_pool:
                il_note = "Your pool has no impermanent loss as it’s a new pool. Monitor price changes to manage future IL."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">{il_note}</div>
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
                if il == 0:
                    il_note = "Your pool has no impermanent loss, performing as well as holding the assets. Continue monitoring price changes to maintain this balance."
                elif 0 < il <= 5:
                    il_note = f"Your pool has a {il:.2f}% impermanent loss due to price divergence. This is relatively low but indicates a small loss compared to holding. Monitor price changes closely to ensure IL doesn’t increase further."
                else:
                    il_note = f"Your pool has a {il:.2f}% impermanent loss due to price divergence, which is significant. Consider reassessing your price change expectations or exiting the pool to minimize further loss."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                    <div class="metric-note">{il_note}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if is_new_pool:
                il_note = "Your pool has no impermanent loss as it’s a new pool. Monitor price changes to manage future IL."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00)}">0.00%</div>
                    <div class="metric-note">{il_note}</div>
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
                if il == 0:
                    il_note = "Your pool has no impermanent loss, performing as well as holding the assets. Continue monitoring price changes to maintain this balance."
                elif 0 < il <= 5:
                    il_note = f"Your pool has a {il:.2f}% impermanent loss due to price divergence. This is relatively low but indicates a small loss compared to holding. Monitor price changes closely to ensure IL doesn’t increase further."
                else:
                    il_note = f"Your pool has a {il:.2f}% impermanent loss due to price divergence, which is significant. Consider reassessing your price change expectations or exiting the pool to minimize further loss."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Impermanent Loss (at current time)</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', il)}">{il:.2f}%</div>
                    <div class="metric-note">{il_note}</div>
                </div>
                """, unsafe_allow_html=True)

        # Months to Breakeven Against IL with Actionable Note
        if break_even_months == 0:
            break_even_note = "There’s no impermanent loss to breakeven against. Your pool is performing as well as holding—focus on maintaining this balance."
        elif break_even_months == float('inf'):
            break_even_note = "Your pool cannot breakeven against its impermanent loss with the current APY. Consider exiting or increasing APY through a different pool."
        elif break_even_months <= 12:
            break_even_note = f"Your pool will offset its impermanent loss in {break_even_months} months at the current APY. This is a short breakeven period, indicating good recovery potential. Ensure APY remains stable to achieve this."
        else:
            break_even_note = f"Your pool will take {break_even_months} months to offset its impermanent loss at the current APY, which is too long to justify the risk. Consider exiting or finding a pool with a higher APY."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Against IL</div>
            <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months)}">{break_even_months} months</div>
            <div class="metric-note">{break_even_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Months to Breakeven Including Expected Price Changes with Actionable Note
        if break_even_months_with_price == 0:
            break_even_price_note = "There’s no impermanent loss to breakeven against, even with expected price changes. Focus on maintaining this balance."
        elif break_even_months_with_price == float('inf'):
            break_even_price_note = "Your pool cannot breakeven against its impermanent loss with the current APY and price changes. Reassess your strategy or exit the pool."
        elif break_even_months_with_price <= 12:
            break_even_price_note = f"Including expected price changes, your pool will offset its impermanent loss in {break_even_months_with_price} months. This short timeline supports holding, but ensure your price change assumptions remain accurate."
        else:
            break_even_price_note = f"Including expected price changes, your pool will take {break_even_months_with_price} months to offset its impermanent loss, which is too long. Adjust your price change expectations or consider exiting the pool."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Months to Breakeven Including Expected Price Changes</div>
            <div class="metric-value {get_value_color('Months to Breakeven Including Expected Price Changes', break_even_months_with_price)}">{break_even_months_with_price} months</div>
            <div class="metric-note">{break_even_price_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # TVL Growth with Actionable Note
        if initial_tvl <= 0:
            tvl_note = "Set Initial TVL to Current TVL for new pool entry to calculate TVL change."
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 TVL Change</div>
                <div class="metric-value">Cannot calculate</div>
                <div class="metric-note">{tvl_note}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            metric_name = "TVL Growth" if tvl_decline >= 0 else "TVL Decline"
            display_value = abs(tvl_decline)
            if tvl_decline >= 0:
                tvl_note = f"Your pool’s TVL has grown by {display_value:.2f}%, indicating increased liquidity and interest. This is a positive sign for fee stability—continue monitoring TVL trends to ensure growth persists."
            elif tvl_decline > -15:
                tvl_note = f"Your pool’s TVL has declined by {display_value:.2f}%, a small drop. This may affect fees slightly—watch for ongoing trends to assess risk."
            elif tvl_decline > -50:
                tvl_note = f"Your pool’s TVL has declined by {display_value:.2f}%, which may impact fees and liquidity. Monitor closely for further decline before deciding to exit."
            else:
                tvl_note = f"Your pool’s TVL has declined by {display_value:.2f}%, signaling high risk of reduced liquidity and fees. Consider exiting to avoid potential losses."
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 {metric_name}</div>
                <div class="metric-value {get_value_color(metric_name, tvl_decline)}">{display_value:.2f}%</div>
                <div class="metric-note">{tvl_note}</div>
            </div>
            """, unsafe_allow_html=True)

    # Metrics for Column 2 (4 cards)
    with col2:
        # Net Return with Actionable Note
        if net_return < 0.95:
            net_return_note = f"Your pool’s net return is {net_return:.2f}x after 12 months, indicating a loss (includes expected price changes for Asset 1 and Asset 2). Reassess your price change expectations or consider exiting the pool."
        elif 0.95 <= net_return <= 1.05:
            net_return_note = f"Your pool’s net return is {net_return:.2f}x after 12 months, close to breakeven (includes expected price changes for Asset 1 and Asset 2). Evaluate if the risk justifies staying in the pool."
        else:
            net_return_note = f"Your pool’s net return is {net_return:.2f}x after 12 months, indicating profitability (includes expected price changes for Asset 1 and Asset 2). Monitor price movements to sustain these gains."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Net Return</div>
            <div class="metric-value {get_value_color('Net Return', net_return)}">{net_return:.2f}x</div>
            <div class="metric-note">{net_return_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Hurdle Rate with Actionable Note
        hurdle_rate_note = f"Your Hurdle Rate is {hurdle_rate:.1f}% ({risk_free_rate:.1f}% risk-free rate + 6% inflation). To justify risk, your ARIL should exceed this and ideally reach {target_aril:.1f}% (2× Hurdle Rate). Compare with your ARIL to assess performance."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Hurdle Rate</div>
            <div class="metric-value {get_value_color('Hurdle Rate', hurdle_rate)}">{hurdle_rate:.2f}%</div>
            <div class="metric-note">{hurdle_rate_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Annualized Return After IL (ARIL) with Actionable Note
        if aril < 0:  # Loss Scenario
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, below the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates a loss. Consider reallocating to a stablecoin pool yielding {risk_free_rate:.1f}% or reassessing price change expectations to reduce impermanent loss."
        elif 0 <= aril < hurdle_rate:  # Underperformance
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, below the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates underperformance. Consider reallocating to a stablecoin pool yielding {risk_free_rate:.1f}% or adjusting your strategy to improve returns."
        elif hurdle_rate <= aril < target_aril:  # Marginal Performance
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, above the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) but below the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. Returns are marginal for the risk taken. Evaluate if this aligns with your investment goals."
        else:  # Outperformance (ARIL >= 2 × Hurdle Rate)
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, exceeding the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates strong profitability. Continue monitoring price changes to sustain this performance."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Annualized Return After IL (ARIL)</div>
            <div class="metric-value {get_value_color('ARIL', aril)}">{aril:.1f}%</div>
            <div class="metric-note">{aril_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Pool Share with Actionable Note
        if pool_share < 5:
            pool_share_note = f"Your pool share is {pool_share:.2f}%, meaning your investment has minimal impact on pool prices. You can withdraw without significant price effects—proceed as needed."
        elif 5 <= pool_share < 10:
            pool_share_note = f"Your pool share is {pool_share:.2f}%, indicating a moderate impact on pool prices. Withdraw with caution to avoid affecting prices."
        else:
            pool_share_note = f"Your pool share is {pool_share:.2f}%, which could significantly impact pool prices. Plan withdrawals carefully to minimize price disruption."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔗 Pool Share</div>
            <div class="metric-value {get_value_color('Pool Share', pool_share)}">{pool_share:.2f}%</div>
            <div class="metric-note">{pool_share_note}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h1>Margin of Safety</h1>", unsafe_allow_html=True)
    st.write(f"**APY Margin of Safety:** {apy_mos:.2f}% (APY can decrease by this percentage before breakeven exceeds 12 months)  ")
    mos_assessment = "✅ High" if apy_mos > 50 else "⚠️ Low"
    st.write(f"**Margin of Safety Assessment:** {mos_assessment} Margin of Safety  ")

    st.markdown("---")
    st.markdown("<h1>Risk Management</h1>", unsafe_allow_html=True)

    # Add ARIL Assessment with highlighting
    if aril < 0:  # Loss Scenario
        st.warning(f"⚠️ **ARIL Assessment:** Your pool’s effective return (ARIL) is {aril:.1f}%, compared to the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation). To compensate for risk, your ARIL should be at least double the Hurdle Rate (2 × {hurdle_rate:.1f}% = {target_aril:.1f}%). Your pool is projected to lose value, underperforming the Hurdle Rate by {abs(aril - hurdle_rate):.1f}% and falling far below the target of {target_aril:.1f}%. **Consider reallocating to a stablecoin pool yielding the risk-free rate of {risk_free_rate:.1f}% or reassessing your price change expectations to reduce impermanent loss.**")
    elif 0 <= aril < hurdle_rate:  # Underperformance
        st.warning(f"⚠️ **ARIL Assessment:** Your pool’s effective return (ARIL) is {aril:.1f}%, compared to the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation). To compensate for risk, your ARIL should be at least double the Hurdle Rate (2 × {hurdle_rate:.1f}% = {target_aril:.1f}%). Your pool underperforms the Hurdle Rate by {abs(aril - hurdle_rate):.1f}% and is below the target of {target_aril:.1f}%. **Consider reallocating to a stablecoin pool yielding the risk-free rate of {risk_free_rate:.1f}% or adjusting your strategy to improve returns.**")
    elif hurdle_rate <= aril < target_aril:  # Marginal Performance
        st.warning(f"⚠️ **ARIL Assessment:** Your pool’s effective return (ARIL) is {aril:.1f}%, compared to the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation). To compensate for risk, your ARIL should be at least double the Hurdle Rate (2 × {hurdle_rate:.1f}% = {target_aril:.1f}%). Your pool meets the Hurdle Rate but is below the target of {target_aril:.1f}% to justify the risk. **The pool’s return is marginal compared to the risk; evaluate if it aligns with your investment goals.**")
    else:  # Outperformance (ARIL >= 2 × Hurdle Rate)
        st.success(f"✅ **ARIL Assessment:** Your pool’s effective return (ARIL) is {aril:.1f}%, compared to the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation). To compensate for risk, your ARIL should be at least double the Hurdle Rate (2 × {hurdle_rate:.1f}% = {target_aril:.1f}%). Your pool exceeds the target of {target_aril:.1f}%, justifying the risk. **Monitor impermanent loss and price changes to maintain this performance.**")

    if pool_share < 5:
        st.success(f"✅ **Pool Share Risk:** Low ({pool_share:.2f}%). Minimal impact expected on pool prices due to small share.")
    elif 5 <= pool_share < 10:
        st.warning(f"⚠️ **Pool Share Risk:** Moderate ({pool_share:.2f}%). Potential for price impact due to moderate pool share.")
    elif 10 <= pool_share < 20:
        st.warning(f"⚠️ **Pool Share Risk:** High ({pool_share:.2f}%). Significant price impact possible due to high pool share.")
    else:
        st.error(f"⚠️ **Pool Share Risk:** Critical ({pool_share:.2f}%). High risk of severe price impact due to very large pool share.")

    if initial_tvl > 0:
        if tvl_decline <= -50:
            st.error(f"⚠️ **TVL Decline Risk:** Critical ({abs(tvl_decline):.2f}% decline). High risk of significant loss due to substantial TVL reduction.")
        elif tvl_decline <= -30:
            st.warning(f"⚠️ **TVL Decline Risk:** High ({abs(tvl_decline):.2f}% decline). Elevated risk due to significant TVL reduction.")
        elif tvl_decline <= -15:
            st.warning(f"⚠️ **TVL Decline Risk:** Moderate ({abs(tvl_decline):.2f}% decline). Potential risk due to moderate TVL reduction.")
        else:
            st.success(f"✅ **TVL Change:** {tvl_decline:.2f}%. Pool health appears stable with minimal TVL reduction or growth.")
    
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
        if net_return < 1.0 or tvl_decline <= -50 or protocol_risk_score >= 75 or aril < 0:  # Add ARIL < 0 condition
            reasons = []
            if net_return < 1.0:
                reasons.append(f"Net Return {net_return:.2f}x indicates a loss")
            if tvl_decline <= -50:
                reasons.append(f"TVL Decline {abs(tvl_decline):.2f}%")
            if protocol_risk_score >= 75:
                reasons.append(f"Protocol Risk {protocol_risk_score:.0f}%")
            if aril < 0:
                reasons.append(f"ARIL {aril:.1f}% indicates a loss")
            reason_str = ", ".join(reasons)
            st.error(f"⚠️ **Investment Risk:** Critical. {reason_str} indicate severe risks.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
        elif apy < hurdle_rate or net_return < 1.1 or volatility_score > 25 or (aril < hurdle_rate - 10):  # Add ARIL vs Hurdle Rate condition
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            if volatility_score > 25:
                reasons.append(f"moderate volatility ({volatility_score:.0f}%)")
            if aril < hurdle_rate - 10:
                reasons.append(f"ARIL {aril:.1f}% underperforms Hurdle Rate ({hurdle_rate:.1f}%) by {abs(aril - hurdle_rate):.1f}%")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability with low risk.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
    else:
        if net_return < 1.0 or aril < 0:  # Add ARIL < 0 condition
            reasons = []
            if net_return < 1.0:
                reasons.append(f"Net Return {net_return:.2f}x indicates a loss")
            if aril < 0:
                reasons.append(f"ARIL {aril:.1f}% indicates a loss")
            reason_str = ", ".join(reasons)
            st.error(f"⚠️ **Investment Risk:** Critical. {reason_str}.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
        elif apy < hurdle_rate or net_return < 1.1 or (aril < hurdle_rate - 10):  # Add ARIL vs Hurdle Rate condition
            reasons = []
            if apy < hurdle_rate:
                reasons.append(f"APY below Hurdle Rate ({hurdle_rate:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            if aril < hurdle_rate - 10:
                reasons.append(f"ARIL {aril:.1f}% underperforms Hurdle Rate ({hurdle_rate:.1f}%) by {abs(aril - hurdle_rate):.1f}%")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability.")
            return break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril

# Streamlit App
st.title("Pool Profit and Risk Analyzer")

st.markdown("""
Welcome to the Pool Profit and Risk Analyzer! This tool helps you evaluate the profitability and risks of liquidity pools in DeFi. By inputting your pool parameters, you can assess impermanent loss, net returns, and potential drawdowns, empowering you to make informed investment decisions. **Disclaimer:** This tool is for informational purposes only and does not constitute financial advice. Projections are estimates based on the inputs provided and are not guaranteed to reflect actual future outcomes.
""")

st.markdown("""
<style>
div[data-testid="stSidebar"] select {
    background-color: #1a1a1a;
    color: #ffffff;
}
div[data-testid="stSidebar"] select option {
    background-color: #1a1a1a;
    color: #ffffff;
}
div[data-testid="stSidebar"] select option:checked {
    background-color: #333333;
    color: #ffffff;
}
div[data-testid="stSidebar"] select option:hover {
    background-color: #444444;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Set Your Pool Parameters")

pool_status = st.sidebar.selectbox("Pool Status", ["Existing Pool", "New Pool"])
is_new_pool = (pool_status == "New Pool")

if is_new_pool:
    current_price_asset1 = st.sidebar.number_input("Asset 1 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Asset 2 Price (Entry, Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    initial_price_asset1 = current_price_asset1
    initial_price_asset2 = current_price_asset2
else:
    initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.01, step=0.01, value=88000.00, format="%.2f")
    initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
    current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.01, step=0.01, value=125000.00, format="%.2f")
    current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.01, step=0.01, value=1.00, format="%.2f")

apy = st.sidebar.number_input("Current APY (%)", min_value=0.01, step=0.01, value=1.00, format="%.2f")
st.sidebar.markdown("**Note:** **Annual Percentage Yield** For conservative projections, consider halving the entered APY to buffer against market volatility.")

trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
st.sidebar.markdown("""
**Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
- 1 = Unknown (default, highest caution)
- 2 = Poor (known but with concerns)
- 3 = Moderate (neutral, some audits)
- 4 = Good (trusted, audited)
- 5 = Excellent (top-tier, e.g., Uniswap, Aave)
""")

investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=2000.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", 
                                     min_value=0.01, step=0.01, value=750000.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")

expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")
expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-30.0, format="%.2f")
st.sidebar.markdown("**Note:** We’ll take your expected APY and price changes, stretch them 50% up and down (e.g., 10% becomes 5-15%), and run 200 scenarios to project your pool’s value over 12 months.")

initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                           min_value=0.0, step=0.01, value=84000.00, format="%.2f")
current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=84000.00, format="%.2f")
btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=-25.0, format="%.2f")

risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
st.sidebar.markdown("""
**Note:** The Risk-Free Rate is what you could earn in a safe pool (e.g., 5-15%) with no price volatility, such as a stablecoin pool. This rate is used as the stablecoin yield in the "Pool vs. BTC vs. Stablecoin Comparison" section. The Hurdle Rate is this rate plus 6% (average global inflation in 2025), setting the minimum APY your pool needs to beat to outpace inflation and justify the risk.
""")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        pool_value, il_impact = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
        value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
        tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)
        break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
        break_even_months_with_price = calculate_break_even_months_with_price_changes(
            investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
        )
        result = check_exit_conditions(
            investment_amount, apy, il, tvl_decline, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, risk_free_rate, trust_score, 12, expected_price_change_asset1, expected_price_change_asset2, is_new_pool, btc_growth_rate
        )
        break_even_months, net_return, break_even_months_with_price, hurdle_rate, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, aril = result
        
        st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
        st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${investment_amount:,.2f}).")
        time_periods = [0, 3, 6, 12]
        future_values = []
        future_ils = []
        for months in time_periods:
            value, il_at_time = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                      current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                      expected_price_change_asset2, is_new_pool)
            future_values.append(value)
            future_ils.append(il_at_time)
        
        formatted_pool_values = [f"{int(value):,}" for value in future_values]
        formatted_ils = [f"{il:.2f}%" for il in future_ils]
        df_projection = pd.DataFrame({
            "Time Period (Months)": time_periods,
            "Projected Value ($)": formatted_pool_values,
            "Projected Impermanent Loss (%)": formatted_ils
        })
        styled_df = df_projection.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Projected Value ($)", "Projected Impermanent Loss (%)"]).set_properties(**{
            'text-align': 'right'
        }, subset=["Time Period (Months)"])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        
        # Enhanced Matplotlib Chart
        sns.set_theme()  # Apply Seaborn's default theme for better aesthetics
        plt.figure(figsize=(10, 6))
        
        # Plot the pool value line with markers
        plt.plot(time_periods, future_values, marker='o', markersize=10, linewidth=3, color='#1f77b4', label="Pool Value")
        
        # Fill the area under the line
        plt.fill_between(time_periods, future_values, color='#1f77b4', alpha=0.2)
        
        # Plot the initial investment line
        plt.axhline(y=investment_amount, color='#ff3333', linestyle='--', linewidth=2, label=f"Initial Investment (${investment_amount:,.0f})")
        
        # Add profit/loss zones
        y_max = max(max(future_values), investment_amount) * 1.1  # Extend y-axis slightly
        y_min = min(min(future_values), investment_amount) * 0.9
        plt.fill_between(time_periods, investment_amount, y_max, color='green', alpha=0.1, label='Profit Zone')
        plt.fill_between(time_periods, y_min, investment_amount, color='red', alpha=0.1, label='Loss Zone')
        
        # Add data labels above each point
        for i, value in enumerate(future_values):
            plt.text(time_periods[i], value + (y_max - y_min) * 0.05, f"${value:,.0f}", ha='center', fontsize=10, color='#1f77b4')
        
        # Add annotation for the final value at 12 months
        final_value = future_values[-1]
        plt.annotate(f"Final Value: ${final_value:,.0f}", 
                     xy=(12, final_value), 
                     xytext=(10, final_value + (y_max - y_min) * 0.15),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                     fontsize=10, color='black')
        
        # Customize the chart
        plt.title("Projected Pool Value Over Time", fontsize=16, pad=20)
        plt.xlabel("Months", fontsize=12)
        plt.ylabel("Value ($)", fontsize=12)
        plt.xticks(time_periods, fontsize=10)
        plt.yticks(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(fontsize=10)
        plt.gca().set_facecolor('#f0f0f0')  # Light gray background for the plot area
        plt.tight_layout()
        st.pyplot(plt)

        st.subheader("Pool vs. BTC vs. Stablecoin Comparison | 12 Months | Compounding on Pool Assets Only")
        asset1_change_desc = "appreciation" if expected_price_change_asset1 >= 0 else "depreciation"
        asset2_change_desc = "appreciation" if expected_price_change_asset2 >= 0 else "depreciation"
        asset1_change_text = f"{abs(expected_price_change_asset1):.1f}% {asset1_change_desc}" if expected_price_change_asset1 != 0 else "no change"
        asset2_change_text = f"{abs(expected_price_change_asset2):.1f}% {asset2_change_desc}" if expected_price_change_asset2 != 0 else "no change"
        st.write(f"**Note:** Pool Value is based on an expected {asset1_change_text} for Asset 1, {asset2_change_text} for Asset 2, and a compounded APY of {apy:.1f}% over 12 months. BTC comparison assumes a {btc_growth_rate:.1f}% annual growth rate. Stablecoin comparison assumes the risk-free rate of {risk_free_rate:.1f}% APY with no price volatility, for comparison purposes only.")
        
        projected_btc_price = initial_btc_price * (1 + btc_growth_rate / 100) if initial_btc_price > 0 else current_btc_price * (1 + btc_growth_rate / 100)
        
        if initial_btc_price == 0.0 or initial_btc_price == current_btc_price:
            initial_btc_amount = investment_amount / current_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        else:
            initial_btc_amount = investment_amount / initial_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        
        pool_value_12_months = future_values[-1]
        difference_pool_btc = pool_value_12_months - btc_value_12_months
        pool_return_pct = (pool_value_12_months / investment_amount - 1) * 100
        btc_return_pct = (btc_value_12_months / investment_amount - 1) * 100
        
        # Calculate Stablecoin return using the risk-free rate as the APY over 12 months
        stablecoin_value_12_months = investment_amount * (1 + risk_free_rate / 100)
        difference_pool_stablecoin = pool_value_12_months - stablecoin_value_12_months
        stablecoin_return_pct = (stablecoin_value_12_months / investment_amount - 1) * 100
        
        formatted_pool_value_12 = f"{int(pool_value_12_months):,}"
        formatted_btc_value_12 = f"{int(btc_value_12_months):,}"
        formatted_stablecoin_value_12 = f"{int(stablecoin_value_12_months):,}"
        formatted_difference_pool_btc = f"{int(difference_pool_btc):,}" if difference_pool_btc >= 0 else f"({int(abs(difference_pool_btc)):,})"
        formatted_difference_pool_stablecoin = f"{int(difference_pool_stablecoin):,}" if difference_pool_stablecoin >= 0 else f"({int(abs(difference_pool_stablecoin)):,})"
        formatted_pool_return = f"{pool_return_pct:.2f}%"
        formatted_btc_return = f"{btc_return_pct:.2f}%"
        formatted_stablecoin_return = f"{stablecoin_return_pct:.2f}%"
        
        df_btc_comparison = pd.DataFrame({
            "Metric": [
                "Projected Pool Value",
                "Value if Invested in BTC Only",
                f"Value if Invested in Stablecoin Pool (Risk-Free Rate: {risk_free_rate:.1f}% APY)",
                "Difference (Pool - BTC)",
                "Difference (Pool - Stablecoin)",
                "Pool Return (%)",
                "BTC Return (%)",
                "Stablecoin Return (%)"
            ],
            "Value": [
                formatted_pool_value_12,
                formatted_btc_value_12,
                formatted_stablecoin_value_12,
                formatted_difference_pool_btc,
                formatted_difference_pool_stablecoin,
                formatted_pool_return,
                formatted_btc_return,
                formatted_stablecoin_return
            ]
        })
        styled_df_btc = df_btc_comparison.style.set_properties(**{
            'text-align': 'right'
        }).apply(lambda x: ['color: red' if x.name == 'Value' and x[1].startswith('(') else '' for i in x], axis=1)
        st.dataframe(styled_df_btc, hide_index=True, use_container_width=True)
        
        st.subheader("Maximum Drawdown Risk Scenarios")
        mdd_scenarios = [10, 30, 65, 100]
        btc_mdd_scenarios = [10, 30, 65, 90]

        st.subheader("MDD from Initial Investment")
        st.write("**Note:** Simulated maximum drawdowns based on initial investment. Pool MDD assumes IL and TVL decline (e.g., 50% IL + 50% TVL decline for 100% loss). BTC MDD assumes price drops up to 90% (historical worst case).")
        pool_mdd_values_initial = [investment_amount * (1 - mdd / 100) for mdd in mdd_scenarios]
        initial_btc_amount = investment_amount / (initial_btc_price if initial_btc_price > 0 else current_btc_price)
        btc_mdd_values_initial = [initial_btc_amount * (current_btc_price * (1 - mdd / 100)) for mdd in btc_mdd_scenarios]

        formatted_pool_mdd_initial = [f"{int(value):,}" for value in pool_mdd_values_initial]
        formatted_btc_mdd_initial = [f"{int(value):,}" for value in btc_mdd_values_initial]

        df_risk_scenarios_initial = pd.DataFrame({
            "Scenario": ["10% MDD", "30% MDD", "65% MDD", "90%/100% MDD"],
            "Pool Value ($)": formatted_pool_mdd_initial,
            "BTC Value ($)": formatted_btc_mdd_initial
        })
        styled_df_risk_initial = df_risk_scenarios_initial.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Pool Value ($)", "BTC Value ($)"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Scenario"])
        st.dataframe(styled_df_risk_initial, hide_index=True, use_container_width=True)

        st.subheader("MDD from Projected Value After 12 Months")
        st.write(f"**Note:** Simulated maximum drawdowns based on projected values after 12 months, including expected price changes (e.g., {expected_price_change_asset1}% appreciation of Asset 1, {expected_price_change_asset2}% change for Asset 2) and {apy}% APY for the pool, and {btc_growth_rate}% growth for BTC.")
        pool_mdd_values_projected = [future_values[-1] * (1 - mdd / 100) for mdd in mdd_scenarios]
        btc_mdd_values_projected = [btc_value_12_months * (1 - mdd / 100) for mdd in btc_mdd_scenarios]

        formatted_pool_mdd_projected = [f"{int(value):,}" for value in pool_mdd_values_projected]
        formatted_btc_mdd_projected = [f"{int(value):,}" for value in btc_mdd_values_projected]

        df_risk_scenarios_projected = pd.DataFrame({
            "Scenario": ["10% MDD", "30% MDD", "65% MDD", "90%/100% MDD"],
            "Pool Value ($)": formatted_pool_mdd_projected,
            "BTC Value ($)": formatted_btc_mdd_projected
        })
        styled_df_risk_projected = df_risk_scenarios_projected.style.set_properties(**{
            'text-align': 'right'
        }, subset=["Pool Value ($)", "BTC Value ($)"]).set_properties(**{
            'text-align': 'left'
        }, subset=["Scenario"])
        st.dataframe(styled_df_risk_projected, hide_index=True, use_container_width=True)
        
        # Simplified Monte Carlo Analysis
        st.subheader("Simplified Monte Carlo Analysis - 12 Month Projections")
        st.write("""
        **Note:** The Simplified Monte Carlo Analysis runs 200 scenarios by tweaking your expected APY and price changes up and down by 50%. It’s a way to estimate a range of possible outcomes for your pool’s value over 12 months. Here’s how we get the results:  
        - **Worst Case:** The 10th percentile (20th lowest of 200 runs)—a plausible low-end outcome, not the absolute worst.  
        - **Expected Case:** The exact result using your inputs (APY and price changes), showing what happens if everything goes as you predict, no randomization.  
        - **Best Case:** The 90th percentile (20th highest of 200 runs)—a strong outcome, not the absolute best.  
        This gives you a practical snapshot of your pool’s potential over the next year.
        """)
        
        mc_results = simplified_monte_carlo_analysis(
            investment_amount, apy, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1,
            expected_price_change_asset2, is_new_pool
        )
        
        # Table with color-coded backgrounds
        df_monte_carlo = pd.DataFrame({
            "Scenario": ["Worst Case", "Expected Case", "Best Case"],
            "Projected Value ($)": [f"${mc_results['worst']['value']:,.0f}", f"${mc_results['expected']['value']:,.0f}", f"${mc_results['best']['value']:,.0f}"],
            "Impermanent Loss (%)": [f"{mc_results['worst']['il']:.2f}%", f"{mc_results['expected']['il']:.2f}%", f"{mc_results['best']['il']:.2f}%"]
        })
        
        def highlight_rows(row):
            if row["Scenario"] == "Worst Case":
                return ['background-color: #ff4d4d; color: white'] * len(row)
            elif row["Scenario"] == "Expected Case":
                return ['background-color: #ffeb3b; color: black'] * len(row)
            elif row["Scenario"] == "Best Case":
                return ['background-color: #4caf50; color: white'] * len(row)
            return [''] * len(row)
        
        styled_df_monte_carlo = df_monte_carlo.style.apply(highlight_rows, axis=1).set_properties(**{
            'text-align': 'center'
        })
        st.dataframe(styled_df_monte_carlo, hide_index=True, use_container_width=True)
        
        # Bar Chart
        sns.set_theme()  # Apply Seaborn theme for the bar chart
        plt.figure(figsize=(8, 5))
        scenarios = ["Worst", "Expected", "Best"]
        values = [mc_results["worst"]["value"], mc_results["expected"]["value"], mc_results["best"]["value"]]
        colors = ["#ff4d4d", "#ffeb3b", "#4caf50"]
        plt.bar(scenarios, values, color=colors)
        plt.axhline(y=investment_amount, color='r', linestyle='--', label=f"Initial Investment (${investment_amount:,.0f})")
        plt.title("Monte Carlo Scenarios - 12 Month Pool Value", fontsize=16)
        plt.ylabel("Value ($)", fontsize=12)
        plt.legend(fontsize=10)
        plt.gca().set_facecolor('#f0f0f0')
        plt.tight_layout()
        st.pyplot(plt)
        
        # Export to CSV with ARIL included
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        if is_new_pool:
            writer.writerow(["Initial Impermanent Loss (%)", "0.00"])
            writer.writerow(["Projected Impermanent Loss (after 12 months) (%)", f"{future_il:.2f}"])
        else:
            writer.writerow(["Impermanent Loss (at current time) (%)", f"{il:.2f}"])
        writer.writerow(["Months to Breakeven Against IL", f"{break_even_months}"])
        writer.writerow(["Months to Breakeven Including Expected Price Changes", f"{break_even_months_with_price}"])
        writer.writerow(["Net Return (x)", f"{net_return:.2f}"])
        writer.writerow(["Hurdle Rate (%)", f"{hurdle_rate:.2f}"])
        writer.writerow(["TVL Change (%)", f"{tvl_decline:.2f}" if initial_tvl > 0 else "N/A"])
        writer.writerow(["Pool Share (%)", f"{pool_share:.2f}"])
        writer.writerow(["APY Margin of Safety (%)", f"{apy_mos:.2f}"])
        writer.writerow(["Volatility Score (%)", f"{volatility_score:.0f}"])
        writer.writerow(["Protocol Risk Score (%)", f"{protocol_risk_score:.0f}"])
        writer.writerow(["ARIL (%)", f"{aril:.1f}"])
        writer.writerow(["Target ARIL (2x Hurdle Rate) (%)", f"{hurdle_rate * 2:.1f}"])
        writer.writerow(["Monte Carlo Worst Case Value ($)", f"{mc_results['worst']['value']:.0f}"])
        writer.writerow(["Monte Carlo Expected Value ($)", f"{mc_results['expected']['value']:.0f}"])
        writer.writerow(["Monte Carlo Best Case Value ($)", f"{mc_results['best']['value']:.0f}"])
        st.download_button(label="Export Results as CSV", data=output.getvalue(), file_name="pool_analysis_results.csv", mime="text/csv")
