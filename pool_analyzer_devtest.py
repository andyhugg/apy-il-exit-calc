import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Core Calculation Functions
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
    current_value = pool_value
    for month in range(1, months + 1):
        monthly_apy = (apy / 100) / 12 * (0.95 ** (month - 1))  # 5% monthly decay
        current_value *= (1 + monthly_apy)
    final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
    final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
    new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                           final_price_asset1, final_price_asset2)
    future_il = calculate_il(initial_price_asset1, initial_price_asset2, final_price_asset1, final_price_asset2, initial_investment)
    current_value += (new_pool_value - pool_value)
    return round(current_value, 2), future_il

def calculate_break_even_months(apy: float, il: float, initial_pool_value: float, value_if_held: float) -> float:
    if apy <= 0 or initial_pool_value <= 0 or value_if_held <= initial_pool_value:
        return 0
    current_value = initial_pool_value
    months = 0
    while current_value < value_if_held and months < 1000:
        monthly_apy = (apy / 100) / 12 * (0.95 ** months)  # 5% monthly decay
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
    monthly_price_change_asset1 = (expected_price_change_asset1 / 100) / 12
    monthly_price_change_asset2 = (expected_price_change_asset2 / 100) / 12
    months = 0
    current_value = pool_value
    while current_value < value_if_held and months < 1000:
        months += 1
        monthly_apy = (apy / 100) / 12 * (0.95 ** (months - 1))  # 5% monthly decay
        final_price_asset1 = current_price_asset1 * (1 + monthly_price_change_asset1 * months)
        final_price_asset2 = current_price_asset2 * (1 + monthly_price_change_asset2 * months)
        new_pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                               final_price_asset1, final_price_asset2)
        current_value = pool_value * (1 + monthly_apy) ** months + (new_pool_value - pool_value)
    return round(months, 2) if months < 1000 else float('inf')

def simplified_monte_carlo_analysis(initial_investment: float, apy: float, initial_price_asset1: float, initial_price_asset2: float,
                                   current_price_asset1: float, current_price_asset2: float, expected_price_change_asset1: float,
                                   expected_price_change_asset2: float, is_new_pool: bool, num_simulations: int = 200) -> dict:
    apy_range = [max(apy * 0.5, 0), apy * 1.5]
    price_change_asset1_range = [expected_price_change_asset1 * 0.5, expected_price_change_asset1 * 1.5] if expected_price_change_asset1 >= 0 else [expected_price_change_asset1 * 1.5, expected_price_change_asset1 * 0.5]
    price_change_asset2_range = [expected_price_change_asset2 * 0.5, expected_price_change_asset2 * 1.5] if expected_price_change_asset2 >= 0 else [expected_price_change_asset2 * 1.5, expected_price_change_asset2 * 0.5]
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
    worst_value, worst_il = sorted(zip(values, ils))[19]  # 10th percentile
    best_value, best_il = sorted(zip(values, ils))[179]   # 90th percentile
    expected_value, expected_il = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                                        current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                        expected_price_change_asset2, is_new_pool)
    return {
        "worst": {"value": worst_value, "il": worst_il},
        "expected": {"value": expected_value, "il": expected_il},
        "best": {"value": best_value, "il": best_il}
    }

