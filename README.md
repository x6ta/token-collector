# 🪙 Multi-Chain EVM Token Collector

Automated tool for collecting tokens and native currencies from multiple EVM wallets across 15+ blockchain networks with integrated DeFi protocol support.

## ✨ Features

### 🌐 Network Support (15 Chains)
- **Layer 1**: Ethereum, BNB Chain, Avalanche, Polygon
- **Layer 2**: zkSync ERA, BASE, Optimism, Arbitrum, Arbitrum Nova, Scroll, Linea, ZORA
- **Other**: CELO, GNOSIS, CORE

### 🏦 DeFi Integration
- **LayerBank** (Scroll): Automatic withdrawal from 8 lending markets
- **SyncSwap** (zkSync ERA): LP token withdrawal and unwrapping
- **Swapr** (Arbitrum): DEX liquidity management

### 🚀 Advanced Features
- **Multi-threading**: Process up to 25 wallets simultaneously
- **Auto Gas Refuel**: Automatically refuel wallets with insufficient gas
- **Smart Gas Calculation**: Network-specific gas optimization (L1, L2, zkSync)
- **Dust Filter**: Skip positions below minimum thresholds
- **Real-time Price Tracking**: Automatic token price updates
- **Safe Mode**: Extensive error handling and retry logic

---

## 📋 Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, Linux, macOS
- **Dependencies**: See `requirements.txt`

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Clone repository
git clone https://github.com/yourusername/token-collector.git
cd token-collector

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configuration

#### Option A: Direct Configuration (Quick Start)

Edit `token_collector.py` lines 15-17:

```python
RECIPIENT_ADDRESS = "0xYourRecipientAddressHere"  # Where tokens will be sent
RECIPIENT_ADDRESS_KEY = "YOUR_PRIVATE_KEY_HERE"    # For auto-refuel (optional)
DONOR_FILE = "DONOR.txt"                           # File with donor wallets
```

#### Option B: Environment Variables (Recommended for Production)

```bash
# Copy example config
cp .env.example .env

# Edit .env file with your settings
nano .env
```

### 3️⃣ Add Donor Wallets

Create `DONOR.txt` with your private keys (one per line):

```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```

> ⚠️ **Security Warning**: Never commit `DONOR.txt` to Git! It's included in `.gitignore`.

### 4️⃣ Run

```bash
python token_collector.py
```

---

## 🛠️ Configuration Options

### Basic Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RECIPIENT_ADDRESS` | Required | Destination wallet address |
| `RECIPIENT_ADDRESS_KEY` | Optional | Private key for auto-refuel |
| `MIN_BALANCE_USD` | `0.05` | Minimum balance to process (USD) |
| `AUTO_REFUEL_GAS` | `True` | Enable automatic gas refueling |
| `MIN_GAS_REFUEL_AMOUNT` | `0.002` | Minimum refuel amount (native token) |

### Performance Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_PARALLEL_WALLETS` | `25` | Concurrent wallet processing (1-25) |
| `PAUSE_BETWEEN_WALLETS` | `7` | Delay between wallets (seconds) |
| `GAS_PRICE_MULTIPLIER` | `1.2` | Gas price buffer (20% extra) |

### Network-Specific Gas Multipliers

- **L1 Networks** (Ethereum, BNB, etc.): `1.3x`
- **L2 Networks** (Optimism, BASE, Arbitrum, ZORA): `2.5x` (includes L1 Data Fee)
- **zkSync ERA**: Custom gas calculation
- **Scroll**: Special L1 Data Fee calculation

---

## 📊 Supported Tokens

### By Network (40+ tokens total)

<details>
<summary><b>zkSync ERA</b> (7 tokens)</summary>

- USDC, USDT, DAI, WETH, ZK, BUSD, EURA
</details>

<details>
<summary><b>BASE</b> (5 tokens)</summary>

- USDC, USDbC, WETH, DAI, AERO
</details>

<details>
<summary><b>Ethereum</b> (5 tokens)</summary>

- USDC, USDT, DAI, WETH, WBTC
</details>

<details>
<summary><b>And 12+ more networks...</b></summary>

