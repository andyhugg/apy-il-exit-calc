import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Optional CoinGecko
try:
    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()
    use_api = True
except ImportError:
    cg = None
    use_api = False
    st.warning("CoinGecko API unavailable. Enter current values manually.")

st.title("Crypto Clarity: Your Crypto Decision Tool")

# Disclaimer
st.markdown("""
**Disclaimer**: This tool is for informational and educational purposes only—it is *not* financial advice. 
Crypto investments are highly volatile and risky. All suggestions are based on your inputs and hypothetical scenarios. 
Always do your own research and consult a professional if needed before making decisions.
""")

# Session state for reset
if 'reset' not in st.session_state:
    st.session_state.reset = False

# Clear Button
if st.button("Clear All Inputs"):
    st.session_state.clear()
    st.rerun()

# Portfolio Input with Simple Fields
st.header("Step 1: Enter Your Portfolio")
num_assets = st.number_input("Number of Assets", min_value=1, value=3, step=1)
assets = []
coin_ids = {"BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "USDC": "usd-coin"}
prices = cg.get_price(ids=",".join(coin_ids.values()), vs_currencies="usd") if use_api else {}

for i in range(num_assets):
    st.subheader(f"Asset {i+1}")
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input(f"Name", value=f"Asset{i+1}", key=f"name_{i}")
    with col2:
        default_curr = 0.0
        if use_api and name in coin_ids and coin_ids[name] in prices:
            default_curr = prices[coin_ids[name]]["usd"]
        curr_val = st.number_input(f"Current Value ($)", min_value=0.0, value=default_curr, key=f"curr_{i}",
                                   help=f"Live price: ${default_curr:.2f}" if default_curr else None)
    with col3:
        init_val = st.number_input(f"Initial Value ($)", min_value=0.0, value=0.0, key=f"init_{i}")
    assets.append({"Name": name, "Current": curr_val, "Initial": init_val})

# Create DataFrame and calculate allocation
df_assets = pd.DataFrame(assets)
total_portfolio = df_assets["Current"].sum()
if total_portfolio > 0:
    df_assets["Allocation"] = df_assets["Current"] / total_portfolio
else:
    df_assets["Allocation"] = 0.0  # Default to 0 if no value
    st.warning("Total portfolio value is $0. Enter non-zero current values to proceed.")
df_assets["Gain/Loss"] = df_assets.apply(lambda row: (row["Current"] - row["Initial"]) / row["Initial"] if row["Initial"] > 0 else 0.0, axis=1)

# Risk and Goals
st.header("Step 2: Set Your Goals & Risk")
goal = st.selectbox("Your Goal", ["Preserve Capital", "Balanced Growth", "Chase Moonshots"])
risk_tolerance = st.slider("Max Loss Tolerance (%)", 0, 100, 20, help="How much can you afford to lose?") / 100
time_horizon = st.number_input("Time Horizon (months)", min_value=1, value=6)

# Assign Risk Levels
risk_levels = {"BTC": 0.3, "ETH": 0.5, "USDT": 0.1, "USDC": 0.1}
for asset in df_assets["Name"]:
    if asset not in risk_levels:
        risk_levels[asset] = 0.9
df_assets["Risk"] = df_assets["Name"].map(risk_levels)
portfolio_risk = (df_assets["Allocation"] * df_assets["Risk"]).sum()

# Scenarios
st.header("Step 3: Define Scenarios")
scenario_configs = {
    "Preserve Capital": {"Bear": (-0.2, -0.3, -0.8), "Base": (0.1, 0.05, -0.2), "Bull": (0.3, 0.2, 0.5)},
    "Balanced Growth": {"Bear": (-0.3, -0.4, -0.7), "Base": (0.2, 0.15, 1.0), "Bull": (0.5, 0.4, 2.0)},
    "Chase Moonshots": {"Bear": (-0.5, -0.5, -1.0), "Base": (0.3, 0.2, 3.0), "Bull": (0.7, 0.6, 10.0)}
}
default_scenarios = {
    "Bear": dict(zip(df_assets["Name"], scenario_configs[goal]["Bear"] * len(df_assets) if len(df_assets) > 3 else scenario_configs[goal]["Bear"])),
    "Base": dict(zip(df_assets["Name"], scenario_configs[goal]["Base"] * len(df_assets) if len(df_assets) > 3 else scenario_configs[goal]["Base"])),
    "Bull": dict(zip(df_assets["Name"], scenario_configs[goal]["Bull"] * len(df_assets) if len(df_assets) > 3 else scenario_configs[goal]["Bull"]))
}
probs = {"Bear": 0.5, "Base": 0.3, "Bull": 0.2}

for scenario in default_scenarios:
    with st.expander(f"{scenario} Scenario"):
        for asset in df_assets["Name"]:
            default_scenarios[scenario][asset] = st.number_input(f"{asset} Change (%) - {scenario}", 
                                                                 value=default_scenarios[scenario].get(asset, 0.0) * 100, 
                                                                 step=1.0, key=f"{asset}_{scenario}") / 100
        probs[scenario] = st.slider(f"{scenario} Probability (%)", 0.0, 100.0, probs[scenario] * 100, key=f"prob_{scenario}") / 100

if abs(sum(probs.values()) - 1.0) > 0.01:
    st.error("Probabilities must sum to 100%")

# Fees
st.header("Step 4: Transaction Costs")
swap_fee = st.number_input("Swap Fee ($)", min_value=0.0, value=5.0, help="Cost to swap assets")

# Calculate Outcomes
outcomes = {}
swap_outcomes = {asset: {} for asset in df_assets["Name"]}
btc_price = df_assets[df_assets["Name"] == "BTC"]["Current"].values[0] if "BTC" in df_assets["Name"].values else 60000

for scenario, changes in default_scenarios.items():
    total_stay = 0
    for _, row in df_assets.iterrows():
        total_stay += row["Current"] * (1 + changes.get(row["Name"], 0))
    outcomes[scenario] = total_stay

    for asset in df_assets["Name"]:
        if asset != "BTC":
            asset_curr = df_assets[df_assets["Name"] == asset]["Current"].values[0]
            btc_amount = max(0, (asset_curr - swap_fee)) / btc_price
            total_swap = total_portfolio - asset_curr + (btc_amount * btc_price * (1 + changes.get("BTC", 0)))
            swap_outcomes[asset][scenario] = total_swap
        else:
            swap_outcomes[asset][scenario] = total_stay  # No swap for BTC

# Expected Values
exp_stay = sum(probs[s] * outcomes[s] for s in outcomes)
exp_swap = {asset: sum(probs[s] * swap_outcomes[asset][s] for s in swap_outcomes[asset]) for asset in swap_outcomes}

# Decision Engine
suggestions = {}
for _, row in df_assets.iterrows():
    asset = row["Name"]
    if asset == "BTC":
        suggestions[asset] = "Hold: Stable anchor for your portfolio."
    else:
        exp_diff = exp_swap[asset] - exp_stay
        risk_impact = row["Risk"] * row["Allocation"]
        if risk_impact > risk_tolerance / len(df_assets) and exp_diff > 0:
            suggestions[asset] = f"Swap to BTC: Cuts risk by {risk_impact:.2%}, gains ${exp_diff:.0f} expected value."
        elif row["Gain/Loss"] < -0.5 and exp_stay > exp_swap[asset]:
            suggestions[asset] = "Hold: Recovery potential may outweigh swapping."
        else:
            suggestions[asset] = "Neutral: Risk and reward are balanced."

# Rebalancing Suggestion
target_alloc = {"BTC": 0.6, "ETH": 0.3, "Stable": 0.1} if goal == "Preserve Capital" else \
               {"BTC": 0.4, "ETH": 0.4, "Altcoins": 0.2} if goal == "Balanced Growth" else \
               {"BTC": 0.3, "ETH": 0.3, "Altcoins": 0.4}
rebalance = "Consider shifting to: " + ", ".join(f"{k}: {v:.0%}" for k, v in target_alloc.items())

# Results
st.header("Your Portfolio Insights")
st.write(f"Total Portfolio Value: ${total_portfolio:.2f}")
st.dataframe(df_assets.style.format({"Current": "${:.2f}", "Initial": "${:.2f}", "Allocation": "{:.2%}", "Gain/Loss": "{:.2%}", "Risk": "{:.2f}"}))

# Pie Chart
if total_portfolio > 0:
    fig, ax = plt.subplots()
    ax.pie(df_assets["Allocation"], labels=df_assets["Name"], autopct="%1.1f%%")
    st.pyplot(fig)
st.write(f"Portfolio Risk Score: {portfolio_risk:.2f} (vs. Tolerance: {risk_tolerance:.2f})")

st.subheader("Scenario Outcomes")
df_outcomes = pd.DataFrame(outcomes, index=["Stay"]).T
for asset in swap_outcomes:
    df_outcomes[f"Swap {asset} to BTC"] = [swap_outcomes[asset].get(s, outcomes[s]) for s in df_outcomes.index]
st.table(df_outcomes.style.format("${:.2f}"))

st.subheader("Expected Portfolio Value")
st.write(f"Stay: ${exp_stay:.0f}")
for asset, val in exp_swap.items():
    st.write(f"Swap {asset} to BTC: ${val:.0f}")

# Bar Chart
if total_portfolio > 0:
    fig, ax = plt.subplots()
    options = ["Stay"] + [f"Swap {a} to BTC" for a in exp_swap.keys()]
    values = [exp_stay] + list(exp_swap.values())
    ax.bar(options, values)
    ax.set_ylabel("Expected Value ($)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

st.subheader("Suggestions")
for asset, suggestion in suggestions.items():
    st.write(f"- {asset}: {suggestion}")
st.write(f"Rebalancing Idea: {rebalance}")

st.sidebar.write("Input your holdings, goals, and scenarios to get tailored insights!")
