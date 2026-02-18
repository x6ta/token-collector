# DeFi Protocol Integration

This document describes the integrated DeFi protocols and how the token collector interacts with them.

---

## Overview

The token collector automatically detects and withdraws assets from supported DeFi protocols before collecting standard tokens. This ensures maximum asset recovery from donor wallets.

**Supported Protocols**: 3  
**Total Markets**: 11 markets across 3 chains

---

## 1. LayerBank (Scroll Network)

### Overview
LayerBank is a lending and borrowing protocol on Scroll. Users can deposit assets to earn interest, receiving lTokens (e.g., lUSDC) that represent their deposited amount plus accrued interest.

### Configuration

**Network**: Scroll (Chain ID: 534352)  
**Core Contract**: `0xEC53c830f4444a8A56455c6836b5D2aA794289Aa`

### Supported Markets (8 Total)

| lToken | Underlying Asset | Contract Address |
|--------|-----------------|------------------|
| lETH | ETH | `0x274C3795dadfEbf562932992bF241ae087e0a98C` |
| lUSDC | USDC | `0x0D8F8e271DD3f2fC58e5716d3Ff7041dBe3F0688` |
| lwstETH | wstETH | `0xB6966083c7b68175B4BF77511608AEe9A80d2Ca4` |
| lwrsETH | wrsETH | `0xec0AD3f43E85fc775a9C9b77f0F0aA7FE5A587d6` |
| lSTONE | STONE | `0xE5C40a3331d4Fb9A26F5e48b494813d977ec0A8E` |
| luniETH | uniETH | `0xBd1d62e74c6d165ccae6d161588a3768023DCc18` |
| lWBTC | WBTC | `0xc40D6957B8110eC55f0F1A20d7D3430e1d8Aa4cf` |
| lUSDT | USDT | `0xE0Cee49cC3C9d047C0B175943ab6FCC3c4F40fB0` |

### How It Works

#### 1. Detection Phase
```python
ltoken_contract = w3.eth.contract(address=ltoken_address, abi=LTOKEN_ABI)
ltoken_balance = ltoken_contract.functions.balanceOf(wallet_address).call()
```

- Checks balance of each lToken
- Skips if balance is 0

#### 2. Exchange Rate Calculation
```python
exchange_rate = ltoken_contract.functions.exchangeRateCurrent().call()
underlying_amount = (ltoken_balance * exchange_rate) / 1e18
```

- Gets current exchange rate from contract
- Calculates underlying token amount
- Exchange rate includes accrued interest

#### 3. Withdrawal
```python
ltoken_contract.functions.redeemUnderlying(underlying_amount).transact()
```

- Calls `redeemUnderlying()` to withdraw
- Burns lTokens
- Receives underlying asset
- Waits 60 seconds for settlement

#### 4. Settlement Wait
```python
time.sleep(60)  # Wait for LayerBank settlement
```

- Ensures withdrawal is processed
- Prevents race conditions
- After wait, underlying tokens are collected in standard flow

### Gas Costs

- **Withdrawal**: ~200,000-300,000 gas
- **Total Cost**: $0.50-$1.50 (depends on ETH price and Scroll gas price)

### Error Handling

- **Insufficient Balance**: Skipped gracefully
- **Contract Error**: Logged, continues to next market
- **Network Timeout**: Retries with exponential backoff

---

## 2. SyncSwap (zkSync ERA)

### Overview
SyncSwap is a native DEX on zkSync ERA with concentrated liquidity pools. Users provide liquidity and receive LP tokens representing their pool share.

### Configuration

**Network**: zkSync ERA (Chain ID: 324)  
**Router**: `0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295` (Classic Router)  
**Pool Factory**: `0xf2DAd89f2788a8CD54625C60b55cD3d2D0ACa7Cb`  
**Vault**: `0x621425a1Ef6abE91058E9712575dcc4258F8d091`

### Supported Pools (2 Total)

#### 1. ETH/USDC Pool
- **Pool Address**: `0x80115c708E12eDd42E504c1cD52Aea96C547c05c`
- **Token0**: USDC (`0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4`)
- **Token1**: WETH (`0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91`)
- **Decimals**: USDC: 6, WETH: 18

#### 2. USDC/USDT Pool
- **Pool Address**: `0xd3D91634Cf4C04aD1B76cE2c06F7385A897F54D3`
- **Token0**: USDT (`0x493257fD37EDB34451f62EDf8D2a0C418852bA4C`)
- **Token1**: WETH (`0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91`)
- **Decimals**: USDT: 6, WETH: 18

