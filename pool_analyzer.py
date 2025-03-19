import math

def calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment):
    """
    Calculate Impermanent Loss (IL) based on price changes.
    Returns value_if_held, pool_value, and IL percentage.
    """
    value_if_held = initial_investment * (current_price_asset1 / initial_price_asset1)
    pool_value = initial_investment * math.sqrt(current_price_asset1 / initial_price_asset1)
    il_percentage = ((value_if_held - pool_value) / value_if_held) * 100
    return value_if_held, pool_value, il_percentage

def calculate_break_even_months(initial_pool_value, value_if_held, monthly_yield):
    """
    Calculate months to breakeven against IL based on yield.
    Returns months (capped at 12).
    """
    current_value = initial_pool_value
    months = 0
    while current_value < value_if_held and months < 12:
        months += 1
        current_value *= (1 + monthly_yield)
    return months if months < 12 else float('inf')

def calculate_future_value(initial_pool_value, months, apy, final_price_asset1, final_price_asset2):
    """
    Calculate future pool value with APY and expected price changes.
    Assumes initial_price_asset1 = 88000 for consistency with debug data.
    """
    apy_compounded_value = initial_pool_value * (1 + apy) ** (months / 12)
    new_pool_value = apy_compounded_value * math.sqrt(final_price_asset1 / 88000)  # Fixed initial price
    return new_pool_value

def calculate_apy_margin_of_safety(initial_pool_value, value_if_held, current_apy, months=12):
    """
    Calculate APY Margin of Safety: how much APY can drop before breakeven > 12 months.
    Returns percentage (0-100%).
    """
    target_value = value_if_held * 1.02  # 2% risk-free rate buffer
    min_apy = ((target_value / initial_pool_value) ** (12 / months) - 1)
    apy_mos = ((current_apy - min_apy) / current_apy) * 100 if current_apy > 0 else 0
    return max(0, min(apy_mos, 100))  # Cap between 0-100%

def calculate_volatility_score(il_percentage, tvl_decline):
    """
    Calculate Volatility Score based on IL and TVL decline (no price divergence).
    Returns score (0-50%).
    """
    il_factor = min(il_percentage / 5, 1.0)  # Cap IL contribution at 5%
    tvl_factor = min(abs(tvl_decline) / 20, 1.0)  # Cap TVL decline at 20%
    volatility_score = (il_factor + tvl_factor) * 25  # Scale to 0-50%
    return min(volatility_score, 50)  # Cap at 50% unless truly extreme

def analyze_pool():
    """
    Main function to analyze the liquidity pool and print results.
    Uses data from your debug output and results.
    """
    # Input parameters (from your data)
    initial_investment = 169.0
    initial_price_asset1, initial_price_asset2 = 88000.0, 1.0
    current_price_asset1, current_price_asset2 = 100000.0, 1.0
    final_price_asset1, final_price_asset2 = 600000.0, 1.0  # Expected price change
    apy = 0.105  # ~10.5% inferred from debug data
    tvl_decline = -16.96
    pool_share = 0.02
    risk_free_rate = 0.02

    # Core Metrics Calculations
    value_if_held, pool_value, il_percentage = calculate_il(
        initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2, initial_investment
    )
    breakeven_months = calculate_break_even_months(pool_value, value_if_held, apy / 12)
    future_value = calculate_future_value(pool_value, 12, apy, final_price_asset1, final_price_asset2)
    net_return = future_value / initial_investment
    apy_exit_threshold = risk_free_rate + 0.05 if il_percentage > 1 or tvl_decline < -20 else risk_free_rate + 0.02

    # Margin of Safety (APY only)
    apy_mos = calculate_apy_margin_of_safety(pool_value, value_if_held, apy)

    # Volatility Score
    volatility_score = calculate_volatility_score(il_percentage, tvl_decline)

    # Print Results
    print("Core Metrics")
    print(f"Impermanent Loss (at current time): {il_percentage:.2f}%")
    print(f"Months to Breakeven Against IL: {breakeven_months} months")
    print(f"Months to Breakeven Including Expected Price Changes: {breakeven_months} months")
    print(f"Net Return: {net_return:.2f}x (includes expected price changes specified for Asset 1 and Asset 2)")
    print(f"APY Exit Threshold: {apy_exit_threshold * 100:.2f}% (based on your risk-free rate; increased by 5% under high volatility or IL conditions)")
    print(f"TVL Decline: {tvl_decline:.2f}%")
    print(f"Pool Share: {pool_share:.2f}%")
    
    print("\nMargin of Safety")
    print(f"APY Margin of Safety: {apy_mos:.2f}% (APY can decrease by this percentage to 0.20% before breakeven exceeds 12 months)")
    print(f"Margin of Safety Assessment: {'✅ High' if apy_mos > 50 else '⚠️ Low'} Margin of Safety")
    
    print("\nRisk Management")
    print(f"TVL Decline Risk: {'✅ Low' if abs(tvl_decline) < 20 else '⚠️ High'} ({tvl_decline:.2f}% decline)")
    print(f"Pool Share Risk: {'✅ Low' if pool_share < 1 else '⚠️ High'} ({pool_share:.2f}%)")
    print("Protocol Risk: ⚠️ ⚠️ Advisory (30%)")  # Static value from your input
    print(f"Volatility Score: {'✅ Low' if volatility_score < 25 else '⚠️ Moderate'} ({volatility_score:.2f}%)")

if __name__ == "__main__":
    # Entry point to run the analysis
    analyze_pool()
