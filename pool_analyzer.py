import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import csv

# Pool Profit and Risk Analyzer
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float, initial_investment: float) -> float:
    if initial_price_asset2 == 0 or current_price_asset2 == 0 or initial_investment <= 0:
        return 0
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    print(f"Debug - calculate_il: value_if_held={value_if_held}")
    
    pool_value = initial_investment * np.sqrt(current_price_asset1 * current_price_asset2) / np.sqrt(initial_price_asset1 * initial_price_asset2)
    print(f"Debug - calculate_il: pool_value={pool_value}")
    
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    print(f"Debug - calculate_il: initial_price_asset1={initial_price_asset1}, initial_price_asset2={initial_price_asset2}, current_price_asset1={current_price_asset1}, current_price_asset2={current_price_asset2}, initial_investment={initial_investment}, il_percentage={il_percentage}")
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

    print(f"Debug - calculate_future_value: months={months}, initial_pool_value={pool_value}")

    if months == 0:
        return round(pool_value, 2), calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)

    apy_compounded_value = pool_value * (1 + monthly_apy) ** months
    print(f"Debug - calculate_future_value: apy_compounded_value={apy_compounded_value}")

    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    print(f"Debug - calculate_future_value: final_price_asset1={final_price_asset1}, final_price_asset2={final_price_asset2}")

    new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                           final_price_asset1, final_price_asset2)
    print(f"Debug - calculate_future_value: new_pool_value={new_pool_value}")

    future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
    current_value = apy_compounded_value + (new_pool_value - pool_value)
    print(f"Debug - calculate_future_value: current_value={current_value}, future_il={future_il}")

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

    print(f"Debug - calculate_break_even_months_with_price_changes: initial_pool_value={pool_value}, value_if_held={value_if_held}")

    while current_value < value_if_held and months < 1000:
        months += 1
        final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                               final_price_asset1, final_price_asset2)
        current_value = pool_value * (1 + monthly_apy) ** months + (new_pool_value - pool_value)
        print(f"Debug - calculate_break_even_months_with_price_changes: months={months}, current_value={current_value}")

    return round(months, 2) if months < 1000 else float('inf')

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_decline = (initial_tvl - current_tvl) / initial_tvl * 100
    return round(tvl_decline, 2)

def calculate_apy_margin_of_safety(initial_pool_value: float, value_if_held: float, current_apy: float, months: int = 12) -> float:
    """
    Calculate APY Margin of Safety: how much APY can drop before breakeven exceeds 12 months.
    Returns percentage (0-100%).
    """
    target_value = value_if_held * 1.02  # 2% risk-free rate buffer
    min_apy = ((target_value / initial_pool_value) ** (12 / months) - 1) * 100
    apy_mos = ((current_apy - min_apy) / current_apy) * 100 if current_apy > 0 else 0
    return max(0, min(apy_mos, 100))  # Cap between 0-100%

def calculate_volatility_score(il_percentage: float, tvl_decline: float) -> tuple[float, str]:
    """
    Calculate Volatility Score based on IL and TVL decline (no price divergence).
    Returns score (0-50%) and message.
    """
    il_factor = min(il_percentage / 5, 1.0)  # Cap IL contribution at 5%
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)  # Cap TVL decline at 20%
    volatility_score = (il_factor + tvl_factor) * 25  # Scale to 0-50%
    final_score = min(volatility_score, 50)  # Cap at 50%

    if final_score <= 25:
        message = f"✅ Volatility Score: Low ({final_score:.0f}%). Stable conditions with low IL and TVL decline."
    else:
        message = f"⚠️ Volatility Score: Moderate ({final_score:.0f}%). Moderate IL or TVL decline may impact returns."
    
    return final_score, message

