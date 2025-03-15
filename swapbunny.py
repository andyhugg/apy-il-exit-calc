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
    df_assets["Allocation"] = 0.0
    st.warning("Total portfolio value is $0. Enter non-zero current values to proceed.")
df_assets["Gain/Loss"] = df_assets.apply(lambda row: (row["Current"] - row["Initial"]) / row["Initial"] if row["Initial"] > 0 else 0.0, axis=1)

# Risk and Goals
st.header("Step 2: Set Your Goals & Risk")
goal = st.selectbox("Your Goal", ["Preserve Capital", "Balanced Growth", "Chase Moonshots"])
risk_tolerance = st.slider("Max Loss Tolerance (%)", 0, 100, 20, help="How much can you afford to lose?") / 100
time_horizon = st.number_input("Time Horizon (months)", min_value=1, value=6)

# Assign Risk Levels and Asset Types
risk_levels = {"BTC": 0.3, "ETH": 0.5, "USDT": 0.1, "USDC": 0.1}
asset_types = {"BTC": "Major", "ETH": "Major", "USDT": "Stable", "USDC": "Stable"}
for asset in df_assets["Name"]:
    if asset not in risk_levels:
        risk_levels[asset] = 0.9
    if asset not in asset_types:
        asset_types[asset] = "Altcoin"
df_assets["Risk"] = df_assets["Name"].map(risk_levels)
df_assets["Type"] = df_assets["Name"].map(asset_types)
portfolio_risk = (df_assets["Allocation"] * df_assets["Risk"]).sum()

# Scenarios
st.header("Step 3: Define Market Scenario")
scenario = st.radio("Select a market scenario:", 
                    ["Bear Market: I expect a downturn", 
                     "Base Case: I expect moderate growth", 
                     "Bull Market: I expect a strong rally"])
scenario = scenario.split(":")[0].split()[0]  # Extract "Bear", "Base", or "Bull"

# Presets for percentage changes
presets = {
    "Stable": {"Bear": 0.0, "Base": 0.0, "Bull": 0.0},  # Stablecoins don't change with scenarios
    "Major": {"Bear": -25.0, "Base": 25.0, "Bull": 75.0},
    "Altcoin": {"Bear": -90.0, "Base": 50.0, "Bull": 200.0}
}

# User-defined percentage changes for the selected scenario
st.write(f"**{scenario} Case Expectations**")
st.write("Enter your expected change for each asset (except stablecoins). Presets are based on historical volatility.")
scenario_data = {}
for _, row in df_assets.iterrows():
    asset = row["Name"]
    asset_type = row["Type"]
    scenario_data[asset] = {}
    if asset_type == "Stable":
        st.write(f"{asset} (Current: ${row['Current']:.2f}): Grows at 10% APY (e.g., to ${(row['Current'] * (1 + 0.10 * time_horizon / 12)):.2f} in {time_horizon} months)")
        scenario_data[asset][scenario] = 0.0  # Stablecoins don't change with scenario
    else:
        preset = presets[asset_type][scenario]
        change = st.number_input(f"{asset} (Current: ${row['Current']:.2f})", value=preset, step=1.0, key=f"{asset}_{scenario}")
        scenario_data[asset][scenario] = change / 100

# Fees
st.header("Step 4: Transaction Costs")
swap_fee = st.number_input("Swap Fee ($)", min_value=0.0, value=5.0, help="Cost to swap assets")

# Calculate Outcomes
outcomes = {"Stay": 0.0}
swap_outcomes = {asset: {"Scenario": 0.0, "CAGR": 0.0, "Stablecoin": 0.0} for asset in df_assets["Name"]}
btc_price = df_assets[df_assets["Name"] == "BTC"]["Current"].values[0] if "BTC" in df_assets["Name"].values else 60000
can_swap_to_btc = "BTC" in df_assets["Name"].values

# Stay Outcome
for _, row in df_assets.iterrows():
    asset = row["Name"]
    if row["Type"] == "Stable":
        # Stablecoins grow at 10% APY
        outcomes["Stay"] += row["Current"] * (1 + 0.10 * time_horizon / 12)
    else:
        # Non-stablecoins use user-defined scenario change
        outcomes["Stay"] += row["Current"] * (1 + scenario_data[asset][scenario])