See `token_collector.py` NETWORKS configuration for complete list.
</details>

---

## 🏦 DeFi Protocols

### LayerBank (Scroll Network)

Automatically withdraws from lending markets:
- lUSDC, lUSDT, lDAI, lWBTC, lETH, lwrsETH, lWSTETH, lweETH

**How it works:**
1. Detects lToken balances
2. Calculates underlying token amounts
3. Executes `redeemUnderlying()` withdrawal
4. Waits 60 seconds for settlement

### SyncSwap (zkSync ERA)

LP token management:
- ETH/USDC Pool
- USDC/USDT Pool

**Features:**
- Automatic decimals detection (USDC: 6, ETH: 18)
- Dust filter (< 0.0001 LP tokens)
- Pool share calculation
- Single-transaction unwrapping

### Swapr (Arbitrum)

DEX liquidity management:
- USDC/WETH Pool

**Status:** Approval working, withdrawal in development

---

## 📖 How It Works

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Load donor wallets from DONOR.txt                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Process each network (15 networks)                      │
│    ├─ Connect to RPC                                        │
│    ├─ Check wallet balances                                 │
│    └─ Calculate gas requirements                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DeFi Protocol Withdrawals (if applicable)               │
│    ├─ LayerBank: Redeem lTokens → Underlying tokens        │
│    ├─ SyncSwap: Burn LP → Native tokens                    │
│    └─ Swapr: Remove liquidity                              │
│    └─ Wait 60 seconds for settlement                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Token Transfers                                          │
│    ├─ Check balance > MIN_BALANCE_USD                       │
│    ├─ Calculate gas cost                                    │
│    ├─ Auto-refuel if insufficient gas                       │
│    └─ Transfer ERC-20 tokens                                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Native Token Transfer                                    │
│    ├─ Reserve gas for transaction                           │
│    ├─ Send remaining balance                                │
│    └─ Multi-signature support (zkSync)                      │
└─────────────────────────────────────────────────────────────┘
```

### Gas Optimization

#### L1 Networks (Ethereum, BNB, Polygon, etc.)
```python
gas_limit = 21000  # Standard ETH transfer
final_gas = gas_limit * gas_price * 1.3  # 30% buffer
```

#### L2 Networks (Optimism, BASE, Arbitrum, ZORA)
```python
gas_limit = 21000
l1_data_fee = estimated_from_rpc()  # Variable
final_gas = (gas_limit * gas_price + l1_data_fee) * 2.5  # 150% buffer
```

#### zkSync ERA (Special)
```python
gas_limit = 500000  # Higher for EIP-712
gas_price = w3.eth.gas_price
# No EIP-1559 (no maxFeePerGas)
```

---

## ⚠️ Important Warnings

### 🔐 Security

- **Never share `DONOR.txt`** - Contains private keys
- **Use test wallets first** - Verify on testnet before mainnet
- **Keep recipient key secure** - Only needed for auto-refuel
- **Audit RPC endpoints** - Use trusted RPC providers
- **Review transactions** - Check recipient address before running

### 💰 Cost Considerations

- **Gas fees vary by network**: L2s cheaper than L1s
- **DeFi withdrawals**: More expensive than simple transfers
- **Auto-refuel**: Consumes gas from recipient wallet
- **Price volatility**: Gas costs fluctuate with network congestion

### 🐛 Known Limitations

- **No price validation**: Doesn't verify token market prices
- **Basic dust handling**: Fixed USD threshold (`MIN_BALANCE_USD`)
- **RPC rate limits**: May need paid RPC for high volume
- **Swapr withdrawal**: Partial implementation (approval only)

---

## 🔧 Troubleshooting

### "Insufficient funds for gas"

**Solution**: Enable auto-refuel or manually add gas to donor wallets
```python
AUTO_REFUEL_GAS = True
MIN_GAS_REFUEL_AMOUNT = 0.002  # Adjust as needed
```

### "Connection timeout" or "RPC error"

**Solution**: Check RPC endpoints, consider using paid RPCs
```python
# Replace in NETWORKS configuration
"rpc": "https://your-reliable-rpc-here"
```

### "LP balance too small" (SyncSwap)

**Cause**: Dust positions below 0.0001 LP tokens  
**Behavior**: Automatically skipped (expected)

### "Arithmetic underflow" (zkSync/SyncSwap)

**Cause**: Trying to withdraw dust from pools  
**Fix**: Already implemented - positions < 0.0001 LP are filtered

### "Transaction reverted"

**Solutions**:
1. Check gas limit settings for network
2. Verify token contract addresses
3. Ensure wallet has approval for DeFi protocols
4. Review error message for specific revert reason

---

## 🧪 Testing

### Testnet Mode (Recommended First Run)

1. **Replace RPC endpoints** with testnet RPCs
2. **Use testnet tokens** - Get from faucets
3. **Test with 1-2 wallets** before full batch

### Validation Checklist

- [ ] Private keys load correctly from `DONOR.txt`
- [ ] Recipient address is correct
- [ ] RPC connections successful for all networks
- [ ] Token balances detected accurately
- [ ] Gas calculations reasonable (check first wallet manually)
- [ ] DeFi withdrawals complete successfully
- [ ] Tokens arrive at recipient address
- [ ] No stuck transactions

---

## 📚 Advanced Usage

### Custom Token Addition

Edit `NETWORKS` dictionary in `token_collector.py`:

```python
"NetworkName": {
    "rpc": "https://rpc-endpoint.com",
    "chain_id": 123456,
    "native_symbol": "ETH",
    "tokens": [
        {
            "symbol": "TOKEN",
            "address": "0x1234567890abcdef1234567890abcdef12345678"
        }
    ]
}
```

### Custom RPC Endpoints

**Free Options:**
- [Chainlist.org](https://chainlist.org) - Public RPCs
- [Ankr Public RPCs](https://www.ankr.com/rpc/)
- [LlamaNodes](https://llamanodes.com)

**Paid Options (Better reliability):**
- [Alchemy](https://www.alchemy.com)
- [Infura](https://www.infura.io)
- [QuickNode](https://www.quicknode.com)

### Adjusting Multithreading

```python
# Conservative (more stable)
MAX_PARALLEL_WALLETS = 5
PAUSE_BETWEEN_WALLETS = 15

