# Network Details

## Supported Networks (15 Total)

### Layer 1 Networks

#### Ethereum Mainnet
- **Chain ID**: 1
- **Native Token**: ETH
- **RPC**: https://eth.llamarpc.com
- **Tokens**: USDC, USDT, DAI, WETH, WBTC
- **Gas Multiplier**: 1.3x

#### BNB Chain (Binance Smart Chain)
- **Chain ID**: 56
- **Native Token**: BNB
- **RPC**: https://bsc-dataseed.binance.org
- **Tokens**: USDC, USDT, BUSD, WETH, EURA, BTC.b, STG, LZ-agEUR
- **Gas Multiplier**: 1.3x

#### Polygon PoS
- **Chain ID**: 137
- **Native Token**: MATIC
- **RPC**: https://polygon-rpc.com
- **Tokens**: USDC, USDT, DAI, BTC.b, STG, WETH, USDC(Bridged), EURA
- **Gas Multiplier**: 1.3x

#### Avalanche C-Chain
- **Chain ID**: 43114
- **Native Token**: AVAX
- **RPC**: https://api.avax.network/ext/bc/C/rpc
- **Tokens**: USDC, USDT, BTC.b, EURA, WETH.e, STG
- **Gas Multiplier**: 1.3x

#### GNOSIS Chain
- **Chain ID**: 100
- **Native Token**: xDAI
- **RPC**: https://rpc.gnosischain.com
- **Tokens**: EURA, LZ-agEUR
- **Gas Multiplier**: 1.3x

#### CORE
- **Chain ID**: 1116
- **Native Token**: CORE
- **RPC**: https://rpc.coredao.org
- **Tokens**: USDT, BTC.b
- **Gas Multiplier**: 1.3x

---

### Layer 2 Networks

#### zkSync ERA
- **Chain ID**: 324
- **Native Token**: ETH
- **RPC**: https://mainnet.era.zksync.io
- **Tokens**: USDC, USDT, DAI, WETH, ZK, BUSD, EURA
- **Gas Handling**: Custom (EIP-712 signatures)
- **Gas Limit**: 500,000 (higher for zkSync transactions)
- **DeFi**: SyncSwap integration

#### BASE (Coinbase L2)
- **Chain ID**: 8453
- **Native Token**: ETH
- **RPC**: https://mainnet.base.org
- **Tokens**: USDC, USDbC (Bridged), WETH, DAI, AERO
- **Gas Multiplier**: 2.5x (includes L1 Data Fee)

#### Optimism
- **Chain ID**: 10
- **Native Token**: ETH
- **RPC**: https://mainnet.optimism.io
- **Tokens**: USDC, USDC(Bridged), USDT, WETH, DAI
- **Gas Multiplier**: 2.5x (includes L1 Data Fee)

#### Arbitrum One
- **Chain ID**: 42161
- **Native Token**: ETH
- **RPC**: https://arb1.arbitrum.io/rpc
- **Tokens**: USDC, USDC(Bridged), USDT, WETH, DAI, STG, ARB
- **Gas Multiplier**: 2.5x (includes L1 Data Fee)
- **Gas Limit**: 100,000 (custom for Arbitrum)
- **DeFi**: Swapr integration

#### Arbitrum Nova
- **Chain ID**: 42170
- **Native Token**: ETH
- **RPC**: https://nova.arbitrum.io/rpc
- **Tokens**: (To be added)
- **Gas Multiplier**: 2.5x
- **Gas Limit**: 100,000 (custom for Arbitrum)
- **Note**: Gaming and social applications focused

#### Scroll
- **Chain ID**: 534352
- **Native Token**: ETH
- **RPC**: https://rpc.scroll.io
- **Tokens**: USDC, USDT, WETH, DAI, wrsETH
- **Gas Multiplier**: Special L1 Data Fee calculation
- **DeFi**: LayerBank integration (8 lending markets)

#### Linea
- **Chain ID**: 59144
- **Native Token**: ETH
- **RPC**: https://rpc.linea.build
- **Tokens**: USDC, USDT, WETH, LINEA
- **Gas Multiplier**: 2.5x

#### ZORA
- **Chain ID**: 7777777
- **Native Token**: ETH
- **RPC**: https://rpc.zora.energy
- **Tokens**: (To be added)
- **Gas Multiplier**: 2.5x (includes L1 Data Fee)
- **Note**: NFT and creator-focused network

---

### Other Networks

#### CELO
- **Chain ID**: 42220
- **Native Token**: CELO
- **RPC**: https://forno.celo.org
- **Tokens**: USDC, USDT, EURA, WETH, LZ-agEUR
- **Gas Multiplier**: 1.3x
- **Note**: Mobile-first blockchain