# Swap Outcomes
for _, row in df_assets.iterrows():
    asset = row["Name"]
    asset_curr = row["Current"]
    
    # Swap to Stablecoin (10% APY)
    stable_value = max(0, asset_curr - swap_fee) * (1 + 0.10 * time_horizon / 12)
    swap_outcomes[asset]["Stablecoin"] = total_portfolio - asset_curr + stable_value
    
    if asset == "BTC":
        swap_outcomes[asset]["Scenario"] = outcomes["Stay"]
        swap_outcomes[asset]["CAGR"] = outcomes["Stay"]
        continue  # No swap for BTC
    
    # Swap to BTC (Scenario-Based)
    if can_swap_to_btc:
        btc_amount = max(0, (asset_curr - swap_fee)) / btc_price
        btc_value = btc_amount * btc_price * (1 + scenario_data["BTC"][scenario])
        swap_outcomes[asset]["Scenario"] = total_portfolio - asset_curr + btc_value
    else:
        swap_outcomes[asset]["Scenario"] = outcomes["Stay"]  # Can't swap without BTC
    
    # Swap to BTC (20% CAGR)
    btc_cagr_price = btc_price * (1 + 0.20) ** (time_horizon / 12)
    btc_cagr_value = btc_amount * btc_cagr_price
    swap_outcomes[asset]["CAGR"] = total_portfolio - asset_curr + btc_cagr_value

# Decision Engine
suggestions = {}
for _, row in df_assets.iterrows():
    asset = row["Name"]
    if asset == "BTC":
        suggestions[asset] = "Hold: Stable anchor for your portfolio."
    else:
        stay_val = outcomes["Stay"]
        swap_scenario = swap_outcomes[asset]["Scenario"]
        swap_cagr = swap_outcomes[asset]["CAGR"]
        swap_stable = swap_outcomes[asset]["Stablecoin"]
        best_val = max(stay_val, swap_scenario, swap_cagr, swap_stable)
        risk_impact = row["Risk"] * row["Allocation"]
        
        if not can_swap_to_btc and (best_val == swap_scenario or best_val == swap_cagr):
            suggestions[asset] = "Cannot swap to BTC: BTC must be in your portfolio to swap into BTC."
        elif best_val == stay_val:
            suggestions[asset] = f"Hold: Best outcome (${stay_val:.0f}) in this scenario."
        elif best_val == swap_scenario:
            suggestions[asset] = f"Swap to BTC (Scenario): Gains ${best_val - stay_val:.0f} and cuts risk by {risk_impact:.2%}."
        elif best_val == swap_cagr:
            suggestions[asset] = f"Swap to BTC (20% CAGR): Gains ${best_val - stay_val:.0f} and cuts risk by {risk_impact:.2%}."
        else:
            suggestions[asset] = f"Swap to Stablecoin (10% APY): Gains ${best_val - stay_val:.0f} and cuts risk by {risk_impact:.2%}."

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

# Scenario Outcomes
st.subheader("Scenario Outcomes")
df_outcomes = pd.DataFrame({scenario: [outcomes["Stay"]]}, index=["Stay"]).T
for asset in swap_outcomes:
    if asset != "BTC":
        if can_swap_to_btc:
            df_outcomes[f"Swap {asset} to BTC ({scenario})"] = [swap_outcomes[asset]["Scenario"]]
            df_outcomes[f"Swap {asset} to BTC (20% CAGR)"] = [swap_outcomes[asset]["CAGR"]]
        df_outcomes[f"Swap {asset} to Stablecoin (10% APY)"] = [swap_outcomes[asset]["Stablecoin"]]
if not can_swap_to_btc:
    st.warning("Swap to BTC not available: BTC must be in your portfolio to calculate scenario-based or CAGR swaps into BTC.")
st.table(df_outcomes.style.format("${:.2f}"))

# Comparison Across Scenarios (Using Presets)
st.subheader("Comparison Across Scenarios (Using Presets)")
comp_outcomes = {}
for s in ["Bear", "Base", "Bull"]:
    total = 0.0
    for _, row in df_assets.iterrows():
        asset = row["Name"]
        if row["Type"] == "Stable":
            total += row["Current"] * (1 + 0.10 * time_horizon / 12)
        else:
            change = presets[row["Type"]][s] / 100
            total += row["Current"] * (1 + change)
    comp_outcomes[s] = total
df_comp = pd.DataFrame(comp_outcomes, index=["Stay"]).T
st.table(df_comp.style.format("${:.2f}"))

# Bar Chart
if total_portfolio > 0:
    fig, ax = plt.subplots()
    options = ["Stay"]
    values = [outcomes["Stay"]]
    for asset in swap_outcomes:
        if asset != "BTC":
            if can_swap_to_btc:
                options += [f"Swap {asset} to BTC ({scenario})", f"Swap {asset} to BTC (20% CAGR)"]
                values += [swap_outcomes[asset]["Scenario"], swap_outcomes[asset]["CAGR"]]
            options += [f"Swap {asset} to Stablecoin (10% APY)"]
            values += [swap_outcomes[asset]["Stablecoin"]]
    ax.bar(options, values)
    ax.set_ylabel("Portfolio Value ($)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

st.subheader("Suggestions")
for asset, suggestion in suggestions.items():
    st.write(f"- {asset}: {suggestion}")
st.write(f"Rebalancing Idea: {rebalance}")

st.sidebar.write("Input your holdings, goals, and scenarios to get tailored insights!")
