import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom CSS with Tooltip Styling
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
        min-height: 100px;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-title {
        font-size: 18px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        width: 20%;
        min-width: 150px;
        white-space: normal;
        word-wrap: break-word;
    }
    .metric-desc {
        font-size: 14px;
        color: #A9A9A9;
        width: 60%;
        overflow-y: auto;
        max-height: 120px;
        line-height: 1.4;
    }
    .tooltip-icon {
        cursor: pointer;
        color: #A9A9A9;
        font-size: 14px;
        position: relative;
    }
    .tooltip-icon:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 10;
    }
    .red-text { color: #FF4D4D; }
    .green-text { color: #32CD32; }
    .yellow-text { color: #FFD700; }
    .neutral-text { color: #A9A9A9; }
    /* ... (rest of your CSS remains unchanged) ... */
    @media (max-width: 768px) {
        .metric-tile {
            flex-direction: column;
            align-items: flex-start;
        }
        .metric-title, .metric-value, .metric-desc {
            width: 100%;
            min-width: 0;
        }
        .metric-value {
            font-size: 20px;
        }
        .metric-desc {
            max-height: 150px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ... (Your existing code for imports, logo, title, sidebar, etc., remains unchanged) ...

# Main content (only showing the "Key Metrics" section with tooltips)
if calculate:
    # ... (Your existing calculations remain unchanged) ...

    st.subheader("Key Metrics")
    roi = ((asset_values[-1] / initial_investment) - 1) * 100
    investment_multiple = asset_values[-1] / initial_investment if initial_investment > 0 else 0

    st.markdown("### Investment Returns and Risk-Adjusted Metrics")
    st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-title">💰 Investment Value (1 Year)
                <span class="tooltip-icon" data-tooltip="The projected value of your investment after 12 months based on the expected growth rate.">?</span>
            </div>
            <div class="metric-value">${asset_values[-1]:,.2f}<br>({investment_multiple:.2f}x)</div>
            <div class="metric-desc">Potential value of your ${initial_investment:,.2f} investment in 12 months.<br>
            <b>Insight:</b> {'Lock in profits if reached.' if roi > 50 else 'Hold and monitor.' if roi >= 0 else 'Reassess investment.'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-title">📉 Sortino Ratio
                <span class="tooltip-icon" data-tooltip="Measures return per unit of downside risk; higher is better.">?</span>
            </div>
            <div class="metric-value {'red-text' if sortino_ratio < 0 else ''}">{sortino_ratio:.2f}</div>
            <div class="metric-desc">Return per unit of downside risk.<br>
            <b>Insight:</b> {'Proceed confidently.' if sortino_ratio > 1 else 'Allocate to stable assets.' if sortino_ratio >= 0 else 'Shift to stable assets.'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-title">📊 Sharpe Ratio
                <span class="tooltip-icon" data-tooltip="Measures return per unit of total risk; above 1 indicates good risk-adjusted returns.">?</span>
            </div>
            <div class="metric-value {'red-text' if sharpe_ratio < 0 else ''}">{sharpe_ratio:.2f}</div>
            <div class="metric-desc">Return per unit of risk.<br>
            <b>Insight:</b> {'Proceed confidently.' if sharpe_ratio > 1 else 'Consider safer assets.' if sharpe_ratio >= 0 else 'Shift to stablecoins.'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Risk Metrics")
    st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-title">📉 Max Drawdown
                <span class="tooltip-icon" data-tooltip="The largest potential loss from peak to trough in a worst-case scenario.">?</span>
            </div>
            <div class="metric-value {'red-text' if max_drawdown > 30 else ''}">{max_drawdown:.2f}%</div>
            <div class="metric-desc">Largest potential loss in a worst-case scenario.<br>
            <b>Insight:</b> {'Minimal action needed.' if max_drawdown < 30 else f'Set stop-loss at {max_drawdown:.2f}%.' if max_drawdown <= 50 else 'Reduce exposure.'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-title">⚖️ Dilution Risk
                <span class="tooltip-icon" data-tooltip="Percentage of tokens yet to be released; higher values indicate greater future supply pressure.">?</span>
            </div>
            <div class="metric-value {'red-text' if dilution_ratio > 50 else ''}">{dilution_ratio:.2f}%</div>
            <div class="metric-desc">{dilution_text}<br>
            <b>Insight:</b> {'Minimal action needed.' if dilution_ratio < 20 else 'Check unlock schedule.' if dilution_ratio <= 50 else 'Reduce position.'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ... (Add similar tooltip spans to other metric tiles as needed) ...

# ... (Rest of your code remains unchanged) ...