---

## Gas Calculation Methods

### L1 Networks (Standard)
```python
gas_cost = gas_limit * gas_price * 1.3
```
- **Networks**: Ethereum, BNB Chain, Polygon, Avalanche, GNOSIS, CORE, CELO
- **Gas Limit**: 21,000 (standard ETH transfer)
- **Multiplier**: 1.3x (30% buffer)

### L2 Networks (OP Stack)
```python
base_fee = gas_limit * gas_price
l1_data_fee = estimated_from_rpc()
total_cost = (base_fee + l1_data_fee) * 2.5
```
- **Networks**: Optimism, BASE, ZORA
- **Gas Limit**: 21,000
- **Multiplier**: 2.5x (150% buffer for volatility)
- **L1 Data Fee**: Variable, fetched from RPC

### Arbitrum Networks
```python
base_fee = 100000 * gas_price  # Higher gas limit
l1_data_fee = estimated_from_rpc()
total_cost = (base_fee + l1_data_fee) * 2.5
```
- **Networks**: Arbitrum One, Arbitrum Nova
- **Gas Limit**: 100,000 (custom)
- **Multiplier**: 2.5x

### Scroll (Special)
```python
base_fee = gas_limit * gas_price
l1_data_fee = w3.eth.get_block('latest')['baseFeePerGas'] * transaction_size * 16
total_cost = base_fee + l1_data_fee
```
- **Network**: Scroll
- **Custom L1 Fee Calculation**: Uses base fee from block

### zkSync ERA (Unique)
```python
gas_limit = 500000  # Much higher for EIP-712
gas_price = w3.eth.gas_price  # No EIP-1559
total_cost = gas_limit * gas_price * 1.2
```
- **Network**: zkSync ERA
- **EIP-712 Signatures**: Required for transactions
- **No maxFeePerGas**: Uses legacy gas price

---

## Alternative RPC Endpoints

### Free Public RPCs

#### Multi-Network Providers
- **Chainlist.org**: https://chainlist.org (comprehensive list)
- **LlamaNodes**: https://llamanodes.com
- **Public Node**: https://www.publicnode.com

#### Network-Specific
- **Ethereum**: 
  - https://cloudflare-eth.com
  - https://rpc.ankr.com/eth
  
- **Arbitrum**: 
  - https://arbitrum.llamarpc.com
  
- **Optimism**: 
  - https://optimism.llamarpc.com
  
- **Polygon**: 
  - https://polygon.llamarpc.com

### Paid RPC Providers (Recommended for Production)

#### Alchemy
- **URL**: https://www.alchemy.com
- **Features**: High reliability, analytics, webhooks
- **Free Tier**: 300M compute units/month
- **Networks**: Most major chains

#### Infura
- **URL**: https://www.infura.io
- **Features**: Enterprise-grade, IPFS support
- **Free Tier**: 100K requests/day
- **Networks**: Ethereum, Polygon, Optimism, Arbitrum

#### QuickNode
- **URL**: https://www.quicknode.com
- **Features**: Global infrastructure, low latency
- **Free Tier**: Limited
- **Networks**: 20+ chains

#### Ankr
- **URL**: https://www.ankr.com/rpc/
- **Features**: Multi-chain, load balancing
- **Free Tier**: Available
- **Networks**: 50+ chains

---

## Network-Specific Notes

### zkSync ERA
- Uses EIP-712 typed signatures instead of standard transactions
- Higher gas limits required (500,000 vs 21,000)
- No EIP-1559 support (no maxFeePerGas)
- SyncSwap DEX integration for LP tokens

### Arbitrum (One & Nova)
- Custom gas limit of 100,000 (vs 21,000 standard)
- L1 Data Fee can be significant
- Nova optimized for gaming/social (lower fees)
- Swapr DEX integration on Arbitrum One

### Scroll
- Special L1 Data Fee calculation using block base fee
- LayerBank lending protocol integration
- 8 lending markets supported (lETH, lUSDC, lwstETH, etc.)

### ZORA
- NFT and creator-focused chain
- Very low fees compared to Ethereum L1
- OP Stack architecture (similar to BASE/Optimism)

### BASE
- Coinbase's L2 network
- Growing DeFi ecosystem
- Low fees, high throughput
- Native USDC support

---

## Adding Custom Networks

To add a new network, edit `token_collector.py`:

```python
"YourNetwork": {
    "rpc": "https://rpc.yournetwork.com",
    "chain_id": 12345,
    "native_symbol": "YTK",
    "tokens": [
        {
            "symbol": "USDC",
            "address": "0x..."
        }
    ]
}
```

**Important**: Also update gas calculation logic if network requires special handling (e.g., L2 with L1 Data Fee).
