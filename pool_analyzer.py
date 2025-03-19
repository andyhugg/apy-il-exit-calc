# ... (previous code remains the same until fetch_defi_data)

def fetch_defi_data(pool_address: str, chain: str = "unknown") -> tuple[float, float]:
    url = f"https://api.llama.fi/yields?pool={pool_address}"
    headers = {"Accept": "application/json"}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                apy = float(data["data"][0].get("apy", 0)) * 100
                tvl = float(data["data"][0].get("tvlUsd", 0))
                return apy, tvl
            else:
                st.warning("DeFi Llama API returned no data. Trying chain-specific fallback...")
                break
        except requests.exceptions.RequestException as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                st.warning("Rate limit exceeded. Retrying in 60 seconds...")
                time.sleep(60)
            else:
                st.warning(f"API request failed: {str(e)}. Trying chain-specific fallback...")
                break
    # Fallback for Solana (Raydium API with token pair search)
    if chain == "solana":
        raydium_url = "https://api.raydium.io/v2/ammV3/ammPools"
        try:
            response = requests.get(raydium_url, timeout=10)
            response.raise_for_status()
            pools = response.json().get("data", [])
            sol_mint = "So11111111111111111111111111111111111111112"  # SOL mint
            # Assume WTRUMP mint needs to be derived (placeholder)
            wtrump_mint = "27.528804.7091402618000"  # Approximate from screenshot
            for pool in pools:
                if (pool.get("mintA") in [sol_mint, wtrump_mint] and pool.get("mintB") in [sol_mint, wtrump_mint] and
                    pool.get("feeRate") == "0.01"):  # 0.01% fee tier
                    tvl = float(pool.get("liquidity", 0))
                    apy = float(pool.get("apr", 0)) * 100 if pool.get("apr") else 0.0
                    return apy, tvl
            st.warning("Raydium API did not find this pool by token pair. Falling back to manual input.")
        except requests.exceptions.RequestException as e:
            st.warning(f"Raydium API failed: {str(e)}. Falling back to manual input.")
    return None, None

# ... (rest of the code remains the same)
