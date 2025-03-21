import streamlit as st
import math
import pandas as pd

# Helper Functions
def calculate_pool_value(initial_investment: float, initial_price_asset1: float, initial_price_asset2: float,
                         current_price_asset1: float, current_price_asset2: float) -> tuple[float, float]:
    pool_value = initial_investment * math.sqrt((current_price_asset1 * current_price_asset2) / (initial_price_asset1 * initial_price_asset2))
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
    
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    
    return pool_value, il_percentage

def calculate_future_value(initial_investment: float, apy: float, months: int,
                           initial_price_asset1: float, initial_price_asset2: float,
                           current_price_asset1: float, current_price_asset2: float,
                           expected_price_change_asset1: float, expected_price_change_asset2: float,
                           is_new_pool: bool) -> tuple[float, float]:
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                         current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    
    monthly_apy = (apy / 100) / 12
    apy_compounded_value = pool_value * (1 + monthly_apy) ** months
    
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    
    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    
    new_pool_value = initial_investment * math.sqrt((final_price_asset1 * final_price_asset2) / (initial_price_asset1 * initial_price_asset2))
    
    initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
    initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
    value_if_held = (initial_amount_asset1 * final_price_asset1) + (initial_amount_asset2 * final_price_asset2)
    
    future_value = apy_compounded_value + (new_pool_value - pool_value)
    il = (value_if_held - new_pool_value) / value_if_held if value_if_held > 0 else 0
    il_percentage = abs(il) * 100
    
    return future_value, il_percentage

def calculate_break_even_months(apy: float, il: float, pool_value: float, value_if_held: float) -> float:
    if il <= 0 or pool_value >= value_if_held:
        return 0
    monthly_apy = (apy / 100) / 12
    il_amount = value_if_held - pool_value
    if monthly_apy <= 0:
        return float('inf')
    months = 0
    current_value = pool_value
    while current_value < value_if_held and months < 1200:
        current_value += current_value * monthly_apy
        months += 1
    return months if months < 1200 else float('inf')

def calculate_break_even_months_with_price_changes(initial_investment: float, apy: float, pool_value: float,
                                                   initial_price_asset1: float, initial_price_asset2: float,
                                                   current_price_asset1: float, current_price_asset2: float,
                                                   expected_price_change_asset1: float, expected_price_change_asset2: float,
                                                   value_if_held: float, is_new_pool: bool) -> float:
    monthly_apy = (apy / 100) / 12
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    
    months = 0
    current_pool_value = pool_value
    current_value_if_held = value_if_held
    
    while current_pool_value < current_value_if_held and months < 1200:
        current_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1)
        current_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2)
        new_pool_value = initial_investment * math.sqrt((current_price_asset1 * current_price_asset2) / (initial_price_asset1 * initial_price_asset2))
        current_pool_value = (current_pool_value * (1 + monthly_apy)) + (new_pool_value - current_pool_value)
        
        initial_amount_asset1 = initial_investment / 2 / initial_price_asset1
        initial_amount_asset2 = initial_investment / 2 / initial_price_asset2
        current_value_if_held = (initial_amount_asset1 * current_price_asset1) + (initial_amount_asset2 * current_price_asset2)
        
        months += 1
    
    return months if months < 1200 else float('inf')

def calculate_tvl_decline(initial_tvl: float, current_tvl: float) -> float:
    if initial_tvl <= 0:
        return 0.0
    tvl_change = (current_tvl - initial_tvl) / initial_tvl * 100
    return tvl_change

def calculate_apy_margin_of_safety(pool_value: float, value_if_held: float, apy: float) -> float:
    if value_if_held <= 0:
        return 0.0
    il = (value_if_held - pool_value) / value_if_held if value_if_held > 0 else 0
    apy_mos = apy / (il * 100) if il > 0 else float('inf')
    return apy_mos

def calculate_volatility_score(il: float, tvl_decline: float) -> tuple[int, str]:
    score = 0
    message = ""
    
    if il > 5:
        score += 2
        message += "High impermanent loss indicates significant price volatility. "
    elif il > 0:
        score += 1
        message += "Moderate impermanent loss suggests some price volatility. "
    
    if tvl_decline < -50:
        score += 2
        message += "Significant TVL decline indicates high liquidity risk. "
    elif tvl_decline < -15:
        score += 1
        message += "Moderate TVL decline suggests liquidity concerns. "
    
    if not message:
        message = "Low volatility and stable TVL—good conditions for holding."
    
    return min(score, 5), message