### How It Works

#### 1. Detection Phase
```python
pool_contract = w3.eth.contract(address=pool_address, abi=SYNCSWAP_POOL_ABI)
lp_balance = pool_contract.functions.balanceOf(wallet_address).call()

# Dust filter
if lp_balance < 10000000000:  # < 0.0001 LP tokens
    skip_position()
```

- Checks LP token balance for each pool
- Filters dust positions (< 0.0001 LP)
- Prevents arithmetic underflow errors

#### 2. Reserves Calculation
```python
reserves = pool_contract.functions.getReserves().call()
reserve0, reserve1 = reserves[0], reserves[1]
total_supply = pool_contract.functions.totalSupply().call()

# Pool share calculation
token0_amount = (lp_balance * reserve0) / total_supply
token1_amount = (lp_balance * reserve1) / total_supply
```

- Gets pool reserves from contract
- Calculates user's share of pool
- Adjusts for decimals (6 for USDC/USDT, 18 for ETH)

#### 3. USD Value Calculation
```python
# Detect decimals based on token address
usdc_usdt_addresses = [
    "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4",  # USDC
    "0x493257fd37edb34451f62edf8d2a0c418852ba4c",  # USDT
]

token0_decimals = 6 if token0.lower() in usdc_usdt_addresses else 18
token1_decimals = 6 if token1.lower() in usdc_usdt_addresses else 18

# Calculate USD value
token0_usd = (token0_amount / (10 ** token0_decimals)) * token0_price
token1_usd = (token1_amount / (10 ** token1_decimals)) * token1_price
total_usd = token0_usd + token1_usd
```

- Automatically detects decimals by token address
- Converts amounts to USD using real-time prices
- Sums both sides of the pool

#### 4. Withdrawal
```python
# Build withdrawal data
withdraw_data = encode_abi(
    ['address', 'address', 'uint8'],
    [token0, wallet_address, 1]  # withdrawMode = 1 (proportional)
)

# Execute burn (single transaction)
pool_contract.functions.burn(
    withdraw_data,
    [0, 0]  # min_amounts (allow any amount for dust)
).transact({
    'from': wallet_address,
    'gas': 500000,
    'gasPrice': gas_price,
    'nonce': nonce,
    'chainId': chain_id
})
```

- **No type:2**: zkSync ERA doesn't support EIP-1559
- **min_amounts = [0, 0]**: Prevents underflow for small amounts
- **Single transaction**: Burns LP and receives underlying tokens
- **Gas limit**: 500,000 (higher for zkSync)

#### 5. Settlement Wait
```python
time.sleep(60)  # Wait for SyncSwap settlement
```

- Ensures LP burn is processed
- After wait, received tokens (ETH, USDC, USDT) are collected

### Gas Costs

- **Burn LP**: ~300,000-500,000 gas
- **Total Cost**: $0.20-$0.50 (zkSync has low gas fees)

### Error Handling

- **Dust positions**: Automatically skipped (< 0.0001 LP)
- **Arithmetic underflow**: Prevented by min_amounts = [0, 0]
- **Type:2 error**: Fixed by removing EIP-1559 fields
- **Network timeout**: Retries with exponential backoff

### Known Issues & Fixes

#### Issue 1: Wrong USD Calculation ($0.00 or millions)
**Cause**: Incorrect decimal handling  
**Fix**: Use token address to detect decimals (USDC/USDT = 6, ETH = 18)  
**Status**: ✅ FIXED

#### Issue 2: Transaction Reverted (Arithmetic Underflow)
**Cause**: Dust LP positions (< 0.0001 tokens)  
**Fix**: Add minimum LP balance filter  
**Status**: ✅ FIXED

#### Issue 3: "invalid type: integer `2`"
**Cause**: zkSync ERA doesn't support EIP-1559 (type:2 transactions)  
**Fix**: Remove `type:2` and use legacy gas pricing  
**Status**: ✅ FIXED

---

## 3. Swapr (Arbitrum)

### Overview
Swapr is a community-owned DEX on Arbitrum with governance features. Users can provide liquidity to earn fees and governance tokens.

### Configuration

**Network**: Arbitrum One (Chain ID: 42161)  
**Router**: `0x530476d5583724A89c8841eB6Da76E7Af4C0F17E`  
**Factory**: `0x359F20Ad0F42D75a5077e65F30274cABe6f4F01a`