# Aggressive (faster, more RPC load)
MAX_PARALLEL_WALLETS = 25
PAUSE_BETWEEN_WALLETS = 3
```

---

## 📈 Performance Benchmarks

**Test Setup**: 10 wallets, 15 networks, ~50 tokens per wallet

| Threads | Total Time | RPC Calls | Avg. per Wallet |
|---------|-----------|-----------|-----------------|
| 1       | ~45 min   | ~1500     | 4.5 min         |
| 5       | ~12 min   | ~1500     | 1.2 min         |
| 25      | ~3 min    | ~1500     | 18 sec          |

> Note: Times vary based on RPC latency and network congestion

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Areas for Improvement

- [ ] Add more DeFi protocols (Uniswap, Curve, etc.)
- [ ] Implement Swapr withdrawal completion
- [ ] Add testnet support toggle
- [ ] Create GUI interface
- [ ] Add token price API integration
- [ ] Support for NFT collection
- [ ] Transaction history export

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚖️ Disclaimer

**USE AT YOUR OWN RISK**

- This software is provided "as-is" without warranty
- Always verify recipient addresses before running
- Test with small amounts first
- Author not responsible for lost funds, errors, or misuse
- Ensure compliance with local regulations
- Not financial advice

---

## 📧 Contact

Created by **@nakleiro**

- GitHub: [@nakleiro](https://github.com/nakleiro)
- Issues: [GitHub Issues](https://github.com/nakleiro/token-collector/issues)

---

## 🙏 Acknowledgments

- Web3.py team for excellent library
- EVM network teams for public RPCs
- DeFi protocols for open-source contracts
- Community contributors

---

## 📊 Project Stats

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Networks](https://img.shields.io/badge/Networks-15-orange.svg)
![DeFi](https://img.shields.io/badge/DeFi-3_Protocols-purple.svg)

---

**⭐ Star this repo if it helped you!**