def calculate_protocol_risk_score(apy: float, tvl_decline: float, current_tvl: float, trust_score: int) -> tuple[float, str, str]:
    # Base risk score based on APY, TVL decline, and pool size
    base_score = 0
    
    # APY contribution
    if apy < 10:
        base_score += 40
    elif apy <= 15:
        base_score += 20
    
    # TVL decline contribution
    if tvl_decline > 50:
        base_score += 40
    elif tvl_decline > 30:
        base_score += 30
    elif tvl_decline > 15:
        base_score += 15
    
    # Pool size contribution
    if current_tvl < 50000:
        base_score += 40
    elif current_tvl <= 200000:
        base_score += 20
    
    # Cap base score at 100
    base_score = min(base_score, 100)
    
    # Adjust base score with Trust Score multiplier
    if trust_score == 1:  # Unknown
        adjusted_score = base_score * 1.5
    elif trust_score == 2:  # Poor
        adjusted_score = base_score * 1.25
    elif trust_score == 3:  # Moderate
        adjusted_score = base_score * 0.9
    elif trust_score == 4:  # Good
        adjusted_score = base_score * 0.75
    else:  # Excellent (5)
        adjusted_score = base_score * 0.5
    
    # Cap adjusted score at 100
    adjusted_score = min(adjusted_score, 100)
    
    # Determine risk factors for the message
    risk_factors = []
    if apy < 10:
        risk_factors.append("low yield")
    elif apy <= 15:
        risk_factors.append("moderate yield")
    if tvl_decline > 50:
        risk_factors.append("major TVL decline")
    elif tvl_decline > 30:
        risk_factors.append("significant TVL decline")
    elif tvl_decline > 15:
        risk_factors.append("moderate TVL decline")
    if current_tvl < 50000:
        risk_factors.append("tiny pool size")
    elif current_tvl <= 200000:
        risk_factors.append("small pool size")
    
    # Determine risk category with enhanced Trust Score influence
    category = None
    if adjusted_score > 75:
        category = "Critical"
    elif adjusted_score > 50:
        category = "High"
    elif trust_score in [1, 2]:  # Trust Score 1 or 2 triggers Advisory as minimum
        category = "Advisory"
    elif adjusted_score > 25:
        category = "Advisory"
    else:
        category = "Low"
    
    # Override to Low for Trust Score 3, 4, or 5 with minimal risks
    if category == "Advisory" and trust_score >= 3 and adjusted_score <= 50 and tvl_decline <= 15 and current_tvl > 200000:
        category = "Low"

    # Construct the message based on category and risk factors
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
    else:  # Critical
        risk_message = " and ".join(risk_factors)
        message = f"⚠️ Protocol Risk: Critical ({adjusted_score:.0f}%). High risk of protocol failure due to {risk_message}"
        if trust_score in [1, 2]:
            message += " and low trust score"
        message += "."
    
    return adjusted_score, message, category

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
    
    future_pool_value_no_apy, _ = calculate_future_value(initial_investment, 0.0, months, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    
    total_loss_percentage = ((initial_investment - future_pool_value_no_apy) / initial_investment) * 100 if initial_investment > 0 else 0
    apy_exit_threshold = max(0, total_loss_percentage * 12 / months if months > 0 else 0)
    
    apy_exit_threshold = max(apy_exit_threshold, risk_free_rate)
    if il > 50 or future_il > 50:
        apy_exit_threshold = max(apy_exit_threshold, risk_free_rate + 5.0)
    
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    pool_share = (initial_investment / current_tvl) * 100 if current_tvl > 0 else 0

    # Margin of Safety Calculation (APY only)
    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)

    # Volatility Score (adjusted to use IL and TVL decline instead of price divergence)
    volatility_score, volatility_message = calculate_volatility_score(il, tvl_decline)

    # Protocol Risk
    protocol_risk_score, protocol_risk_message, protocol_risk_category = calculate_protocol_risk_score(apy, tvl_decline, current_tvl, trust_score)

    # Streamlit Output with Improved Formatting
    # Core Metrics
    st.markdown("<h1>Core Metrics</h1>", unsafe_allow_html=True)
    if initial_tvl <= 0:
        if is_new_pool:
            st.write(f"**Initial Impermanent Loss:** 0.00% (new pool, IL starts at 0)  ")
            st.write(f"**Projected Impermanent Loss (after {months} months):** {future_il:.2f}% (based on expected price changes)  ")
        else:
            st.write(f"**Impermanent Loss (at current time):** {il:.2f}%  ")
        st.write(f"**Months to Breakeven Against IL:** {break_even_months} months  ")
        st.write(f"**Months to Breakeven Including Expected Price Changes:** {break_even_months_with_price} months  ")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)  ")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (based on your risk-free rate; increased by 5% under high IL conditions)  ")
        st.write(f"**TVL Decline:** Cannot calculate without a valid Initial TVL. Set Initial TVL to Current TVL for new pool entry.  ")
    else:
        if is_new_pool:
            st.write(f"**Initial Impermanent Loss:** 0.00% (new pool, IL starts at 0)  ")
            st.write(f"**Projected Impermanent Loss (after {months} months):** {future_il:.2f}% (based on expected price changes)  ")
        else:
            st.write(f"**Impermanent Loss (at current time):** {il:.2f}%  ")
        st.write(f"**Months to Breakeven Against IL:** {break_even_months} months  ")
        st.write(f"**Months to Breakeven Including Expected Price Changes:** {break_even_months_with_price} months  ")
        st.write(f"**Net Return:** {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)  ")
        st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}% (based on your risk-free rate; increased by 5% under high IL conditions)  ")
        st.write(f"**TVL Decline:** {tvl_decline:.2f}%  ")
    st.write(f"**Pool Share:** {pool_share:.2f}%  ")

    # Separator
    st.markdown("---")

    # Margin of Safety
    st.markdown("<h1>Margin of Safety</h1>", unsafe_allow_html=True)
    st.write(f"**APY Margin of Safety:** {apy_mos:.2f}% (APY can decrease by this percentage before breakeven exceeds 12 months)  ")
    mos_assessment = "✅ High" if apy_mos > 50 else "⚠️ Low"
    st.write(f"**Margin of Safety Assessment:** {mos_assessment} Margin of Safety  ")

    # Separator
    st.markdown("---")

    # Risk Management
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

    # Separator
    st.markdown("---")

    # Investment Risk Alert
    st.markdown("<h1>Investment Risk Alert</h1>", unsafe_allow_html=True)
    if initial_tvl > 0:
        if net_return < 1.0 or tvl_decline >= 50 or protocol_risk_score >= 75:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x, TVL Decline {tvl_decline:.2f}%, Protocol Risk {protocol_risk_score:.0f}% indicate severe risks.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, None, None, None
        elif apy < apy_exit_threshold or net_return < 1.1 or volatility_score > 25:
            reasons = []
            if apy < apy_exit_threshold:
                reasons.append(f"APY below threshold ({apy_exit_threshold:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            if volatility_score > 25:
                reasons.append(f"moderate volatility ({volatility_score:.0f}%)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, None, None, None
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability with low risk.")
    else:
        if net_return < 1.0:
            st.error(f"⚠️ **Investment Risk:** Critical. Net Return {net_return:.2f}x indicates a loss.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, None, None, None
        elif apy < apy_exit_threshold or net_return < 1.1:
            reasons = []
            if apy < apy_exit_threshold:
                reasons.append(f"APY below threshold ({apy_exit_threshold:.2f}%)")
            if net_return < 1.1:
                reasons.append(f"marginal profit (Net Return {net_return:.2f}x)")
            reason_str = ", ".join(reasons)
            st.warning(f"⚠️ **Investment Risk:** Moderate. {reason_str} indicate potential underperformance.")
            return 0, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, None, None, None
        else:
            st.success(f"✅ **Investment Risk:** Low. Net Return {net_return:.2f}x indicates profitability.")

    # Separator
    st.markdown("---")

    # Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes
    st.subheader("Projected Pool Value Based on Yield, Impermanent Loss, and Price Changes")
    st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${initial_investment:,.2f}).")
    time_periods = [0, 3, 6, 12]
    future_values = []
    future_ils = []
    for months in time_periods:
        value, il_at_time = calculate_future_value(initial_investment, apy, months, initial_price_asset1, initial_price_asset2,
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
    
    plt.figure(figsize=(10, 5))
    plt.plot(time_periods, future_values, marker='o', label="Pool Value")
    plt.axhline(y=initial_investment, color='r', linestyle='--', label="Initial Investment")
    plt.title("Projected Pool Value Over Time")
    plt.xlabel("Months")
    plt.ylabel("Value ($)")
    plt.legend()
    st.pyplot(plt)

    # Separator
    st.markdown("---")

    # Simplified Monte Carlo Scenarios
    st.markdown("<h1>Simplified Monte Carlo Scenarios</h1>", unsafe_allow_html=True)
    st.markdown("""
    *This section provides a simplified Monte Carlo analysis by evaluating three scenarios—best case, most probable, and worst case—to estimate the range of outcomes for your pool investment over 12 months. We adjust APY (±50%), asset price changes (±50% for worst case, +10% for best case), and TVL decline (±30% for best case, 50% for worst case) to reflect optimistic, expected, and pessimistic conditions. The "Most Probable" scenario is adjusted to be 15% more conservative than your 12-month projection above to account for potential underperformance in APY due to market conditions.*
    """)

    # Define the scenarios
    # First, calculate the target net return for the "Most Probable" scenario (15% more conservative)
    target_most_probable_net_return = net_return * (1 - 0.15)  # 15% more conservative than the 12-month net return
    # Approximate the APY needed to achieve this net return
    # Since net return is roughly linear with APY (for small changes, ignoring IL and price effects), reduce APY by ~15%
    conservative_apy = apy * (1 - 0.15)
    # Fine-tune the APY to get closer to the target net return
    future_value_test, _ = calculate_future_value(
        initial_investment, conservative_apy, 12, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1,
        expected_price_change_asset2, is_new_pool
    )
    test_net_return = future_value_test / initial_investment if initial_investment > 0 else 0
    # Adjust APY iteratively if needed (simple approximation for now)
    if test_net_return > target_most_probable_net_return:
        conservative_apy *= (target_most_probable_net_return / test_net_return)

    scenarios = {
        "Best Case (Optimistic)": {
            "apy": apy * 1.5,  # +50%
            "price_change_asset1": 10.0,  # +10%
            "price_change_asset2": 10.0,  # +10%
            "tvl_decline": -30.0  # TVL increases by 30%
        },
        "Most Probable (Conservative)": {
            "apy": conservative_apy,  # Adjusted to achieve 15% more conservative net return
            "price_change_asset1": expected_price_change_asset1,
            "price_change_asset2": expected_price_change_asset2,
            "tvl_decline": tvl_decline
        },
        "Worst Case (Pessimistic)": {
            "apy": apy * 0.5,  # -50%
            "price_change_asset1": -50.0,  # -50%
            "price_change_asset2": 50.0,  # +50%
            "tvl_decline": 50.0  # TVL drops by 50%
        }
    }

    # Run calculations for each scenario
    scenario_results = {}
    for scenario_name, params in scenarios.items():
        future_value, future_il = calculate_future_value(
            initial_investment, params["apy"], 12, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, params["price_change_asset1"],
            params["price_change_asset2"], is_new_pool
        )
        scenario_net_return = future_value / initial_investment if initial_investment > 0 else 0
        scenario_results[scenario_name] = {
            "net_return": scenario_net_return,
            "pool_value": future_value,
            "impermanent_loss": future_il
        }

    # Create a DataFrame for the table
    df_scenarios = pd.DataFrame({
        "Metric": ["Net Return", "Pool Value (12 months)", "Impermanent Loss"],
        "Best Case (Optimistic)": [
            f"{scenario_results['Best Case (Optimistic)']['net_return']:.2f}x",
            f"${scenario_results['Best Case (Optimistic)']['pool_value']:.2f}",
            f"{scenario_results['Best Case (Optimistic)']['impermanent_loss']:.2f}%"
        ],
        "Most Probable (Conservative)": [
            f"{scenario_results['Most Probable (Conservative)']['net_return']:.2f}x",
            f"${scenario_results['Most Probable (Conservative)']['pool_value']:.2f}",
            f"{scenario_results['Most Probable (Conservative)']['impermanent_loss']:.2f}%"
        ],
        "Worst Case (Pessimistic)": [
            f"{scenario_results['Worst Case (Pessimistic)']['net_return']:.2f}x",
            f"${scenario_results['Worst Case (Pessimistic)']['pool_value']:.2f}",
            f"{scenario_results['Worst Case (Pessimistic)']['impermanent_loss']:.2f}%"
        ]
    })

    # Display the table
    styled_df_scenarios = df_scenarios.style.set_properties(**{
        'text-align': 'right'
    }, subset=["Best Case (Optimistic)", "Most Probable (Conservative)", "Worst Case (Pessimistic)"]).set_properties(**{
        'text-align': 'left'
    }, subset=["Metric"])
    st.dataframe(styled_df_scenarios, hide_index=True, use_container_width=True)

    # Add a bar chart for net returns
    st.markdown("**Net Return Comparison Across Scenarios**")
    fig, ax = plt.subplots(figsize=(8, 5))
    scenarios_names = list(scenario_results.keys())
    net_returns = [scenario_results[name]["net_return"] for name in scenarios_names]
    bars = ax.bar(scenarios_names, net_returns, color=['#4CAF50', '#2196F3', '#F44336'])
    
    # Add labels on top of the bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.2f}x", ha='center', va='bottom')
    
    ax.set_title("Net Return After 12 Months by Scenario")
    ax.set_ylabel("Net Return (x)")
    ax.set_ylim(0, max(net_returns) + 0.2)
    ax.axhline(y=1.0, color='gray', linestyle='--', label="Break-even (1.0x)")
    ax.legend()
    plt.xticks(rotation=15)
    st.pyplot(fig)

    # Provide insights
    st.markdown("**Key Insights:**")
    best_return = scenario_results['Best Case (Optimistic)']['net_return']
    most_probable_return = scenario_results['Most Probable (Conservative)']['net_return']
    worst_return = scenario_results['Worst Case (Pessimistic)']['net_return']
    best_value = scenario_results['Best Case (Optimistic)']['pool_value']
    most_probable_value = scenario_results['Most Probable (Conservative)']['pool_value']
    worst_value = scenario_results['Worst Case (Pessimistic)']['pool_value']
    best_il = scenario_results['Best Case (Optimistic)']['impermanent_loss']
    worst_il = scenario_results['Worst Case (Pessimistic)']['impermanent_loss']
    
    st.write(f"- **Best Case**: With a higher APY ({scenarios['Best Case (Optimistic)']['apy']:.2f}%), slight asset appreciation (+10% each), and strong TVL growth (+30%), your ${initial_investment:.2f} investment could grow to ${best_value:.2f} ({best_return:.2f}x return) with {best_il:.2f}% impermanent loss.")
    st.write(f"- **Most Probable (Conservative)**: Using a more conservative APY ({scenarios['Most Probable (Conservative)']['apy']:.2f}%), your expected price changes ({expected_price_change_asset1}% and {expected_price_change_asset2}%), and TVL decline ({tvl_decline:.2f}%), your investment is likely to grow to ${most_probable_value:.2f} ({most_probable_return:.2f}x return) with {scenario_results['Most Probable (Conservative)']['impermanent_loss']:.2f}% impermanent loss.")
    st.write(f"- **Worst Case**: If APY drops to {scenarios['Worst Case (Pessimistic)']['apy']:.2f}%, assets diverge significantly (-50% and +50%), and TVL drops by 50%, your investment could fall to ${worst_value:.2f} ({worst_return:.2f}x return) with {worst_il:.2f}% impermanent loss.")

    # Recommendation
    worst_case_loss = (1 - worst_return) * 100 if worst_return < 1 else 0
    best_case_gain = (best_return - 1) * 100 if best_return > 1 else 0
    st.write(f"**Recommendation**: The most probable scenario (conservative) suggests a {((most_probable_return - 1) * 100 if most_probable_return > 1 else (1 - most_probable_return) * 100):.2f}% {'profit' if most_probable_return > 1 else 'loss'}, compared to your projected {((net_return - 1) * 100 if net_return > 1 else (1 - net_return) * 100):.2f}% {'profit' if net_return > 1 else 'loss'} at 12 months. The worst case indicates a potential {worst_case_loss:.2f}% loss. Consider whether the potential upside ({best_case_gain:.2f}% gain in the best case) justifies the risk, or explore pools with more stable assets or higher APY to mitigate downside risk.")

    # Separator
    st.markdown("---")

    # Return future_values, scenarios, and scenario_results along with other metrics
    return break_even_months, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, future_values, scenarios, scenario_results

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
st.sidebar.markdown("**Note:** **Annual Percentage Yield** For conservative projections, consider halving the entered APY to buffer against market volatility. **Global Average Inflation Hurdle Rate: 5%** (as of 2025 IMF data). This is the minimum return needed to outpace global inflation. Compare this to your pool APY to ensure real returns.")

trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, step=1, value=1)
st.sidebar.markdown("""
**Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
- 1 = Unknown (default, highest caution)
- 2 = Poor (known but with concerns)
- 3 = Moderate (neutral, some audits)
- 4 = Good (trusted, audited)
- 5 = Excellent (top-tier, e.g., Uniswap, Aave)
""")

investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.01, step=0.01, value=169.00, format="%.2f")
initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", 
                                     min_value=0.01, step=0.01, value=855000.00, format="%.2f")
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.01, step=0.01, value=1000000.00, format="%.2f")

expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")
expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0, format="%.2f")

initial_btc_price = st.sidebar.number_input("Initial BTC Price (leave blank or set to current price if entering pool today) ($)", 
                                           min_value=0.0, step=0.01, value=100.00, format="%.2f")
current_btc_price = st.sidebar.number_input("Current BTC Price ($)", min_value=0.01, step=0.01, value=90.00, format="%.2f")
btc_growth_rate = st.sidebar.number_input("Expected BTC Annual Growth Rate (Next 12 Months) (%)", min_value=0.0, step=0.1, value=100.0, format="%.2f")

risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0, format="%.2f")
st.sidebar.markdown("""
**Note:** The Risk-Free Rate represents the APY you could earn in a low-risk stablecoin pool (e.g., 5-15% depending on market conditions). The APY Exit Threshold uses this as a baseline, increasing by 5% under high IL conditions, ensuring a margin of safety.
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
        break_even_months, net_return, break_even_months_with_price, apy_exit_threshold, pool_share, future_il, protocol_risk_score, volatility_score, apy_mos, future_values, scenarios, scenario_results = result
        
        # Pool vs. BTC Comparison | 12 Months | Compounding on Pool Assets Only
        st.subheader("Pool vs. BTC Comparison | 12 Months | Compounding on Pool Assets Only")
        asset1_change_desc = "appreciation" if expected_price_change_asset1 >= 0 else "depreciation"
        asset2_change_desc = "appreciation" if expected_price_change_asset2 >= 0 else "depreciation"
        asset1_change_text = f"{abs(expected_price_change_asset1):.1f}% {asset1_change_desc}" if expected_price_change_asset1 != 0 else "no change"
        asset2_change_text = f"{abs(expected_price_change_asset2):.1f}% {asset2_change_desc}" if expected_price_change_asset2 != 0 else "no change"
        st.write(f"**Note:** Pool Value is based on an expected {asset1_change_text} for Asset 1, {asset2_change_text} for Asset 2, and a compounded APY of {apy:.1f}% over 12 months. This comparison assumes a {btc_growth_rate:.1f}% annual growth rate for BTC and no additional fees or slippage.")
        
        projected_btc_price = initial_btc_price * (1 + btc_growth_rate / 100) if initial_btc_price > 0 else current_btc_price * (1 + btc_growth_rate / 100)
        
        if initial_btc_price == 0.0 or initial_btc_price == current_btc_price:
            initial_btc_amount = investment_amount / current_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        else:
            initial_btc_amount = investment_amount / initial_btc_price
            btc_value_12_months = initial_btc_amount * projected_btc_price
        
        pool_value_12_months = future_values[-1] if future_values else 0
        difference = pool_value_12_months - btc_value_12_months
        pool_return_pct = (pool_value_12_months / investment_amount - 1) * 100 if investment_amount > 0 else 0
        btc_return_pct = (btc_value_12_months / investment_amount - 1) * 100 if investment_amount > 0 else 0
        
        formatted_pool_value_12 = f"{int(pool_value_12_months):,}"
        formatted_btc_value_12 = f"{int(btc_value_12_months):,}"
        formatted_difference = f"{int(difference):,}" if difference >= 0 else f"({int(abs(difference)):,})"
        formatted_pool_return = f"{pool_return_pct:.2f}%"
        formatted_btc_return = f"{btc_return_pct:.2f}%"
        
        df_btc_comparison = pd.DataFrame({
            "Metric": ["Projected Pool Value", "Value if Invested in BTC Only", "Difference (Pool - BTC)", "Pool Return (%)", "BTC Return (%)"],
            "Value": [formatted_pool_value_12, formatted_btc_value_12, formatted_difference, formatted_pool_return, formatted_btc_return]
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
        pool_mdd_values_projected = [pool_value_12_months * (1 - mdd / 100) for mdd in mdd_scenarios]
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
        
        # Update CSV Export to include Simplified Monte Carlo Scenarios
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
        writer.writerow(["APY Exit Threshold (%)", f"{apy_exit_threshold:.2f}"])
        writer.writerow(["TVL Decline (%)", f"{tvl_decline:.2f}" if initial_tvl > 0 else "N/A"])
        writer.writerow(["Pool Share (%)", f"{pool_share:.2f}"])
        writer.writerow(["APY Margin of Safety (%)", f"{apy_mos:.2f}"])
        writer.writerow(["Volatility Score (%)", f"{volatility_score:.0f}"])
        writer.writerow(["Protocol Risk Score (%)", f"{protocol_risk_score:.0f}"])
        
        # Add Simplified Monte Carlo Scenarios to CSV with safety check
        writer.writerow([])  # Separator
        writer.writerow(["Simplified Monte Carlo Scenarios", "", ""])
        writer.writerow(["Scenario", "Net Return (x)", "Pool Value (12 months) ($)", "Impermanent Loss (%)"])
        if scenarios and scenario_results:  # Safety check to avoid errors if None
            for scenario_name in scenarios:
                writer.writerow([
                    scenario_name,
                    f"{scenario_results[scenario_name]['net_return']:.2f}",
                    f"{scenario_results[scenario_name]['pool_value']:.2f}",
                    f"{scenario_results[scenario_name]['impermanent_loss']:.2f}"
                ])
        else:
            writer.writerow(["No scenario data available", "", "", ""])
        
        st.download_button(label="Export Results as CSV", data=output.getvalue(), file_name="pool_analysis_results.csv", mime="text/csv")