### Supported Pools (1 Total)

#### USDC/WETH Pool
- **Pair Address**: `0x9C05e740F34FBB2F8b770A7b89Ed12E4c7F6E32B`
- **Token0**: USDC (`0xaf88d065e77c8cc2239327c5edb3a432268e5831`)
- **Token1**: WETH (`0x82af49447d8a07e3bd95bd0d56f35241523fbab1`)

### How It Works

#### 1. Detection Phase
```python
pair_contract = w3.eth.contract(address=pair_address, abi=SWAPR_PAIR_ABI)
lp_balance = pair_contract.functions.balanceOf(wallet_address).call()
```

- Checks LP token balance
- Skips if balance is 0

#### 2. Pool Share Calculation
```python
reserves = pair_contract.functions.getReserves().call()
reserve0, reserve1 = reserves[0], reserves[1]
total_supply = pair_contract.functions.totalSupply().call()

usdc_amount = (lp_balance * reserve0) / total_supply
weth_amount = (lp_balance * reserve1) / total_supply
```

- Gets reserves from pair contract
- Calculates proportional share
- USDC: 6 decimals, WETH: 18 decimals

#### 3. Approval
```python
pair_contract.functions.approve(
    router_address,
    lp_balance  # or max_uint256 for unlimited
).transact()
```

- Approves router to spend LP tokens
- Required before withdrawal

#### 4. Withdrawal (IN DEVELOPMENT)
```python
router_contract.functions.removeLiquidity(
    token0,
    token1,
    lp_balance,
    min_token0,  # Minimum amount of token0 to receive
    min_token1,  # Minimum amount of token1 to receive
    wallet_address,
    deadline
).transact()
```

- **Status**: Approval works, withdrawal fails
- **Issue**: Needs debugging (reverts with unknown error)
- **Workaround**: Manual withdrawal via Swapr UI

### Gas Costs

- **Approval**: ~50,000 gas (~$0.10-$0.20)
- **Withdrawal**: ~150,000 gas (~$0.50-$1.00)

### Current Status

- ✅ Detection: Working
- ✅ Approval: Working
- ❌ Withdrawal: Not implemented (reverts)
- **Temporary Solution**: LP tokens are sent to recipient, can be withdrawn manually

---

## Integration Flow

### Execution Order

```
1. Connect to network
   ↓
2. Check DeFi protocol balances
   ↓
3. Withdraw from DeFi protocols
   ├─ LayerBank (Scroll)
   ├─ SyncSwap (zkSync ERA)
   └─ Swapr (Arbitrum)
   ↓
4. Wait 60 seconds for settlement
   ↓
5. Collect standard ERC-20 tokens
   ↓
6. Collect native token (ETH, BNB, etc.)
```

### Why 60-Second Wait?

After DeFi withdrawals, we wait 60 seconds to ensure:
1. **Settlement**: Transactions are confirmed on-chain
2. **State Update**: Contract state reflects new balances
3. **No Race Conditions**: Prevents trying to collect tokens before they arrive
4. **Network Propagation**: RPC nodes sync with latest state

### Network-Specific Considerations

| Network | Protocol | Special Handling |
|---------|----------|-----------------|
| Scroll | LayerBank | Standard ERC-20 flow after withdrawal |
| zkSync ERA | SyncSwap | No EIP-1559, higher gas limits (500k) |
| Arbitrum | Swapr | Custom gas limit (100k), L1 Data Fee |

---

## Adding New DeFi Protocols

### Step 1: Add Configuration

```python
YOUR_PROTOCOL_CONFIG = {
    "NetworkName": {
        "contract_address": "0x...",
        "pools": [
            {
                "name": "TokenA/TokenB",
                "address": "0x...",
                "token0": "0x...",
                "token1": "0x..."
            }
        ]
    }
}
```

### Step 2: Add ABI

```python
YOUR_PROTOCOL_ABI = json.loads('''[
    {
        "name": "balanceOf",
        "inputs": [{"type": "address"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "name": "withdraw",
        "inputs": [...],
        "outputs": [...],
        "stateMutability": "nonpayable"
    }
]''')
```

### Step 3: Implement Detection Function

```python
def check_your_protocol_balance(w3, address, network_name, lock):
    if network_name not in YOUR_PROTOCOL_CONFIG:
        return False
    
    config = YOUR_PROTOCOL_CONFIG[network_name]
    found = False
    
    for pool in config["pools"]:
        # Check balance
        contract = w3.eth.contract(address=pool["address"], abi=YOUR_PROTOCOL_ABI)
        balance = contract.functions.balanceOf(address).call()
        
        if balance > 0:
            safe_print(f"Found {balance} LP tokens in {pool['name']}", lock)
            found = True
    
    return found
```

