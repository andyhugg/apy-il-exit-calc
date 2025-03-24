import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import csv

# Core Calculation Functions (unchanged for brevity)
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

def check_exit_conditions(initial_investment: float, apy: float, initial_price_asset1, initial_price_asset2,
                         current_price_asset1, current_price_asset2, current_tvl: float, risk_free_rate: float,
                         expected_price_change_asset1: float, expected_price_change_asset2: float, is_new_pool: bool):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment)
    pool_value, _ = calculate_pool_value(initial_investment, initial_price_asset1, initial_price_asset2,
                                        current_price_asset1, current_price_asset2) if not is_new_pool else (initial_investment, 0.0)
    value_if_held = (initial_investment / 2 / initial_price_asset1 * current_price_asset1) + (initial_investment / 2 / initial_price_asset2 * current_price_asset2)
    future_value, _ = calculate_future_value(initial_investment, apy, 12, initial_price_asset1, initial_price_asset2,
                                            current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                            expected_price_change_asset2, is_new_pool)
    net_return = future_value / initial_investment if initial_investment > 0 else 0
    break_even_months = calculate_break_even_months(apy, il, pool_value, value_if_held)
    break_even_months_with_price = calculate_break_even_months_with_price_changes(
        initial_investment, apy, pool_value, initial_price_asset1, initial_price_asset2,
        current_price_asset1, current_price_asset2, expected_price_change_asset1, expected_price_change_asset2, value_if_held, is_new_pool
    )
    drawdown_initial = initial_investment * 0.1  # 90% loss
    drawdown_12_months = future_value * 0.1      # 90% loss

    # Calculate Hurdle Rate
    hurdle_rate = risk_free_rate + 6.0  # Original hurdle rate formula
    hurdle_value_12_months = initial_investment * (1 + hurdle_rate / 100)

    # Custom CSS for Metric Cards (Fixed Height)
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f0f0;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100px;  /* Fixed height for uniformity */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label {
        font-size: 14px;
        color: #333;
        font-weight: bold;
    }
    .metric-value {
        font-size: 16px;
        color: #000;
    }
    .metric-note {
        font-size: 12px;
        color: #666;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    # Simplified Output with Markdown
    st.subheader("Key Insights")
    
    # First Row: 3 cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Impermanent Loss</div>
            <div class="metric-value">{il:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">12-Month Outlook</div>
            <div class="metric-value">${future_value:,.0f} ({net_return:.2f}x return)</div>
            <div class="metric-note">After 12 months includes compounded APY, price changes, and IL</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current TVL</div>
            <div class="metric-value">${current_tvl:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Second Row: 3 cards
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Breakeven Time</div>
            <div class="metric-value">Against IL: {break_even_months} months, With Price Changes: {break_even_months_with_price} months</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Worst-Case Drawdown (90%)</div>
            <div class="metric-value">Initial: ${drawdown_initial:,.0f}, After 12 Months: ${drawdown_12_months:,.0f}</div>
            <div class="metric-note">After 12 months includes compounded APY, price changes, and IL</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Hurdle Rate</div>
            <div class="metric-value">{hurdle_rate:.1f}% (${hurdle_value_12_months:,.0f} after 12 months)</div>
        </div>
        """, unsafe_allow_html=True)

    # Risk Summary with TVL Check
    st.subheader("Risk Summary")
    risk_messages = []
    if net_return < 1.0:
        risk_messages.append("Loss projected")
    if il > 5.0:
        risk_messages.append("High IL")
    if current_tvl < 250000:
        risk_messages.append("TVL too low: Pool may be at risk of low liquidity or manipulation")

    if risk_messages:
        st.error(f"⚠️ High Risk: {', '.join(risk_messages)}")
    else:
        st.success("✅ Low Risk: Profitable with manageable IL")

    # Return all necessary values, including hurdle_rate and hurdle_value_12_months
    return (il, net_return, future_value, break_even_months, break_even_months_with_price, 
            drawdown_initial, drawdown_12_months, hurdle_rate, hurdle_value_12_months)

# Streamlit App
st.title("Simple Pool Analyzer")
st.write("Evaluate your liquidity pool with key insights and minimal clutter.")

# Simplified Sidebar (No Expander)
with st.sidebar:
    st.header("Your Pool")
    pool_status = st.selectbox("Pool Status", ["Existing Pool", "New Pool"])
    is_new_pool = (pool_status == "New Pool")
    
    if is_new_pool:
        current_price_asset1 = st.number_input("Asset 1 Price (Today) ($)", min_value=0.01, value=90.00, format="%.2f")
        current_price_asset2 = st.number_input("Asset 2 Price (Today) ($)", min_value=0.01, value=1.00, format="%.2f")
        initial_price_asset1 = current_price_asset1
        initial_price_asset2 = current_price_asset2
    else:
        initial_price_asset1 = st.number_input("Initial Asset 1 Price ($)", min_value=0.01, value=88000.00, format="%.2f")
        initial_price_asset2 = st.number_input("Initial Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f")
        current_price_asset1 = st.number_input("Current Asset 1 Price ($)", min_value=0.01, value=125000.00, format="%.2f")
        current_price_asset2 = st.number_input("Current Asset 2 Price ($)", min_value=0.01, value=1.00, format="%.2f")
    
    investment_amount = st.number_input("Investment ($)", min_value=0.01, value=2000.00, format="%.2f")
    apy = st.number_input("APY (%)", min_value=0.01, value=10.00, format="%.2f")

    expected_price_change_asset1 = st.number_input("Expected Price Change Asset 1 (%)", min_value=-100.0, value=0.0, format="%.2f")
    expected_price_change_asset2 = st.number_input("Expected Price Change Asset 2 (%)", min_value=-100.0, value=0.0, format="%.2f")
    current_tvl = st.number_input("Current TVL ($)", min_value=0.01, value=1000000.00, format="%.2f")
    current_btc_price = st.number_input("Current BTC Price ($)", min_value=0.01, value=84000.00, format="%.2f")
    btc_growth_rate = st.number_input("Expected BTC Growth Rate (%)", min_value=-100.0, value=-25.0, format="%.2f")
    risk_free_rate = st.number_input("Risk-Free Rate (%)", min_value=0.0, value=5.0, format="%.2f")

if st.sidebar.button("Calculate"):
    with st.spinner("Calculating..."):
        result = check_exit_conditions(
            investment_amount, apy, initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2,
            current_tvl, risk_free_rate, expected_price_change_asset1, expected_price_change_asset2, is_new_pool
        )
        (il, net_return, future_value, break_even_months, break_even_months_with_price, 
         drawdown_initial, drawdown_12_months, hurdle_rate, hurdle_value_12_months) = result

        # Projected Pool Value Chart with Hurdle Rate
        st.subheader("Projected Pool Value Over Time")
        time_periods = [0, 3, 6, 12]
        future_values = []
        for months in time_periods:
            value, _ = calculate_future_value(investment_amount, apy, months, initial_price_asset1, initial_price_asset2,
                                             current_price_asset1, current_price_asset2, expected_price_change_asset1,
                                             expected_price_change_asset2, is_new_pool)
            future_values.append(value)
        
        # Hurdle Rate (16% annual growth)
        hurdle_rate_chart = 0.16  # 16% annual growth for the chart (as previously defined)
        hurdle_values = [investment_amount * (1 + hurdle_rate_chart * (months / 12)) for months in time_periods]

        sns.set_theme()
        plt.figure(figsize=(10, 6))
        plt.plot(time_periods, future_values, marker='o', markersize=10, linewidth=3, color='#1f77b4', label="Pool Value")
        plt.fill_between(time_periods, future_values, color='#1f77b4', alpha=0.2)
        plt.plot(time_periods, hurdle_values, linestyle='--', linewidth=2, color='green', label="Hurdle Rate (16%)")
        plt.axhline(y=investment_amount, color='#ff3333', linestyle='--', linewidth=2, label=f"Initial Investment (${investment_amount:,.0f})")
        y_max = max(max(future_values), max(hurdle_values), investment_amount) * 1.1
        y_min = min(min(future_values), min(hurdle_values), investment_amount) * 0.9
        plt.fill_between(time_periods, investment_amount, y_max, color='green', alpha=0.1, label='Profit Zone')
        plt.fill_between(time_periods, y_min, investment_amount, color='red', alpha=0.1, label='Loss Zone')
        for i, value in enumerate(future_values):
            plt.text(time_periods[i], value + (y_max - y_min) * 0.05, f"${value:,.0f}", ha='center', fontsize=10, color='#1f77b4')
        plt.title("Projected Pool Value Over Time", fontsize=16, pad=20)
        plt.xlabel("Months", fontsize=12)
        plt.ylabel("Value ($)", fontsize=12)
        plt.xticks(time_periods, fontsize=10)
        plt.yticks(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(fontsize=10)
        plt.gca().set_facecolor('#f0f0f0')
        plt.tight_layout()
        st.pyplot(plt)
        st.caption("Projected over 12 months, including compounded APY, price changes, and IL.")

        st.subheader("Pool vs. BTC vs. Stablecoin Comparison")
        projected_btc_price = current_btc_price * (1 + btc_growth_rate / 100)
        initial_btc_amount = investment_amount / current_btc_price
        btc_value_12_months = initial_btc_amount * projected_btc_price
        pool_value_12_months = future_values[-1]
        stablecoin_value_12_months = investment_amount * (1 + risk_free_rate / 100)
        
        df_btc_comparison = pd.DataFrame({
            "Metric": ["Pool Value", "BTC Value", "Stablecoin Value"],
            "Value ($)": [f"${int(pool_value_12_months):,}", f"${int(btc_value_12_months):,}", f"${int(stablecoin_value_12_months):,}"]
        })
        st.dataframe(df_btc_comparison.style.set_properties(**{'text-align': 'right'}), hide_index=True, use_container_width=True)
        st.caption("Values projected over 12 months. Pool value includes compounded APY, price changes, and IL.")

        st.subheader("Monte Carlo Scenarios - 12 Months")
        mc_results = simplified_monte_carlo_analysis(
            investment_amount, apy, initial_price_asset1, initial_price_asset2,
            current_price_asset1, current_price_asset2, expected_price_change_asset1,
            expected_price_change_asset2, is_new_pool
        )
        df_monte_carlo = pd.DataFrame({
            "Scenario": ["Worst Case", "Expected Case", "Best Case"],
            "Value ($)": [f"${mc_results['worst']['value']:,.0f}", f"${mc_results['expected']['value']:,.0f}", f"${mc_results['best']['value']:,.0f}"]
        })
        def highlight_rows(row):
            if row["Scenario"] == "Worst Case":
                return ['background-color: #ff4d4d; color: white'] * len(row)
            elif row["Scenario"] == "Expected Case":
                return ['background-color: #ffeb3b; color: black'] * len(row)
            elif row["Scenario"] == "Best Case":
                return ['background-color: #4caf50; color: white'] * len(row)
            return [''] * len(row)
        styled_df_monte_carlo = df_monte_carlo.style.apply(highlight_rows, axis=1).set_properties(**{'text-align': 'center'})
        st.dataframe(styled_df_monte_carlo, hide_index=True, use_container_width=True)

        sns.set_theme()
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

        # CSV Export
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
        writer.writerow(["Hurdle Rate (%)", f"{hurdle_rate:.1f}"])
        writer.writerow(["Hurdle Rate Value After 12 Months ($)", f"{hurdle_value_12_months:,.0f}"])
        csv_data = output.getvalue()
        st.download_button(
            label="Export Results as CSV",
            data=csv_data,
            file_name="pool_results.csv",
            mime="text/csv"
        )