def calculate_protocol_risk_score(apy: float, tvl_decline: float, current_tvl: float, trust_score: int) -> tuple[int, str, str]:
    score = trust_score
    message = ""
    category = ""
    
    if apy > 100:
        score += 2
        message += "Extremely high APY suggests potential for unsustainable returns. "
    elif apy > 50:
        score += 1
        message += "High APY may indicate elevated risk. "
    
    if tvl_decline < -50:
        score += 2
        message += "Significant TVL decline signals high protocol risk. "
    elif tvl_decline < -15:
        score += 1
        message += "Moderate TVL decline indicates some protocol risk. "
    
    if current_tvl < 100000:
        score += 2
        message += "Low TVL increases risk of manipulation. "
    elif current_tvl < 1000000:
        score += 1
        message += "Moderate TVL suggests some risk of manipulation. "
    
    score = min(score, 5)
    
    if score == 1:
        category = "Low Risk"
        message += "Protocol appears low risk—monitor for changes."
    elif score == 2:
        category = "Moderate Risk"
        message += "Protocol has moderate risk—proceed with caution."
    elif score == 3:
        category = "Elevated Risk"
        message += "Protocol shows elevated risk—review security and stability."
    elif score == 4:
        category = "High Risk"
        message += "Protocol is high risk—consider exiting unless confident in its stability."
    else:
        category = "Very High Risk"
        message += "Protocol is very high risk—strongly consider exiting."
    
    return score, message, category

def get_value_color(metric_name: str, value: float, hurdle_rate: float = 16.0) -> str:
    if metric_name in ["Impermanent Loss", "Projected Impermanent Loss"]:
        return "red" if value > 0 else "green"
    elif metric_name == "TVL Decline":
        return "red"
    elif metric_name == "TVL Growth":
        return "green" if value >= 0 else "red"
    elif metric_name == "Net Return":
        return "green" if value > 1 else "red"
    elif metric_name in ["Months to Breakeven Against IL", "Months to Breakeven Including Expected Price Changes"]:
        return "green" if value <= 12 else "red"
    elif metric_name == "Pool Share":
        return "green" if value < 5 else "red"
    elif metric_name == "ARIL":
        target_aril = hurdle_rate * 2
        if value < 0:
            return "red"
        elif value >= target_aril:
            return "green"
        elif value >= hurdle_rate:
            return "yellow"
        else:
            return "red"
    return "neutral"