### Step 4: Implement Withdrawal Function

```python
def withdraw_from_your_protocol(w3, account, network_name, lock):
    if network_name not in YOUR_PROTOCOL_CONFIG:
        return
    
    config = YOUR_PROTOCOL_CONFIG[network_name]
    
    for pool in config["pools"]:
        # Get balance
        contract = w3.eth.contract(address=pool["address"], abi=YOUR_PROTOCOL_ABI)
        balance = contract.functions.balanceOf(account.address).call()
        
        if balance == 0:
            continue
        
        # Build transaction
        tx = contract.functions.withdraw(balance).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        safe_print(f"✓ Withdrew from {pool['name']}", lock)
```

### Step 5: Integrate into Main Flow

```python
# In process_wallet() function, after connecting to network:

# Check DeFi protocols
check_layerbank_balance(w3, address, network_name, lock)
check_syncswap_liquidity(w3, address, network_name, lock)
check_swapr_liquidity(w3, address, network_name, lock)
check_your_protocol_balance(w3, address, network_name, lock)  # Add here

# Withdraw from DeFi protocols
withdraw_from_layerbank(w3, account, network_name, lock)
withdraw_from_syncswap(w3, account, network_name, lock)
withdraw_from_swapr(w3, account, network_name, lock)
withdraw_from_your_protocol(w3, account, network_name, lock)  # Add here

# Wait for settlement
time.sleep(60)
```

---

## Best Practices

### 1. Always Check Balances First
Don't blindly attempt withdrawals. Check if user has assets in protocol first.

### 2. Handle Dust Gracefully
Set minimum thresholds to avoid:
- High gas costs for tiny amounts
- Arithmetic underflow errors
- Failed transactions

### 3. Use Appropriate Gas Limits
- **Simple transfers**: 21,000
- **ERC-20 approvals**: 50,000-100,000
- **DeFi withdrawals**: 200,000-500,000
- **zkSync transactions**: 500,000+

### 4. Wait for Settlement
After DeFi withdrawals, wait before collecting standard tokens:
```python
time.sleep(60)  # Adjust based on network speed
```

### 5. Network-Specific Handling
- **zkSync ERA**: No EIP-1559, higher gas limits
- **Arbitrum**: Custom gas limit (100k), L1 Data Fee
- **Scroll**: Special L1 Fee calculation

### 6. Error Handling
```python
try:
    withdraw_from_protocol()
except Exception as e:
    safe_print(f"⚠ Withdrawal failed: {str(e)}", lock)
    # Continue to next step (don't block entire process)
```

### 7. Test with Small Amounts
Before adding new protocols:
1. Test on testnet
2. Test with small amounts on mainnet
3. Verify tokens are received
4. Check gas costs are reasonable

---

## Troubleshooting

### "Contract execution reverted"
- Check if wallet has approved spending
- Verify contract addresses are correct
- Ensure wallet has sufficient assets in protocol
- Check if protocol has withdrawal restrictions

### "Gas estimation failed"
- Manually set gas limit
- Check if transaction would succeed (call vs transact)
- Verify wallet has enough native token for gas

### "Arithmetic underflow"
- Add dust filters (minimum balance checks)
- Use `min_amounts = [0, 0]` for withdrawals
- Check decimal calculations

### "Transaction timeout"
- Increase timeout parameter
- Check network congestion
- Verify RPC endpoint is responsive

### "Wrong token amounts"
- Verify decimal handling (6 vs 18 decimals)
- Check reserve calculations
- Ensure using correct token addresses

---

## Future Improvements

- [ ] Complete Swapr withdrawal implementation
- [ ] Add Uniswap V2/V3 support
- [ ] Add Curve Finance support
- [ ] Add Balancer support
- [ ] Add Aave/Compound lending protocols
- [ ] Add cross-chain bridge detection
- [ ] Add NFT collection (ERC-721/ERC-1155)
- [ ] Add staking position detection

---

## References

- **LayerBank Docs**: https://docs.layerbank.finance
- **SyncSwap Docs**: https://syncswap.xyz/docs
- **Swapr Docs**: https://dxdao.eth.limo/swapr
- **Web3.py Docs**: https://web3py.readthedocs.io