def generate_pdf_report(il, net_return, future_value, break_even_months, break_even_months_with_price, 
                        drawdown_initial, drawdown_12_months, current_tvl, platform_trust_score, 
                        hurdle_rate, hurdle_value_12_months, risk_messages):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Liquidity Pool Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Key Insights", styles['Heading2']))
    story.append(Paragraph(f"Current Impermanent Loss: {il:.2f}%", styles['BodyText']))
    story.append(Paragraph(f"12-Month Outlook: ${future_value:,.0f} ({net_return:.2f}x return)", styles['BodyText']))
    story.append(Paragraph(f"Current TVL: ${current_tvl:,.0f}", styles['BodyText']))
    story.append(Paragraph(f"Breakeven Time: Against IL: {break_even_months} months, With Price Changes: {break_even_months_with_price} months", styles['BodyText']))
    story.append(Paragraph(f"Worst-Case Drawdown (90%): Initial: ${drawdown_initial:,.0f}, After 12 Months: ${drawdown_12_months:,.0f}", styles['BodyText']))
    story.append(Paragraph(f"Hurdle Rate: {hurdle_rate:.1f}% (${hurdle_value_12_months:,.0f} after 12 months)", styles['BodyText']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Summary", styles['Heading2']))
    if risk_messages:
        story.append(Paragraph(f"High Risk: {', '.join(risk_messages)}", styles['BodyText']))
    else:
        story.append(Paragraph("Low Risk: Profitable with manageable IL", styles['BodyText']))
    story.append(Paragraph(f"Platform Trust Score: {platform_trust_score} (1-5)", styles['BodyText']))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

# Parse TVL Input Function
def parse_tvl_input(tvl_str: str) -> float:
    try:
        tvl_str = tvl_str.strip().lower()
        if tvl_str.endswith('m'):
            return float(tvl_str[:-1]) * 1_000_000
        elif tvl_str.endswith('k'):
            return float(tvl_str[:-1]) * 1_000
        else:
            return float(tvl_str)
    except ValueError:
        return 1.00  # Default on invalid input

# CSS (Updated for Arrows)
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
        min-height: 80px;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-title {
        font-size: 16px;
        font-weight: bold;
        width: 20%;
        min-width: 120px;
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        width: 20%;
        min-width: 120px;
        white-space: normal;
        word-wrap: break-word;
    }
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 100px;
        line-height: 1.4;
    }
    .tooltip {
        cursor: help;
        color: #FFC107;
        font-size: 14px;
        margin-left: 5px;
        position: relative;
    }
    .tooltip:hover:after {
        content: attr(title);
        position: absolute;
        left: 10px;
        top: calc(100% + 5px);
        background-color: #2A3555;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        z-index: 1000;
        max-width: 300px;
        white-space: normal;
        transition-delay: 0s !important;
        visibility: visible !important;
    }
    .red-text { color: #FF4D4D; }
    .green-text { color: #32CD32; }
    .yellow-text { color: #FFC107; }
    .neutral-text { color: #A9A9A9; }
    .arrow-up { color: #32CD32; font-size: 16px; margin-left: 5px; }
    .arrow-down { color: #FF4D4D; font-size: 16px; margin-left: 5px; }
    .risk-assessment {
        background-color: #1E2A44;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-width: 620px;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .risk-red { border: 2px solid #FF4D4D; }
    .risk-yellow { border: 2px solid #FFC107; }
    .risk-green { border: 2px solid #32CD32; }
    .progress-bar {
        width: 100%;
        background-color: #A9A9A9;
        border-radius: 5px;
        height: 10px;
        margin-top: 10px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 5px;
    }
    .proj-table-container {
        overflow-x: auto;
        max-width: 100%;
    }
    .proj-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(to bottom, #1E2A44, #6A82FB);
    }
    .proj-table th, .proj-table td {
        padding: 12px;
        text-align: center;
        color: #FFFFFF;
        border: 1px solid #2A3555;
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        font-weight: 500;
    }
    .proj-table th {
        background-color: #1E2A44;
        font-weight: bold;
    }
    .proj-table tr:nth-child(even) td { background: rgba(255, 255, 255, 0.05); }
    .proj-table tr:nth-child(odd) td { background: rgba(255, 255, 255, 0.1); }
    .proj-table tr:hover td {
        background: rgba(255, 255, 255, 0.2);
        transition: background 0.3s ease;
    }
    .monte-carlo-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: #2A3555;
    }
    .monte-carlo-table th, .monte-carlo-table td {
        padding: 12px;
        text-align: center;
        color: #FFFFFF;
        border: 1px solid #2A3555;
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        font-weight: 500;
    }
    .monte-carlo-table th {
        background-color: #1E2A44;
        font-weight: bold;
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
        .metric-tile { flex-direction: column; align-items: flex-start; }
        .metric-title, .metric-value, .metric-desc { width: 100%; min-width: 0; }
        .metric-value { font-size: 18px; }
        .metric-desc { max-height: 120px; }
        .proj-table th, .proj-table td { font-size: 12px; padding: 8px; }
        .monte-carlo-table th, .monte-carlo-table td { font-size: 12px; padding: 8px; }
    }
    </style>
""", unsafe_allow_html=True)

# Title and Introduction
st.title("Arta - Master the Risk - CryptoRiskAnalyzer.com")
st.markdown("""
Arta - Indonesian for "wealth" - was the name of my cat and now the name of my app! It's perfect for fast, accurate insights into price projections, potential profits, and crypto asset or liquidity pool risk. You can run scenarios, test your assumptions, and sharpen your edge, all in real time. **Builder - AHU**
""")
st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer</b>: Arta is a tool for educational and informational purposes only. It does not provide financial advice. All projections are hypothetical and not guarantees of future performance. Always do your own research and consult a licensed advisor before making financial decisions.
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
**Looking to Analyze a Crypto Asset?**  
Click the link below to use our Crypto Asset Analyzer tool:  
<a href="https://arta-crypto-risk-analyzer.onrender.com" target="_self">Go to Asset Analyzer</a>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
**Instructions for Analyzing a Liquidity Pool**: Enter the values below to analyze your pool. APY decays at 5% monthly, and BTC growth is fixed at 25% CAGR.
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Configure Your Pool")
    pool_status = st.selectbox("Pool Status", ["Existing Pool", "New Pool"])
    is_new_pool = (pool_status == "New Pool")
    
    if is_new_pool:
        current_price_asset1 = st.number_input("Current Price Asset 1 ($)", min_value=0.01, value=1.00, format="%.2f")
        current_price_asset2 = st.number_input("Current Price Asset 2 ($)", min_value=0.01, value=1.00, format="%.2f")
        initial_price_asset1 = current_price_asset1
        initial_price_asset2 = current_price_asset2
    else:
        initial_price_asset1 = st.number_input("Initial Price Asset 1 ($)", min_value=0.01, value=1.00, format="%.2f")
        initial_price_asset2 = st.number_input("Initial Price Asset 2 ($)", min_value=0.01, value=1.00, format="%.2f")
        current_price_asset1 = st.number_input("Current Price Asset 1 ($)", min_value=0.01, value=1.00, format="%.2f")
        current_price_asset2 = st.number_input("Current Price Asset 2 ($)", min_value=0.01, value=1.00, format="%.2f")
    
    investment_amount = st.number_input("Investment ($)", min_value=0.01, value=1.00, format="%.2f")
    apy = st.number_input("Pool APY (%)", min_value=0.01, value=25.00, format="%.2f")
    fear_and_greed_score = st.number_input("Fear and Greed Score (0-100)", min_value=0, max_value=100, value=50)
    expected_price_change_asset1 = st.number_input("Expected Price Change Asset 1 (%)", min_value=-100.0, value=1.0, format="%.2f")
    expected_price_change_asset2 = st.number_input("Expected Price Change Asset 2 (%)", min_value=-100.0, value=1.0, format="%.2f")
    tvl_input = st.text_input("Current TVL ($)", value="1.00", help="Enter as 18m, 250k, or full number (e.g., 18000000)")
    current_tvl = parse_tvl_input(tvl_input)
    if current_tvl < 0.01:
        current_tvl = 1.00
        st.sidebar.warning("TVL must be at least 0.01. Set to 1.00.")
    
    platform_trust_score = st.selectbox(
        "Platform Trust Score (1-5)",
        options=[
            (1, "1 - Unknown (highest caution)"),
            (2, "2 - Poor (known but with concerns)"),
            (3, "3 - Moderate (neutral, some audits)"),
            (4, "4 - Good (trusted, audited)"),
            (5, "5 - Excellent (top-tier, e.g., Uniswap, Aave)")
        ],
        format_func=lambda x: x[1],
        index=0
    )[0]

    risk_free_rate = st.number_input("Risk-Free Rate (%)", min_value=0.0, value=10.0, format="%.2f")
    st.markdown("**Note**: BTC growth is assumed at a 25% CAGR based on historical trends.")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        # Compute Risk Metrics
        il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, investment_amount)
        pool_value, _ = calculate_pool_value(investment_amount, initial_price_asset1, initial_price_asset2,
                                            current_price_asset1, current_price_asset2) if not is_new_pool else (investment_amount, 0.0)
        value_if_held = (investment_amount / 2 / initial_price_asset1 * current_price_asset1) + (investment_amount / 2 / initial_price_asset2 * current_price_asset2)
        future_value, _ = calculate_future_value(investment_amount, apy, 12, initial_price_asset1, initial_price_asset2,
                                                current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                expected_price_change_asset2, is_new_pool)
        net_return = future_value / investment_amount if investment_amount > 0 else 0
        break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
        break_even_months_with_price = calculate_break_even_months_with_price_changes(
            investment_amount, apy, pool_value, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
        )
        drawdown_initial = investment_amount * 0.1
        drawdown_12_months = future_value * 0.1
        hurdle_rate = risk_free_rate + 6.0
        hurdle_value_12_months = investment_amount * (1 + hurdle_rate / 100)

        # Risk Assessment
        risk_messages = []
        if net_return < 1.0:
            risk_messages.append("Loss projected")
        if il > 5.0:
            risk_messages.append("High IL")
        if current_tvl < 250000:
            risk_messages.append("TVL too low: Pool may be at risk of low liquidity or manipulation")
        if apy < hurdle_rate:
            risk_messages.append(f"APY ({apy:.1f}%) below hurdle rate ({hurdle_rate:.1f}%)")
        if platform_trust_score <= 2:
            risk_messages.append("Low Platform Trust Score: Protocol may be risky")

        # Compute Composite Risk Score
        scores = {
            'IL': 100 if il < 2 else 50 if il < 5 else 0,
            'Net Return': 100 if net_return > 1.5 else 50 if net_return > 1 else 0,
            'TVL': 100 if current_tvl >= 1_000_000 else 50 if current_tvl >= 250_000 else 0,
            'APY vs Hurdle': 100 if apy >= hurdle_rate + 10 else 50 if apy >= hurdle_rate else 0,
            'Platform Trust': 100 if platform_trust_score >= 4 else 50 if platform_trust_score >= 3 else 0,
            'Fear and Greed': 100 - abs(50 - fear_and_greed_score) * 2
        }
        weights = {
            'IL': 1.5,
            'Net Return': 1.2,
            'TVL': 1.0,
            'APY vs Hurdle': 1.0,
            'Platform Trust': 2.5,
            'Fear and Greed': 2.0
        }
        weighted_sum = sum(scores[metric] * weights[metric] for metric in scores)
        total_weight = sum(weights.values())
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Risk Summary Section
        with st.expander("Risk Summary", expanded=True):
            bg_class = "risk-green" if composite_score >= 70 else "risk-yellow" if composite_score >= 40 else "risk-red"
            insight = (
                f"Low risk profile. Profitable with manageable IL." if composite_score >= 70 else
                f"Moderate risk. Check IL, TVL, or APY." if composite_score >= 40 else
                f"High risk. Reassess due to IL, TVL, or platform trust."
            )
            summary = "Low Risk" if composite_score >= 70 else "Moderate Risk" if composite_score >= 40 else "High Risk"
            progress_color = "#32CD32" if composite_score >= 70 else "#FFC107" if composite_score >= 40 else "#FF4D4D"
            st.markdown(f"""
                <div class="risk-assessment {bg_class}">
                    <div style="font-size: 24px; font-weight: bold; color: white;">Composite Risk Score: {composite_score:.1f}/100</div>
                    <div style="font-size: 16px; margin-top: 5px; color: white;">Summary: {summary}</div>
                    <div class="progress-bar"><div class="progress-fill" style="width: {composite_score}%; background-color: {progress_color};"></div></div>
                    <div style="font-size: 16px; margin-top: 10px; color: #A9A9A9;">{insight}</div>
                    <div style="font-size: 14px; margin-top: 5px; color: #A9A9A9; font-style: italic;">Platform Trust Score: {platform_trust_score}/5</div>
                </div>
            """, unsafe_allow_html=True)

        # Key Insights Section
        with st.expander("Key Insights", expanded=False):
            st.markdown("### Pool Performance Metrics")
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Impermanent Loss<span class="tooltip" title="Shows how much you’re losing because the pool’s assets changed in price compared to just holding them. High loss means your earnings might take a hit. What to do: If it’s below 2%, you’re fine—keep going. Between 2-5%, keep an eye on it. Over 5%, think about pulling out to avoid bigger losses.">?</span></div>
                    <div class="metric-value {'red-text' if il > 5 else 'yellow-text' if il > 2 else 'green-text'}">{il:.2f}%</div>
                    <div class="metric-desc">Current loss from price divergence.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">💰 12-Month Value<span class="tooltip" title="Your money’s expected value in a year, based on pool earnings (which drop 5% monthly), price shifts, and losses. The ‘x’ shows how much your investment grows. What to do: Above 1.5x, you’re in great shape—consider locking in gains. At 1-1.5x, hold steady but watch the market. Below 1x, rethink if this pool’s worth it.">?</span></div>
                    <div class="metric-value">${future_value:,.0f}<br>({net_return:.2f}x)</div>
                    <div class="metric-desc">After 12 months includes compounded APY, price changes, and IL.</div>
                </div>
            """, unsafe_allow_html=True)

            tvl_insight = "Below $250k, stick to small moves to avoid price swings." if current_tvl < 250000 else "Trade carefully." if current_tvl < 1_000_000 else "You’re good for bigger trades."
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">💧 TVL<span class="tooltip" title="The total cash locked in the pool—more means it’s safer and easier to trade. Low cash can mean risky trades. What to do: Below $250k, stick to small moves to avoid price swings. $250k-$1M, trade carefully. Above $1M, you’re good for bigger trades.">?</span></div>
                    <div class="metric-value {'red-text' if current_tvl < 250_000 else 'yellow-text' if current_tvl < 1_000_000 else 'green-text'}">${current_tvl:,.0f}</div>
                    <div class="metric-desc">Current total value locked.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### Break-even and Risk Metrics")
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">⏳ Break-even<span class="tooltip" title="Shows how many months until your pool’s earnings cover price losses, if prices stay the same. What to do: Under 6 months, you’re fine—stay in. 6-12 months, check often to avoid delays. Over 12 months, it takes too long—find a better pool.">?</span></div>
                    <div class="metric-value {'red-text' if break_even_months > 12 else 'yellow-text' if break_even_months > 6 else 'green-text'}">{break_even_months} months</div>
                    <div class="metric-desc">Against IL, without price changes.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">⏳ Break-even (Price)<span class="tooltip" title="Tells how many months until earnings cover losses, using your expected price changes. What to do: Under 6 months, it’s good—keep going. 6-12 months, watch prices closely. Over 12 months, it’s risky—look for another pool.">?</span></div>
                    <div class="metric-value {'red-text' if break_even_months_with_price > 12 else 'yellow-text' if break_even_months_with_price > 6 else 'green-text'}">{break_even_months_with_price} months</div>
                    <div class="metric-desc">With expected price changes.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📉 Drawdown<span class="tooltip" title="Shows the largest loss you might face in a bad year. What to do: Under 20% of your investment, don’t worry—stay calm. 20-50%, set a limit to reduce loss. Over 50%, take money out to protect it.">?</span></div>
                    <div class="metric-value {'red-text' if drawdown_12_months > investment_amount * 0.5 else 'yellow-text' if drawdown_12_months > investment_amount * 0.2 else 'green-text'}">${drawdown_12_months:,.0f}</div>
                    <div class="metric-desc">After 12 months (90th percentile).</div>
                </div>
            """, unsafe_allow_html=True)

            # Updated Section: How Does This Compare?
            st.markdown("### How Does This Compare?")
            time_periods = [0, 3, 6, 12]
            future_values = []
            btc_values = []
            for months in time_periods:
                value, _ = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                                 current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                                 expected_price_change_asset2, is_new_pool)
                future_values.append(value)
                btc_value = investment_amount * (1 + 0.25) ** (months / 12)  # 25% CAGR
                btc_values.append(btc_value)

            # Calculate returns for comparisons
            pool_return = net_return  # Already calculated as future_value / investment_amount
            btc_return = 1.25  # 25% CAGR over 12 months
            stablecoin_return = 1 + (risk_free_rate / 100)  # 12-month stablecoin growth

            # Determine arrow directions
            pool_vs_hurdle = apy >= hurdle_rate
            pool_vs_btc = pool_return >= btc_return
            pool_vs_stablecoin = pool_return >= stablecoin_return

            # Combined tooltip
            tooltip_text = (
                f"Your pool’s growth ({pool_return:.2f}x) is better than BTC ({btc_return:.2f}x) and stablecoins ({stablecoin_return:.2f}x). "
                f"It also beats the safe earning target. Stay in the pool. "
                f"If the platform trust is low or price losses are high, add some stablecoins or switch to BTC for less risk."
            )

            # Display comparisons with arrows
            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📈 Pool vs Safe Target<span class="tooltip" title="{tooltip_text}">?</span></div>
                    <div class="metric-value">{apy:.1f}% vs {hurdle_rate:.1f}% <span class="{'arrow-up' if pool_vs_hurdle else 'arrow-down'}">{'▲' if pool_vs_hurdle else '▼'}</span></div>
                    <div class="metric-desc">Earnings compared to safe target (risk-free rate + 6% inflation).</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📈 Pool vs BTC<span class="tooltip" title="{tooltip_text}">?</span></div>
                    <div class="metric-value">{pool_return:.2f}x vs {btc_return:.2f}x <span class="{'arrow-up' if pool_vs_btc else 'arrow-down'}">{'▲' if pool_vs_btc else '▼'}</span></div>
                    <div class="metric-desc">12-month growth compared to BTC (25% CAGR).</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-title">📈 Pool vs Stablecoin<span class="tooltip" title="{tooltip_text}">?</span></div>
                    <div class="metric-value">{pool_return:.2f}x vs {stablecoin_return:.2f}x <span class="{'arrow-up' if pool_vs_stablecoin else 'arrow-down'}">{'▲' if pool_vs_stablecoin else '▼'}</span></div>
                    <div class="metric-desc">12-month growth compared to stablecoin ({risk_free_rate:.1f}%).</div>
                </div>
            """, unsafe_allow_html=True)

        # Projected Pool Value Over Time
        with st.expander("Projected Pool Value Over Time", expanded=False):
            st.markdown("**Note**: Projected values reflect growth of your initial investment over 12 months, compared with BTC (25% CAGR) and Stablecoin pools. It considers impermanent loss, APY (with 5% monthly decay), asset price changes, and market volatility via the Fear and Greed Score.")
            stablecoin_values = []
            for months in time_periods:
                stablecoin_value = investment_amount * (1 + (risk_free_rate / 100) * (months / 12))
                stablecoin_values.append(stablecoin_value)
            
            hurdle_values = [investment_amount * (1 + hurdle_rate / 100 * (months / 12)) for months in time_periods]

            proj_data = {
                "Metric": ["Pool Value ($)", "BTC Value ($)", "Stablecoin Value ($)", "Hurdle Value ($)"],
                "Month 0": [future_values[0], btc_values[0], stablecoin_values[0], hurdle_values[0]],
                "Month 3": [future_values[1], btc_values[1], stablecoin_values[1], hurdle_values[1]],
                "Month 6": [future_values[2], btc_values[2], stablecoin_values[2], hurdle_values[2]],
                "Month 12": [future_values[3], btc_values[3], stablecoin_values[3], hurdle_values[3]]
            }
            proj_df = pd.DataFrame(proj_data)

            styled_proj_df = proj_df.style.set_table_attributes('class="proj-table"').format({
                "Month 0": lambda x: "${:,.2f}".format(x),
                "Month 3": lambda x: "${:,.2f}".format(x),
                "Month 6": lambda x: "${:,.2f}".format(x),
                "Month 12": lambda x: "${:,.2f}".format(x)
            })
            
            st.markdown('<div class="proj-table-container">', unsafe_allow_html=True)
            st.table(styled_proj_df)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.spinner("Generating chart..."):
                plt.figure(figsize=(10, 6))
                sns.set_style("whitegrid")
                sns.lineplot(x=time_periods, y=future_values, label='Pool Value', color='#4B5EAA', linewidth=2.5, marker='o')
                sns.lineplot(x=time_periods, y=btc_values, label='BTC Value', color='#FFC107', linewidth=2.5, marker='o')
                sns.lineplot(x=time_periods, y=stablecoin_values, label=f'Stablecoin Value ({risk_free_rate:.1f}%)', color='#A9A9A9', linewidth=2.5, marker='o')
                sns.lineplot(x=time_periods, y=hurdle_values, label=f'Hurdle Rate ({hurdle_rate:.1f}%)', color='#32CD32', linewidth=2.5, marker='o')
                plt.axhline(y=investment_amount, color='#FF4D4D', linestyle='--', label=f'Initial Investment (${investment_amount:,.2f})')
                plt.fill_between(time_periods, investment_amount, future_values, where=(np.array(future_values) < investment_amount), color='#FF4D4D', alpha=0.1, label='Loss Zone')
                plt.title('Projected Value Over 12 Months (Pool vs BTC vs Stablecoin)')
                plt.xlabel('Months')
                plt.ylabel('Value ($)')
                plt.legend()
                st.pyplot(plt)
                plt.clf()

        # Monte Carlo Scenarios
        with st.expander("Monte Carlo Scenarios - 12 Months", expanded=False):
            st.markdown("Simulates 200 scenarios over 12 months considering APY and price change volatility.")
            st.markdown("- **Expected**: Average | **Best**: 90th percentile | **Worst**: 10th percentile")
            mc_results = simplified_monte_carlo_analysis(
                investment_amount, apy, initial_price_asset1, initial_price_asset2,
                current_price_asset1, current_price_asset2, expected_price_change_asset1,
                expected_price_change_asset2, is_new_pool
            )
            df_monte_carlo = pd.DataFrame({
                "Scenario": ["Worst Case", "Expected Case", "Best Case"],
                "Value ($)": [mc_results['worst']['value'], mc_results['expected']['value'], mc_results['best']['value']],
                "IL (%)": [mc_results['worst']['il'], mc_results['expected']['il'], mc_results['best']['il']]
            })
            def highlight_rows(row):
                return ['background: #D32F2F'] * len(row) if row['Scenario'] == 'Worst Case' else ['background: #FFB300'] * len(row) if row['Scenario'] == 'Expected Case' else ['background: #388E3C'] * len(row)
            styled_mc_df = df_monte_carlo.style.apply(highlight_rows, axis=1).set_table_attributes('class="monte-carlo-table"')
            st.table(styled_mc_df)

            with st.spinner("Generating chart..."):
                plt.figure(figsize=(10, 6))
                scenarios = ["Worst", "Expected", "Best"]
                values = [mc_results["worst"]["value"], mc_results["expected"]["value"], mc_results["best"]["value"]]
                colors = ["#D32F2F", "#FFB300", "#388E3C"]
                plt.bar(scenarios, values, color=colors)
                plt.axhline(y=investment_amount, color='#1E2A44', linestyle='--', label=f'Initial Investment (${investment_amount:,.2f})')
                plt.title("Monte Carlo Scenarios - 12 Month Pool Value")
                plt.ylabel("Value ($)")
                plt.legend()
                st.pyplot(plt)
                plt.clf()

        # Export Results
        with st.expander("Export Results", expanded=False):
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Current Impermanent Loss (%)", f"{il:.2f}"])
            writer.writerow(["12-Month Projected Value ($)", f"{future_value:,.0f}"])
            writer.writerow(["12-Month Net Return (x)", f"{net_return:.2f}"])
            writer.writerow(["Breakeven Against IL (months)", break_even_months])
            writer.writerow(["Breakeven With Price Changes (months)", break_even_months_with_price])
            writer.writerow(["Drawdown Initial ($)", f"{drawdown_initial:,.0f}"])
            writer.writerow(["Drawdown After 12 Months ($)", f"{drawdown_12_months:,.0f}"])
            writer.writerow(["Current TVL ($)", f"{current_tvl:,.0f}"])
            writer.writerow(["Platform Trust Score", f"{platform_trust_score}"])
            writer.writerow(["Hurdle Rate (%)", f"{hurdle_rate:.1f}"])
            writer.writerow(["Hurdle Rate Value After 12 Months ($)", f"{hurdle_value_12_months:,.0f}"])
            csv_data = output.getvalue()

            pdf_data = generate_pdf_report(il, net_return, future_value, break_even_months, break_even_months_with_price,
                                           drawdown_initial, drawdown_12_months, current_tvl, platform_trust_score,
                                           hurdle_rate, hurdle_value_12_months, risk_messages)

            col_csv, col_pdf = st.columns(2)
            with col_csv:
                st.download_button(
                    label="Export Results as CSV",
                    data=csv_data,
                    file_name="pool_results.csv",
                    mime="text/csv"
                )
            with col_pdf:
                st.download_button(
                    label="Export Results as PDF",
                    data=pdf_data,
                    file_name="pool_results.pdf",
                    mime="application/pdf"
                )