# Main Analysis Function
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
    aril = ((future_value / initial_investment) - 1) * 100
    
    # Simplified Hurdle Rate: Risk-Free Rate + 6% global inflation
    hurdle_rate = risk_free_rate + 6.0
    target_aril = hurdle_rate * 2
    
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

    # Custom CSS for metric cards
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1f2a44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
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
    .metric-value.yellow {
        color: #ffeb3b;
    }
    .metric-value.neutral {
        color: #ffffff;
    }
    .metric-note {
        font-size: 12px;
        color: #b0b0b0;
        margin-top: 5px;
        flex: 1;
        white-space: normal;
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True)

    # Split into two columns
    col1, col2 = st.columns(2)

    # Metrics for Column 1
    with col1:
        # Impermanent Loss (at current time) with Actionable Note
        if initial_tvl <= 0:
            if is_new_pool:
                il_note = "Your pool has no impermanent loss as it’s a new pool. Monitor price changes to manage future IL."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00, hurdle_rate)}">0.00%</div>
                    <div class="metric-note">{il_note}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il, hurdle_rate)}">{future_il:.2f}%</div>
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
                    <div class="metric-value {get_value_color('Impermanent Loss', il, hurdle_rate)}">{il:.2f}%</div>
                    <div class="metric-note">{il_note}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if is_new_pool:
                il_note = "Your pool has no impermanent loss as it’s a new pool. Monitor price changes to manage future IL."
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📉 Initial Impermanent Loss</div>
                    <div class="metric-value {get_value_color('Impermanent Loss', 0.00, hurdle_rate)}">0.00%</div>
                    <div class="metric-note">{il_note}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔮 Projected Impermanent Loss (after {months} months)</div>
                    <div class="metric-value {get_value_color('Projected Impermanent Loss', future_il, hurdle_rate)}">{future_il:.2f}%</div>
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
                    <div class="metric-value {get_value_color('Impermanent Loss', il, hurdle_rate)}">{il:.2f}%</div>
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
            <div class="metric-value {get_value_color('Months to Breakeven Against IL', break_even_months, hurdle_rate)}">{break_even_months} months</div>
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
            <div class="metric-value {get_value_color('Months to Breakeven Including Expected Price Changes', break_even_months_with_price, hurdle_rate)}">{break_even_months_with_price} months</div>
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
                <div class="metric-value {get_value_color(metric_name, display_value, hurdle_rate)}">{display_value:.2f}%</div>
                <div class="metric-note">{tvl_note}</div>
            </div>
            """, unsafe_allow_html=True)

    # Metrics for Column 2
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
            <div class="metric-value {get_value_color('Net Return', net_return, hurdle_rate)}">{net_return:.2f}x</div>
            <div class="metric-note">{net_return_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Hurdle Rate with Actionable Note
        hurdle_rate_note = f"Your Hurdle Rate is {hurdle_rate:.1f}% ({risk_free_rate:.1f}% risk-free rate + 6% inflation). To justify risk, your ARIL should exceed this and ideally reach {target_aril:.1f}% (2× Hurdle Rate). Compare with your ARIL to assess performance."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Hurdle Rate</div>
            <div class="metric-value {get_value_color('Hurdle Rate', hurdle_rate, hurdle_rate)}">{hurdle_rate:.2f}%</div>
            <div class="metric-note">{hurdle_rate_note}</div>
        </div>
        """, unsafe_allow_html=True)

        # Annualized Return After IL (ARIL) with Actionable Note
        if aril < 0:
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, below the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates a loss. Consider reallocating to a stablecoin pool yielding {risk_free_rate:.1f}% or reassessing price change expectations to reduce impermanent loss."
        elif 0 <= aril < hurdle_rate:
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, below the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates underperformance. Consider reallocating to a stablecoin pool yielding {risk_free_rate:.1f}% or adjusting your strategy to improve returns."
        elif hurdle_rate <= aril < target_aril:
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, above the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) but below the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. Returns are marginal for the risk taken. Evaluate if this aligns with your investment goals."
        else:
            aril_note = f"Your pool’s effective return (ARIL) is {aril:.1f}%, exceeding the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation) and the target of {target_aril:.1f}% (2× Hurdle Rate) to justify risk. This indicates strong profitability. Continue monitoring price changes to sustain this performance."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Annualized Return After IL (ARIL)</div>
            <div class="metric-value {get_value_color('ARIL', aril, hurdle_rate)}">{aril:.1f}%</div>
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
            <div class="metric-value {get_value_color('Pool Share', pool_share, hurdle_rate)}">{pool_share:.2f}%</div>
            <div class="metric-note">{pool_share_note}</div>
        </div>
        """, unsafe_allow_html=True)

    # Risk Management Section
    st.markdown("<h1 style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>Risk Management</h1>", unsafe_allow_html=True)

    if aril >= target_aril:  # Strong Performance
        st.success(f"✅ **ARIL Assessment:** Your ARIL of {aril:.1f}% exceeds the target of {target_aril:.1f}% (2× Hurdle Rate), indicating strong risk-adjusted returns. Monitor price changes to maintain profitability.")
    elif hurdle_rate <= aril < target_aril:  # Marginal Performance
        st.warning(f"⚠️ **ARIL Assessment:** Your ARIL of {aril:.1f}% is above the Hurdle Rate of {hurdle_rate:.1f}% but below the target of {target_aril:.1f}% (2× Hurdle Rate). Returns are marginal for the risk taken. Consider adjusting your strategy or exiting if better opportunities arise.")
    else:  # Poor Performance
        st.error(f"❌ **ARIL Assessment:** Your ARIL of {aril:.1f}% is below the Hurdle Rate of {hurdle_rate:.1f}% (risk-free rate + 6% inflation), indicating poor performance. Consider exiting the pool and reallocating to a stablecoin pool yielding {risk_free_rate:.1f}%.")

    st.markdown(f"**Volatility Score (1-5):** {volatility_score} - {volatility_message}")
    st.markdown(f"**Protocol Risk Score (1-5):** {protocol_risk_score} ({protocol_risk_category}) - {protocol_risk_message}")

    # Projected Pool Value Over Time
    st.markdown("<h1 style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>Projected Pool Value Over Time</h1>", unsafe_allow_html=True)
    
    investment_amount = initial_investment
    data = []
    intervals = [0, 3, 6, 12]
    
    for month in intervals:
        future_value, future_il = calculate_future_value(initial_investment, apy, month, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
        data.append({
            "Time Period (Months)": month,
            "Projected Value ($)": future_value,
            "Projected Impermanent Loss (%)": future_il
        })
    
    df = pd.DataFrame(data)
    st.table(df)
    
    st.write(f"**Note:** The initial projected value reflects the current market value of your liquidity position, adjusted for price changes and impermanent loss, not the cash invested (${investment_amount:,.2f}).")

    # Additional Section to Verify Rendering
    st.markdown("<h1 style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>Additional Analysis</h1>", unsafe_allow_html=True)
    st.write("This section confirms that content after 'Projected Pool Value Over Time' renders correctly.")
    st.write("Here are some additional insights:")
    st.write("- **Recommendation**: Based on the risk scores, review your position and consider adjusting your strategy.")
    st.write("- **Next Steps**: Monitor price changes and TVL trends over the next few weeks to make an informed decision.")

# Streamlit App
st.title("Liquidity Pool Exit Analyzer")

# Sidebar Inputs
st.sidebar.header("Set Your Pool Parameters")

pool_status = st.sidebar.selectbox("Pool Status", ["New Pool", "Existing Pool"])
is_new_pool = (pool_status == "New Pool")

initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price (at Entry) ($)", min_value=0.0, value=88000.0, step=1000.0)
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price (at Entry) ($)", min_value=0.0, value=1.0, step=0.1)

if not is_new_pool:
    current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price (Today) ($)", min_value=0.0, value=150000.0, step=1000.0)
    current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price (Today) ($)", min_value=0.0, value=1.0, step=0.1)
else:
    current_price_asset1 = initial_price_asset1
    current_price_asset2 = initial_price_asset2

apy = st.sidebar.number_input("Current APY (%)", min_value=0.0, value=1.0, step=0.1)
st.sidebar.markdown("**Note:** Annual Percentage Yield for conservative projections, consider halving the entered APY to buffer against market volatility.")

trust_score = st.sidebar.number_input("Protocol Trust Score (1-5)", min_value=1, max_value=5, value=3, step=1)
st.sidebar.markdown("""
**Note:** Protocol Trust Score reflects your trust in the protocol's reliability:
- **1** = Unknown (default, highest caution)
- **2** = Poor (known but with concerns)
- **3** = Moderate (neutral, some audits)
- **4** = Good (trusted, audited)
- **5** = Excellent (top-tier, e.g., Uniswap, Aave)
""")

investment_amount = st.sidebar.number_input("Initial Investment ($)", min_value=0.0, value=250000.0, step=1000.0)
initial_tvl = st.sidebar.number_input("Initial TVL (set to current Total value Locked if entering today) ($)", min_value=0.0, value=750000.0, step=10000.0)
current_tvl = st.sidebar.number_input("Current TVL ($)", min_value=0.0, value=399999.97, step=10000.0)

# Expected Price Changes
st.sidebar.header("Expected Price Changes (Annual)")
expected_price_change_asset1 = st.sidebar.number_input("Expected Annual Price Change for Asset 1 (%)", value=0.0, step=1.0)
expected_price_change_asset2 = st.sidebar.number_input("Expected Annual Price Change for Asset 2 (%)", value=0.0, step=1.0)

# Risk-Free Rate
risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, step=0.1)
st.sidebar.markdown("**Note:** Typically the yield of a 10-year Treasury note or a stablecoin staking yield (e.g., 4-5% in stable markets).")

# BTC Growth Rate (optional, for future use)
btc_growth_rate = st.sidebar.number_input("Expected Annual BTC Growth Rate (%)", value=0.0, step=1.0)
st.sidebar.markdown("**Note:** Used for benchmarking against BTC performance. Set to 0 to ignore.")

# Calculate Button
st.markdown("<h3 style='text-align: center; margin-top: 20px;'>Run Analysis</h3>", unsafe_allow_html=True)
if st.button("Calculate"):
    # Calculate Impermanent Loss for Existing Pool
    if not is_new_pool:
        _, il = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    else:
        il = 0.0

    # Calculate TVL Decline
    tvl_decline = calculate_tvl_decline(initial_tvl, current_tvl)

    # Run Analysis
    check_exit_conditions(
        initial_investment=investment_amount,
        apy=apy,
        il=il,
        tvl_decline=tvl_decline,
        initial_price_asset1=initial_price_asset1,
        initial_price_asset2=initial_price_asset2,
        current_price_asset1=current_price_asset1,
        current_price_asset2=current_price_asset2,
        current_tvl=current_tvl,
        risk_free_rate=risk_free_rate,
        trust_score=trust_score,
        expected_price_change_asset1=expected_price_change_asset1,
        expected_price_change_asset2=expected_price_change_asset2,
        is_new_pool=is_new_pool,
        btc_growth_rate=btc_growth_rate
    )
else:
    st.write("Please click the 'Calculate' button to run the analysis with the provided inputs.")
