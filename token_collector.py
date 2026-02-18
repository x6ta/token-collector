"""
TOKEN COLLECTOR by @nakleiro
"""

from web3 import Web3
from decimal import Decimal
import time
import json
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# ===== НАСТРОЙКИ =====
# ⚠️ ВАЖНО: Замените эти значения на ваши собственные!
RECIPIENT_ADDRESS = "0xYourRecipientAddressHere"  # УКАЖИТЕ АДРЕС ПОЛУЧАТЕЛЯ
RECIPIENT_ADDRESS_KEY = "YOUR_PRIVATE_KEY_HERE"  # ПРИВАТНЫЙ КЛЮЧ получателя (для автопополнения газа, опционально)
DONOR_FILE = "DONOR.txt"  # Файл с приватными ключами донорских кошельков (один ключ на строку)
GAS_PRICE_MULTIPLIER = 1.2  # Множитель для gas price (10% запас)
MIN_BALANCE_USD = 0.05  # Минимальный баланс для обработки (в USD)
AUTO_REFUEL_GAS = True  # Автоматически пополнять gas из RECIPIENT_ADDRESS_KEY
MIN_GAS_REFUEL_AMOUNT = 0.002  # Минимальная сумма для пополнения газа (в нативном токене)

# Настройки многопоточности
MAX_PARALLEL_WALLETS = 25  # Количество кошельков для одновременной обработки (1-10)
PAUSE_BETWEEN_WALLETS = 7  # Пауза между кошельками в секундах

# ERC-20 ABI (минимальный набор для transfer, balanceOf, decimals)
ERC20_ABI = json.loads('''[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]''')

# Конфигурация сетей
NETWORKS = {
    "zkSync ERA": {
        "rpc": "https://mainnet.era.zksync.io",  # Public RPC
        "chain_id": 324,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC(bridged)", "address": "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4"},
            {"symbol": "USD+", "address": "0x8e86e46278518efc1c5ced245cba2c7e3ef11557"},
            {"symbol": "BUSD", "address": "0x2039bb4116b4efc145ec4f0e2ea75012d6c0f181"},
            {"symbol": "LUSD", "address": "0x503234f203fc7eb888eec8513210612a43cf6115"},
            {"symbol": "ZK", "address": "0x5a7d6b2f92c77fad6ccabd7ee0624e64907eaf3e"},
            {"symbol": "WETH", "address": "0x5aea5775959fbc2557cc8789bc1bf90a239d9a91"},
            {"symbol": "WBTC", "address": "0xbbeb516fb02a01611cbbe0453fe3c580d7281011"},
            {"symbol": "USDT", "address": "0x493257fd37edb34451f62edf8d2a0c418852ba4c"},
            {"symbol": "AVAX", "address": "0x6a5279e99ca7786fb13f827fc1fb4f61684933d6"},
            {"symbol": "iZi", "address": "0x16a9494e257703797d747540f01683952547ee5b"},
            {"symbol": "MATIC", "address": "0x28a487240e4d45cff4a2980d334cc933b7483842"},
            {"symbol": "WBTC", "address": "0xbbeb516fb02a01611cbbe0453fe3c580d7281011"},
            {"symbol": "MAV", "address": "0x787c09494ec8bcb24dcaf8659e7d5d69979ee508"},
        ]
    },
    "BASE": {
        "rpc": "https://mainnet.base.org",  # Public RPC
        "chain_id": 8453,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"},
            {"symbol": "DAI", "address": "0x50c5725949a6f0c72e6c4a641f24049a917db0cb"},
            {"symbol": "WETH", "address": "0x4200000000000000000000000000000000000006"},
            {"symbol": "USDbC", "address": "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca"},
            {"symbol": "toby", "address": "0xb8d98a102b0079b69ffbc760c8d857a31653e56e"},
        ]
    },
    "Polygon": {
        "rpc": "https://polygon-rpc.com",  # Public RPC
        "chain_id": 137,
        "native_symbol": "POL",
        "tokens": [
            {"symbol": "USDC", "address": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"},
            {"symbol": "USDT", "address": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"},
            {"symbol": "DAI", "address": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063"},
            {"symbol": "BTC.b", "address": "0x2297aebd383787a160dd0d9f71508148769342e3"},
            {"symbol": "STG", "address": "0x2f6f07cdcf3588944bf4c42ac74ff24bf56e7590"},
            {"symbol": "WETH", "address": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619"},
            {"symbol": "USDC(Bridged)", "address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"},
            {"symbol": "EURA", "address": "0xe0b52e49357fd4daf2c15e02058dce6bc0057db4"},
            {"symbol": "STG", "address": "0x2f6f07cdcf3588944bf4c42ac74ff24bf56e7590"},
            {"symbol": "USDT0", "address": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"},
        ]
    },
    "Scroll": {
        "rpc": "https://rpc.scroll.io",  # Public RPC
        "chain_id": 534352,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0x06efdbff2a14a7c8e15944d1f4a48f9f95f663a4"},
            {"symbol": "USDT", "address": "0xf55bec9cafdbe8730f096aa55dad6d22d44099df"},
            {"symbol": "WETH", "address": "0x5300000000000000000000000000000000000004"},
            {"symbol": "DAI", "address": "0xca77eb3fefe3725dc33bccb54edefc3d9f764f97"},
            {"symbol": "wrsETH", "address": "0xa25b25548b4c98b0c7d3d27dca5d5ca743d68b7f"},
        ]
    },
    "Ethereum": {
        "rpc": "https://eth.llamarpc.com",  # Public RPC
        "chain_id": 1,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"},
            {"symbol": "USDT", "address": "0xdac17f958d2ee523a2206206994597c13d831ec7"},
            {"symbol": "DAI", "address": "0x6b175474e89094c44da98b954eedeac495271d0f"},
            {"symbol": "WETH", "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
            {"symbol": "WBTC", "address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"},
        ]
    },
    "CELO": {
        "rpc": "https://forno.celo.org",  # Public RPC
        "chain_id": 42220,
        "native_symbol": "CELO",
        "tokens": [
            {"symbol": "USDC", "address": "0xceba9300f2b948710d2653dd7b07f33a8b32118c"},
            {"symbol": "USDT", "address": "0x88eec49252c8cbc039dcdb394c0c2ba2f1637ea0"},
            {"symbol": "EURA", "address": "0xc16b81af351ba9e64c1a069e3ab18c244a1e3049"},
            {"symbol": "WETH", "address": "0x122013fd7df1c6f636a5bb8f03108e876548b455"},
            {"symbol": "LZ-agEUR", "address": "0xf1ddcaca7d17f8030ab2eb54f2d9811365efe123"},
        ]
    },
    "Optimism": {
        "rpc": "https://mainnet.optimism.io",  # Public RPC
        "chain_id": 10,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0x0b2c639c533813f4aa9d7837caf62653d097ff85"},
            {"symbol": "USDC(Bridged)", "address": "0x7f5c764cbc14f9669b88837ca1490cca17c31607"},
            {"symbol": "USDT", "address": "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58"},
            {"symbol": "WETH", "address": "0x4200000000000000000000000000000000000006"},
            {"symbol": "DAI", "address": "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1"},
        ]
    },
    "BNB Chain": {
        "rpc": "https://bsc-dataseed.binance.org",  # Public RPC
        "chain_id": 56,
        "native_symbol": "BNB",
        "tokens": [
            {"symbol": "USDC", "address": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"},
            {"symbol": "USDT", "address": "0x55d398326f99059ff775485246999027b3197955"},
            {"symbol": "BUSD", "address": "0xe9e7cea3dedca5984780bafc599bd69add087d56"},
            {"symbol": "WETH", "address": "0x2170ed0880ac9a755fd29b2688956bd959f933f8"},
            {"symbol": "EURA", "address": "0x12f31b73d812c6bb0d735a218c086d44d5fe5f89"},
            {"symbol": "BTC.b", "address": "0x2297aebd383787a160dd0d9f71508148769342e3"},
            {"symbol": "STG", "address": "0xb0d502e938ed5f4df2e681fe6e419ff29631d62b"},
            {"symbol": "LZ-agEUR", "address": "0xe9f183fc656656f1f17af1f2b0df79b8ff9ad8ed"},
        ]
    },
    "Linea": {
        "rpc": "https://rpc.linea.build",  # Public RPC
        "chain_id": 59144,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0x176211869ca2b568f2a7d4ee941e073a821ee1ff"},
            {"symbol": "USDT", "address": "0xa219439258ca9da29e9cc4ce5596924745e12b93"},
            {"symbol": "WETH", "address": "0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f"},
            {"symbol": "LINEA", "address": "0x1789e0043623282d5dcc7f213d703c6d8bafbb04"},
        ]
    },
    "Arbitrum": {
        "rpc": "https://arb1.arbitrum.io/rpc",  # Public RPC
        "chain_id": 42161,
        "native_symbol": "ETH",
        "tokens": [
            {"symbol": "USDC", "address": "0xaf88d065e77c8cc2239327c5edb3a432268e5831"},
            {"symbol": "USDC(Bridged)", "address": "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8"},
            {"symbol": "USDT", "address": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"},
            {"symbol": "WETH", "address": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"},
            {"symbol": "DAI", "address": "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1"},
            {"symbol": "STG", "address": "0x6694340fc020c5e6b96567843da2df01b2ce1eb6"},
            {"symbol": "ARB", "address": "0x912ce59144191c1204e64559fe8253a0e49e6548"},
        ]
    },
    "Avalanche": {
        "rpc": "https://api.avax.network/ext/bc/C/rpc",  # Public RPC
        "chain_id": 43114,
        "native_symbol": "AVAX",
        "tokens": [
            {"symbol": "USDC", "address": "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e"},
            {"symbol": "USDT", "address": "0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7"},
            {"symbol": "BTC.b", "address": "0x152b9d0fdc40c096757f570a51e494bd4b943e50"},
            {"symbol": "EURA", "address": "0xaec8318a9a59baeb39861d10ff6c7f7bf1f96c57"},
            {"symbol": "WETH.e", "address": "0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab"},
            {"symbol": "STG", "address": "0x2f6f07cdcf3588944bf4c42ac74ff24bf56e7590"},
        ]
    },
    "GNOSIS": {
        "rpc": "https://rpc.gnosischain.com",  # Public RPC
        "chain_id": 100,
        "native_symbol": "xDAI",
        "tokens": [
            {"symbol": "EURA", "address": "0x4b1e2c2762667331bc91648052f646d1b0d35984"},
            {"symbol": "LZ-agEUR", "address": "0xfa5ed56a203466cbbc2430a43c66b9d8723528e7"},
        ]
    },
    "CORE": {
        "rpc": "https://rpc.coredao.org",  # Public RPC
        "chain_id": 1116,
        "native_symbol": "CORE",
        "tokens": [
            {"symbol": "USDT", "address": "0x900101d06a7426441ae63e9ab3b9b0f63be145f1"},
            {"symbol": "BTC.b", "address": "0x2297aebd383787a160dd0d9f71508148769342e3"},
        ]
    },
    "Arbitrum Nova": {
        "rpc": "https://nova.arbitrum.io/rpc",  # Public RPC
        "chain_id": 42170,
        "native_symbol": "ETH",
        "tokens": [
            # Arbitrum Nova - сеть с низкими комиссиями для gaming и social приложений
            # Токены будут добавлены по мере необходимости
        ]
    },
    "ZORA": {
        "rpc": "https://rpc.zora.energy",
        "chain_id": 7777777,
        "native_symbol": "ETH",
        "tokens": [
            # ZORA - сеть для NFT и креаторов
            # Токены будут добавлены по мере необходимости
        ]
    },
}

# ===== LayerBank Configuration =====
LAYERBANK_CONFIG = {
    "Scroll": {
        "core_address": "0xEC53c830f4444a8A56455c6836b5D2aA794289Aa",
        "ltokens": {
            "lETH": "0x274C3795dadfEbf562932992bF241ae087e0a98C",
            "lUSDC": "0x0D8F8e271DD3f2fC58e5716d3Ff7041dBe3F0688",
            "lwstETH": "0xB6966083c7b68175B4BF77511608AEe9A80d2Ca4",
            "lwrsETH": "0xec0AD3f43E85fc775a9C9b77f0F0aA7FE5A587d6",
            "lSTONE": "0xE5C40a3331d4Fb9A26F5e48b494813d977ec0A8E",
            "luniETH": "0xBd1d62e74c6d165ccae6d161588a3768023DCc18",
            "lWBTC": "0xc40D6957B8110eC55f0F1A20d7D3430e1d8Aa4cf",
            "lUSDT": "0xE0Cee49cC3C9d047C0B175943ab6FCC3c4F40fB0",
        }
    }
}

# ===== SyncSwap Configuration =====
SYNCSWAP_CONFIG = {
    "zkSync ERA": {
        "router_address": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",  # SyncSwap Classic Router
        "pool_factory": "0xf2DAd89f2788a8CD54625C60b55cD3d2D0ACa7Cb",  # Classic Pool Factory
        "vault_address": "0x621425a1Ef6abE91058E9712575dcc4258F8d091",  # SyncSwap Vault
        "min_liquidity_usd": 0.5,  # Минимальная ликвидность для вывода ($0.50)
        # Популярные пулы SyncSwap на zkSync ERA (только проверенные)
        "pools": [
            # ETH/USDC Pool (ИСПРАВЛЕНО: порядок токенов)
            {
                "name": "ETH/USDC",
                "pool_address": "0x80115c708E12eDd42E504c1cD52Aea96C547c05c",
                "token0": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",  # USDC (token0)
                "token1": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",  # WETH (token1)
            },
            # ETH/USDT Pool (ИСПРАВЛЕНО: порядок токенов)
            {
                "name": "ETH/USDT",
                "pool_address": "0xd3D91634Cf4C04aD1B76cE2c06F7385A897F54D3",
                "token0": "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C",  # USDT (token0)
                "token1": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",  # WETH (token1)
            },
        ]
    }
}

# ===== Swapr Configuration =====
SWAPR_CONFIG = {
    "Arbitrum": {
        "router_address": "0x530476d5583724A89c8841eB6Da76E7Af4C0F17E",  # Swapr Router на Arbitrum
        "factory_address": "0x359F20Ad0F42D75a5077e65F30274cABe6f4F01a",  # Swapr Factory на Arbitrum
        "min_liquidity_usd": 0.5,  # Минимальная ликвидность для вывода ($0.50)
        # Рабочие пулы Swapr на Arbitrum
        "pools": [
            # ETH/USDC Pool (рабочий адрес)
            {
                "name": "ETH/USDC",
                "pool_address": "0xdb86e7fe4074e3c29d2fd0ed1d104c00e11a196b",
                "token0": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC.e
                "token1": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
            },
        ]
    }
}

# ===== SyncSwap ABIs =====
# LP Token (ERC-20) ABI - используется для проверки баланса LP токенов
SYNCSWAP_LP_ABI = json.loads('''[
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint256"},
            {"name": "_reserve1", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# SyncSwap Router ABI - для вывода ликвидности
SYNCSWAP_ROUTER_ABI = json.loads('''[
    {
        "inputs": [
            {"name": "pool", "type": "address"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "minAmounts", "type": "uint256[]"},
            {"name": "callback", "type": "address"},
            {"name": "callbackData", "type": "bytes"}
        ],
        "name": "burnLiquidity",
        "outputs": [
            {"name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "pool", "type": "address"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "minAmounts", "type": "uint256[]"},
            {"name": "callback", "type": "address"},
            {"name": "callbackData", "type": "bytes"}
        ],
        "name": "burnLiquiditySingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]''')

# LayerBank ABIs
LTOKEN_ABI = json.loads('''[
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "exchangeRate",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# ===== Swapr ABIs =====
# Swapr Pair (LP Token) ABI - основан на Uniswap V2
SWAPR_PAIR_ABI = json.loads('''[
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# Swapr Router ABI - для вывода ликвидности (совместим с Uniswap V2)
SWAPR_ROUTER_ABI = json.loads('''[
    {
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "amountAMin", "type": "uint256"},
            {"name": "amountBMin", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "removeLiquidity",
        "outputs": [
            {"name": "amountA", "type": "uint256"},
            {"name": "amountB", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "token", "type": "address"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "amountTokenMin", "type": "uint256"},
            {"name": "amountETHMin", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "removeLiquidityETH",
        "outputs": [
            {"name": "amountToken", "type": "uint256"},
            {"name": "amountETH", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]''')

LAYERBANK_CORE_ABI = json.loads('''[
    {
        "inputs": [
            {"name": "lToken", "type": "address"},
            {"name": "lAmount", "type": "uint256"}
        ],
        "name": "redeemToken",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]''')


def load_private_keys():
    """Загрузка приватных ключей из файла"""
    try:
        with open(DONOR_FILE, 'r') as f:
            keys = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        print(f"✓ Загружено {len(keys)} приватных ключей")
        return keys
    except FileNotFoundError:
        print(f"✗ Файл {DONOR_FILE} не найден!")
        return []


def get_token_balance(w3, token_address, wallet_address):
    """Получить баланс ERC-20 токена"""
    try:
        token_address = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        balance = contract.functions.balanceOf(wallet_address).call()
        decimals = contract.functions.decimals().call()
        return balance, decimals
    except Exception as e:
        print(f"  ✗ Ошибка получения баланса токена {token_address}: {e}")
        return 0, 18


def estimate_token_transfer_cost(w3, token_address, from_address, to_address, amount):
    """Оценить стоимость перевода токена в нативной валюте"""
    try:
        token_address = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Оценка gas
        gas_estimate = contract.functions.transfer(to_address, amount).estimate_gas({
            'from': from_address
        })
        
        # Получение gas price
        gas_price = w3.eth.gas_price
        
        # Общая стоимость в wei
        total_cost = gas_estimate * gas_price
        
        return total_cost, gas_estimate, gas_price
    except Exception as e:
        print(f"  ✗ Ошибка оценки стоимости перевода: {e}")
        return None, None, None


def send_token(w3, private_key, token_address, recipient, amount, chain_id, network_name=""):
    """Отправить ERC-20 токен"""
    try:
        account = w3.eth.account.from_key(private_key)
        token_address = Web3.to_checksum_address(token_address)
        recipient = Web3.to_checksum_address(recipient)
        
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Построение транзакции
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
        
        # Специальный gas limit для разных сетей
        if network_name in ["zkSync ERA"]:
            gas_limit = 200000  # zkSync требует больше газа
        elif network_name in ["Arbitrum", "Optimism", "Scroll"]:
            gas_limit = 150000  # L2 сети с L1 Data Fee
        else:
            gas_limit = 100000  # Стандартный лимит
        
        transaction = contract.functions.transfer(recipient, amount).build_transaction({
            'chainId': chain_id,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        # Пробуем оценить gas (может не сработать для некоторых сетей)
        try:
            estimated_gas = w3.eth.estimate_gas(transaction)
            if estimated_gas > gas_limit:
                transaction['gas'] = int(estimated_gas * 1.2)
        except:
            pass  # Используем фиксированный лимит
        
        # Подпись и отправка
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        print(f"  ✓ Транзакция отправлена: {tx_hash.hex()}")
        
        # Ожидание подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"  ✓ Транзакция подтверждена!")
            return True
        else:
            print(f"  ✗ Транзакция не удалась")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка отправки токена: {e}")
        return False


def send_native(w3, private_key, recipient, amount, chain_id, network_name=""):
    """Отправить нативную валюту"""
    try:
        account = w3.eth.account.from_key(private_key)
        recipient = Web3.to_checksum_address(recipient)
        
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Специальный gas limit для разных сетей
        if network_name in ["zkSync ERA"]:
            gas_limit = 250000  # zkSync ERA требует большой лимит (реальное использование ~100-150k)
        elif network_name in ["Arbitrum", "Arbitrum Nova"]:
            gas_limit = 100000  # Arbitrum и Nova требуют больше газа
        else:
            gas_limit = 21000  # Стандартный лимит
        
        # Для zkSync ERA используем EIP-1559
        if network_name in ["zkSync ERA"]:
            gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
            transaction = {
                'chainId': chain_id,
                'from': account.address,
                'to': recipient,
                'value': amount,
                'gas': gas_limit,
                'maxFeePerGas': gas_price,
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
                'type': 2,  # EIP-1559
            }
        else:
            # Для других сетей используем legacy транзакцию
            gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
            transaction = {
                'chainId': chain_id,
                'to': recipient,
                'value': amount,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
            }
        
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        print(f"  ✓ Транзакция отправлена: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"  ✓ Транзакция подтверждена!")
            return True
        else:
            print(f"  ✗ Транзакция не удалась")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка отправки нативной валюты: {e}")
        return False


def get_token_price_coingecko(symbol):
    """Получить цену токена в USD (актуальные цены на февраль 2026)"""
    # Маппинг символов на актуальные цены
    price_map = {
        # Нативные токены
        'ETH': 3400,
        'BNB': 620,
        'AVAX': 40,
        'POL': 0.8,
        'MATIC': 0.8,
        'CELO': 0.8,
        'XDAI': 1.0,
        'CORE': 1.2,
        
        # Стейблкоины
        'USDC': 1.0,
        'USDT': 1.0,
        'DAI': 1.0,
        'USDC(BRIDGED)': 1.0,
        'USDC(BRIDGED)': 1.0,
        'USDC.E': 1.0,
        'USDBC': 1.0,
        'USD+': 1.0,
        'BUSD': 1.0,
        'LUSD': 1.0,
        'EURA': 1.1,
        'LZ-AGEUR': 1.1,
        'USDT0': 1.0,
        
        # BTC токены
        'WBTC': 95000,
        'BTC.B': 95000,
        
        # ETH токены
        'WETH': 3400,
        'WETH.E': 3400,
        'WRSETH': 3400,
        
        # DeFi & Governance токены
        'ARB': 0.75,        # Arbitrum
        'ZK': 0.12,         # zkSync
        'STG': 0.40,        # Stargate
        'MAV': 0.25,        # Maverick
        'IZI': 0.02,        # iZiSwap
        'LINEA': 0.0,       # Linea (нет публичного токена)
        
        # Другие токены
        'STMATIC': 0.8,     # Staked MATIC
        'WMATIC': 0.8,      # Wrapped MATIC
        'TOBY': 0.0,        # Мем-токен
    }
    return price_map.get(symbol.upper(), 0)


def check_layerbank_balance(w3, wallet_address, network_name, lock=None):
    """Проверить баланс в LayerBank для указанной сети"""
    if network_name not in LAYERBANK_CONFIG:
        return []
    
    config = LAYERBANK_CONFIG[network_name]
    ltokens_with_balance = []
    
    for ltoken_name, ltoken_address in config['ltokens'].items():
        try:
            ltoken_address = Web3.to_checksum_address(ltoken_address)
            contract = w3.eth.contract(address=ltoken_address, abi=LTOKEN_ABI)
            
            # Получаем баланс lToken
            ltoken_balance = contract.functions.balanceOf(wallet_address).call()
            
            if ltoken_balance == 0:
                continue
            
            # Получаем exchange rate
            exchange_rate = contract.functions.exchangeRate().call()
            
            # Рассчитываем underlying amount
            underlying_amount = (ltoken_balance * exchange_rate) // 10**18
            
            if underlying_amount == 0:
                continue
            
            # Оценка стоимости в USD
            if "ETH" in ltoken_name:
                value_usd = (underlying_amount / 1e18) * get_token_price_coingecko("ETH")
            elif "USDC" in ltoken_name or "USDT" in ltoken_name or "USDe" in ltoken_name:
                value_usd = underlying_amount / 1e6
            elif "BTC" in ltoken_name:
                value_usd = (underlying_amount / 1e8) * get_token_price_coingecko("WBTC")
            else:
                value_usd = (underlying_amount / 1e18) * 1000  # Предполагаем высокую стоимость
            
            if value_usd >= MIN_BALANCE_USD:
                ltokens_with_balance.append({
                    'name': ltoken_name,
                    'address': ltoken_address,
                    'ltoken_balance': ltoken_balance,
                    'underlying_amount': underlying_amount,
                    'value_usd': value_usd
                })
                
        except Exception as e:
            safe_print(f"  ⊘ Ошибка проверки {ltoken_name}: {e}", lock)
            continue
    
    return ltokens_with_balance


def withdraw_from_layerbank(w3, private_key, ltoken_address, ltoken_balance, network_name, lock=None):
    """Вывести средства из LayerBank"""
    try:
        config = LAYERBANK_CONFIG[network_name]
        core_address = Web3.to_checksum_address(config['core_address'])
        
        account = w3.eth.account.from_key(private_key)
        core_contract = w3.eth.contract(address=core_address, abi=LAYERBANK_CORE_ABI)
        
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price
        
        # Строим транзакцию redeemToken
        transaction = core_contract.functions.redeemToken(
            Web3.to_checksum_address(ltoken_address),
            ltoken_balance
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 500000,  # Оценка газа для redeem
        })
        
        # Подписываем и отправляем
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        safe_print(f"    ✓ Транзакция вывода: {tx_hash.hex()}", lock)
        
        # Ждем подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            safe_print(f"    ✓ Вывод подтвержден!", lock)
            return True
        else:
            safe_print(f"    ✗ Транзакция не прошла", lock)
            return False
            
    except Exception as e:
        safe_print(f"    ✗ Ошибка вывода: {e}", lock)
        return False


def process_layerbank_withdrawals(w3, private_key, network_name, lock=None):
    """Обработать вывод всех средств из LayerBank. Возвращает True если был вывод."""
    account = w3.eth.account.from_key(private_key)
    
    # СНАЧАЛА проверяем есть ли средства в LayerBank
    ltokens = check_layerbank_balance(w3, account.address, network_name, lock)
    
    if not ltokens:
        return False
    
    # ТОЛЬКО ЕСЛИ есть средства - проверяем газ и пополняем при необходимости
    if not check_and_refuel_gas(w3, account.address, network_name, "LayerBank вывод", 500000, lock):
        safe_print(f"  ⊘ Пропускаем вывод из LayerBank\n", lock)
        return False
    
    safe_print(f"\n🏦 Найдены средства в LayerBank ({len(ltokens)} токенов):", lock)
    
    had_withdrawal = False
    for ltoken_data in ltokens:
        safe_print(f"\n  [{ltoken_data['name']}]", lock)
        
        if "ETH" in ltoken_data['name']:
            formatted = f"{ltoken_data['underlying_amount'] / 1e18:.8f}"
        elif "USDC" in ltoken_data['name'] or "USDT" in ltoken_data['name']:
            formatted = f"{ltoken_data['underlying_amount'] / 1e6:.6f}"
        elif "BTC" in ltoken_data['name']:
            formatted = f"{ltoken_data['underlying_amount'] / 1e8:.8f}"
        else:
            formatted = f"{ltoken_data['underlying_amount'] / 1e18:.8f}"
        
        safe_print(f"    • Underlying: {formatted} (~${ltoken_data['value_usd']:.2f})", lock)
        safe_print(f"    • lToken баланс: {ltoken_data['ltoken_balance'] / 1e18:.8f}", lock)
        
        # Выводим из LayerBank
        safe_print(f"    → Вывод из LayerBank...", lock)
        success = withdraw_from_layerbank(
            w3, 
            private_key, 
            ltoken_data['address'], 
            ltoken_data['ltoken_balance'],
            network_name,
            lock
        )
        
        if success:
            had_withdrawal = True
            time.sleep(3)  # Ждем обновления балансов
        else:
            safe_print(f"    ⊘ Не удалось вывести {ltoken_data['name']}", lock)
    
    return had_withdrawal


# ===== SyncSwap Functions =====

def check_syncswap_liquidity(w3, wallet_address, network_name, lock=None):
    """Проверить ликвидность в SyncSwap пулах"""
    if network_name not in SYNCSWAP_CONFIG:
        return []
    
    config = SYNCSWAP_CONFIG[network_name]
    pools_with_liquidity = []
    
    for pool_info in config['pools']:
        try:
            pool_address = Web3.to_checksum_address(pool_info['pool_address'])
            pool_contract = w3.eth.contract(address=pool_address, abi=SYNCSWAP_LP_ABI)
            
            # Получаем баланс LP токенов
            lp_balance = pool_contract.functions.balanceOf(wallet_address).call()
            
            # Пропускаем dust позиции (меньше 0.0001 LP токенов)
            # Такие маленькие позиции часто не могут быть выведены из-за ограничений контракта
            if lp_balance < 100000000000000:  # 0.0001 LP tokens в wei (18 decimals)
                safe_print(f"    ⊘ {pool_info['name']}: LP баланс слишком мал ({lp_balance / 1e18:.8f}), пропускаем", lock)
                continue
            
            if lp_balance == 0:
                continue
            
            # Получаем резервы пула
            try:
                reserves = pool_contract.functions.getReserves().call()
                reserve0 = reserves[0]
                reserve1 = reserves[1]
            except:
                # Если getReserves не работает, пробуем альтернативный метод
                reserve0 = 0
                reserve1 = 0
            
            # Получаем total supply LP токенов
            total_supply = pool_contract.functions.totalSupply().call()
            
            if total_supply == 0:
                continue
            
            # Рассчитываем долю пользователя
            user_share = lp_balance / total_supply
            
            # Рассчитываем количество токенов, которые получит пользователь
            user_amount0 = int(reserve0 * user_share) if reserve0 > 0 else 0
            user_amount1 = int(reserve1 * user_share) if reserve1 > 0 else 0
            
            # Оценка стоимости в USD
            # Упрощенная оценка: используем цены из get_token_price_coingecko
            value_usd = 0
            
            # Получаем адреса токенов из пула для точного определения
            token0_addr = pool_info['token0'].lower()
            token1_addr = pool_info['token1'].lower()
            
            # Определяем известные адреса токенов на zkSync ERA
            weth_zksync = "0x5aea5775959fbc2557cc8789bc1bf90a239d9a91"
            usdc_zksync = "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4"
            usdt_zksync = "0x493257fd37edb34451f62edf8d2a0c418852ba4c"
            
            # Рассчитываем стоимость каждого токена
            # Token0
            if token0_addr == weth_zksync:
                value_usd += (user_amount0 / 1e18) * get_token_price_coingecko("ETH")
            elif token0_addr in [usdc_zksync, usdt_zksync]:
                value_usd += user_amount0 / 1e6  # 6 decimals
            else:
                # Другие токены с 18 decimals
                value_usd += (user_amount0 / 1e18) * 1.0  # Предполагаем $1 если неизвестно
            
            # Token1
            if token1_addr == weth_zksync:
                value_usd += (user_amount1 / 1e18) * get_token_price_coingecko("ETH")
            elif token1_addr in [usdc_zksync, usdt_zksync]:
                value_usd += user_amount1 / 1e6  # 6 decimals
            else:
                # Другие токены с 18 decimals
                value_usd += (user_amount1 / 1e18) * 1.0  # Предполагаем $1 если неизвестно
            
            # Удаляем debug вывод
            # safe_print(f"    DEBUG {pool_info['name']}: value_usd=${value_usd:.4f}, user_amount0={user_amount0}, user_amount1={user_amount1}", lock)
            
            # Проверка минимальной ликвидности
            if value_usd >= config['min_liquidity_usd']:
                pools_with_liquidity.append({
                    'name': pool_info['name'],
                    'pool_address': pool_address,
                    'lp_balance': lp_balance,
                    'user_amount0': user_amount0,
                    'user_amount1': user_amount1,
                    'value_usd': value_usd,
                    'token0': pool_info['token0'],
                    'token1': pool_info['token1']
                })
            else:
                # Debug: показываем почему пул не подходит
                safe_print(f"    ⊘ {pool_info['name']}: LP={lp_balance / 1e18:.18f}, USD=${value_usd:.4f} (минимум ${config['min_liquidity_usd']})", lock)
                
        except Exception as e:
            safe_print(f"  ⊘ Ошибка проверки пула {pool_info['name']}: {e}", lock)
            continue
    
    return pools_with_liquidity


def withdraw_from_syncswap(w3, private_key, pool_data, network_name, lock=None):
    """Вывести ликвидность из SyncSwap пула"""
    try:
        config = SYNCSWAP_CONFIG[network_name]
        router_address = Web3.to_checksum_address(config['router_address'])
        
        account = w3.eth.account.from_key(private_key)
        router_contract = w3.eth.contract(address=router_address, abi=SYNCSWAP_ROUTER_ABI)
        
        # Параметры для burnLiquidity
        pool_address = pool_data['pool_address']
        liquidity = pool_data['lp_balance']
        
        # data: пустой bytes для стандартного вывода
        data = b''
        
        # minAmounts: устанавливаем в 0 для очень маленьких балансов чтобы избежать underflow
        # Порог: если меньше 1000 wei, ставим 0
        min_amount0 = 0 if pool_data['user_amount0'] < 1000 else int(pool_data['user_amount0'] * 0.95)
        min_amount1 = 0 if pool_data['user_amount1'] < 1000 else int(pool_data['user_amount1'] * 0.95)
        min_amounts = [min_amount0, min_amount1]
        
        # callback и callbackData: пустые для стандартного вывода
        callback = "0x0000000000000000000000000000000000000000"
        callback_data = b''
        
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
        
        # Debug: показываем параметры
        safe_print(f"    → Параметры вывода:", lock)
        safe_print(f"      Pool: {pool_address}", lock)
        safe_print(f"      Liquidity: {liquidity}", lock)
        safe_print(f"      Min amounts: [{min_amount0}, {min_amount1}]", lock)
        
        # Строим транзакцию burnLiquidity
        # Для zkSync ERA НЕ используем 'type': 2, используем только gas (без maxFeePerGas)
        transaction = router_contract.functions.burnLiquidity(
            pool_address,
            liquidity,
            data,
            min_amounts,
            callback,
            callback_data
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gas': 500000,  # Большой лимит для сложной операции
            'gasPrice': gas_price,  # Используем gasPrice вместо maxFeePerGas для zkSync ERA
        })
        
        # Подписываем и отправляем
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        safe_print(f"    ✓ Транзакция вывода: {tx_hash.hex()}", lock)
        
        # Ждем подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            safe_print(f"    ✓ Вывод ликвидности подтвержден!", lock)
            return True
        else:
            safe_print(f"    ✗ Транзакция не прошла (reverted)", lock)
            # Пробуем получить причину реверта
            try:
                w3.eth.call(transaction, receipt.blockNumber)
            except Exception as call_error:
                safe_print(f"    ℹ️ Причина: {str(call_error)[:200]}", lock)
            return False
            
    except Exception as e:
        safe_print(f"    ✗ Ошибка вывода: {e}", lock)
        import traceback
        safe_print(f"    ℹ️ Детали: {traceback.format_exc()[:500]}", lock)
        return False


def process_syncswap_withdrawals(w3, private_key, network_name, lock=None):
    """Обработать вывод всей ликвидности из SyncSwap. Возвращает True если был вывод."""
    account = w3.eth.account.from_key(private_key)
    
    # СНАЧАЛА проверяем есть ли ликвидность в SyncSwap
    pools = check_syncswap_liquidity(w3, account.address, network_name, lock)
    
    if not pools:
        return False
    
    # ТОЛЬКО ЕСЛИ есть ликвидность - проверяем газ и пополняем при необходимости
    if not check_and_refuel_gas(w3, account.address, network_name, "SyncSwap вывод", 500000, lock):
        safe_print(f"  ⊘ Пропускаем вывод из SyncSwap\n", lock)
        return False
    
    safe_print(f"\n💧 Найдена ликвидность в SyncSwap ({len(pools)} пулов):", lock)
    
    had_withdrawal = False
    for pool_data in pools:
        safe_print(f"\n  [{pool_data['name']}]", lock)
        safe_print(f"    • LP баланс: {pool_data['lp_balance'] / 1e18:.8f}", lock)
        safe_print(f"    • Примерная стоимость: ~${pool_data['value_usd']:.2f}", lock)
        safe_print(f"    • Token0 amount: {pool_data['user_amount0'] / 1e18:.8f}", lock)
        safe_print(f"    • Token1 amount: {pool_data['user_amount1'] / 1e18:.8f}", lock)
        
        # Выводим ликвидность
        safe_print(f"    → Вывод ликвидности из SyncSwap...", lock)
        success = withdraw_from_syncswap(
            w3, 
            private_key, 
            pool_data,
            network_name,
            lock
        )
        
        if success:
            had_withdrawal = True
            time.sleep(3)  # Ждем обновления балансов
        else:
            safe_print(f"    ⊘ Не удалось вывести ликвидность из {pool_data['name']}", lock)
    
    return had_withdrawal


# ===== Swapr Functions =====

def check_swapr_liquidity(w3, wallet_address, network_name, lock=None):
    """Проверить ликвидность в Swapr пулах"""
    if network_name not in SWAPR_CONFIG:
        return []
    
    config = SWAPR_CONFIG[network_name]
    pools_with_liquidity = []
    
    for pool_info in config['pools']:
        try:
            pool_address = Web3.to_checksum_address(pool_info['pool_address'])
            pool_contract = w3.eth.contract(address=pool_address, abi=SWAPR_PAIR_ABI)
            
            # Получаем баланс LP токенов
            lp_balance = pool_contract.functions.balanceOf(wallet_address).call()
            
            if lp_balance == 0:
                continue
            
            # Получаем резервы пула
            reserves = pool_contract.functions.getReserves().call()
            reserve0 = reserves[0]
            reserve1 = reserves[1]
            
            # Получаем total supply LP токенов
            total_supply = pool_contract.functions.totalSupply().call()
            
            if total_supply == 0:
                continue
            
            # Получаем реальные адреса токенов из контракта пула
            actual_token0 = pool_contract.functions.token0().call()
            actual_token1 = pool_contract.functions.token1().call()
            
            # Рассчитываем долю пользователя
            user_share = lp_balance / total_supply
            
            # Рассчитываем количество токенов, которые получит пользователь
            user_amount0 = int(reserve0 * user_share)
            user_amount1 = int(reserve1 * user_share)
            
            # Оценка стоимости в USD
            value_usd = 0
            
            # Определяем токены по адресам
            token0_addr = pool_contract.functions.token0().call().lower()
            token1_addr = pool_contract.functions.token1().call().lower()
            
            # WETH на Arbitrum
            weth_arbitrum = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
            # Stablecoins на Arbitrum
            usdc_arbitrum = "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8"
            usdt_arbitrum = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"
            dai_arbitrum = "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1"
            # ARB токен
            arb_arbitrum = "0x912ce59144191c1204e64559fe8253a0e49e6548"
            
            # Рассчитываем стоимость каждого токена
            if token0_addr == weth_arbitrum:
                value_usd += (user_amount0 / 1e18) * get_token_price_coingecko("ETH")
            elif token0_addr in [usdc_arbitrum, usdt_arbitrum]:
                value_usd += user_amount0 / 1e6
            elif token0_addr == dai_arbitrum:
                value_usd += user_amount0 / 1e18
            elif token0_addr == arb_arbitrum:
                value_usd += (user_amount0 / 1e18) * get_token_price_coingecko("ARB")
            else:
                value_usd += user_amount0 / 1e18  # Предполагаем 18 decimals
            
            if token1_addr == weth_arbitrum:
                value_usd += (user_amount1 / 1e18) * get_token_price_coingecko("ETH")
            elif token1_addr in [usdc_arbitrum, usdt_arbitrum]:
                value_usd += user_amount1 / 1e6
            elif token1_addr == dai_arbitrum:
                value_usd += user_amount1 / 1e18
            elif token1_addr == arb_arbitrum:
                value_usd += (user_amount1 / 1e18) * get_token_price_coingecko("ARB")
            else:
                value_usd += user_amount1 / 1e18
            
            # Проверка минимальной ликвидности
            if value_usd >= config['min_liquidity_usd']:
                pools_with_liquidity.append({
                    'name': pool_info['name'],
                    'pool_address': pool_address,
                    'lp_balance': lp_balance,
                    'user_amount0': user_amount0,
                    'user_amount1': user_amount1,
                    'value_usd': value_usd,
                    'token0': actual_token0,  # Используем реальные адреса из контракта
                    'token1': actual_token1,  # Используем реальные адреса из контракта
                    'is_eth_pool': token0_addr == weth_arbitrum or token1_addr == weth_arbitrum
                })
                
        except Exception as e:
            safe_print(f"  ⊘ Ошибка проверки пула {pool_info['name']}: {e}", lock)
            continue
    
    return pools_with_liquidity


def withdraw_from_swapr(w3, private_key, pool_data, network_name, lock=None):
    """Вывести ликвидность из Swapr пула"""
    try:
        config = SWAPR_CONFIG[network_name]
        router_address = Web3.to_checksum_address(config['router_address'])
        pool_address = pool_data['pool_address']
        
        account = w3.eth.account.from_key(private_key)
        router_contract = w3.eth.contract(address=router_address, abi=SWAPR_ROUTER_ABI)
        pool_contract = w3.eth.contract(address=pool_address, abi=SWAPR_PAIR_ABI)
        
        # Сначала нужно approve LP токенов для роутера
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
        
        # Проверяем текущий allowance
        try:
            allowance = pool_contract.functions.allowance(account.address, router_address).call()
        except:
            allowance = 0
        
        # Если allowance недостаточен, делаем approve
        if allowance < pool_data['lp_balance']:
            safe_print(f"    → Approve LP токенов для роутера...", lock)
            
            approve_tx = pool_contract.functions.approve(
                router_address,
                pool_data['lp_balance']
            ).build_transaction({
                'chainId': w3.eth.chain_id,
                'from': account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': gas_price,
            })
            
            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
            approve_hash = w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            
            safe_print(f"    ✓ Approve транзакция: {approve_hash.hex()}", lock)
            
            # Ждем подтверждения approve
            approve_receipt = w3.eth.wait_for_transaction_receipt(approve_hash, timeout=300)
            
            if approve_receipt.status != 1:
                safe_print(f"    ✗ Approve не прошел", lock)
                return False
            
            time.sleep(2)
            nonce += 1
        
        # Минимальные суммы с очень большим slippage (99%) для маленьких сумм
        # Если сумма очень маленькая или равна 0, используем 0
        min_amount0 = 0 if pool_data['user_amount0'] < 1000 else int(pool_data['user_amount0'] * 0.01)
        min_amount1 = 0 if pool_data['user_amount1'] < 1000 else int(pool_data['user_amount1'] * 0.01)
        
        # Deadline: текущее время + 20 минут
        deadline = int(time.time()) + 1200
        
        # Для Swapr всегда используем removeLiquidity (не ETH-специфичный метод)
        # Это более универсальный и безопасный способ
        safe_print(f"    → Вывод ликвидности...", lock)
        safe_print(f"    • Token0: {pool_data['token0']}", lock)
        safe_print(f"    • Token1: {pool_data['token1']}", lock)
        safe_print(f"    • Min amount0: {min_amount0}", lock)
        safe_print(f"    • Min amount1: {min_amount1}", lock)
        safe_print(f"    • Liquidity: {pool_data['lp_balance']}", lock)
        
        transaction = router_contract.functions.removeLiquidity(
            Web3.to_checksum_address(pool_data['token0']),
            Web3.to_checksum_address(pool_data['token1']),
            pool_data['lp_balance'],
            min_amount0,
            min_amount1,
            account.address,
            deadline
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': gas_price,
        })
        
        # Подписываем и отправляем
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        safe_print(f"    ✓ Транзакция вывода: {tx_hash.hex()}", lock)
        
        # Ждем подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            safe_print(f"    ✓ Вывод ликвидности подтвержден!", lock)
            return True
        else:
            safe_print(f"    ✗ Транзакция не прошла", lock)
            return False
            
    except Exception as e:
        safe_print(f"    ✗ Ошибка вывода: {e}", lock)
        return False


def process_swapr_withdrawals(w3, private_key, network_name, lock=None):
    """Обработать вывод всей ликвидности из Swapr. Возвращает True если был вывод."""
    account = w3.eth.account.from_key(private_key)
    
    # СНАЧАЛА проверяем есть ли ликвидность в Swapr
    pools = check_swapr_liquidity(w3, account.address, network_name, lock)
    
    if not pools:
        return False
    
    # ТОЛЬКО ЕСЛИ есть ликвидность - проверяем газ и пополняем при необходимости
    if not check_and_refuel_gas(w3, account.address, network_name, "Swapr вывод", 600000, lock):
        safe_print(f"  ⊘ Пропускаем вывод из Swapr\n", lock)
        return False
    
    safe_print(f"\n🔄 Найдена ликвидность в Swapr ({len(pools)} пулов):", lock)
    
    had_withdrawal = False
    for pool_data in pools:
        safe_print(f"\n  [{pool_data['name']}]", lock)
        safe_print(f"    • LP баланс: {pool_data['lp_balance'] / 1e18:.8f}", lock)
        safe_print(f"    • Примерная стоимость: ~${pool_data['value_usd']:.2f}", lock)
        safe_print(f"    • Token0 amount: {pool_data['user_amount0'] / 1e18:.8f}", lock)
        safe_print(f"    • Token1 amount: {pool_data['user_amount1'] / 1e18:.8f}", lock)
        
        # Выводим ликвидность
        safe_print(f"    → Вывод ликвидности из Swapr...", lock)
        success = withdraw_from_swapr(
            w3, 
            private_key, 
            pool_data,
            network_name,
            lock
        )
        
        if success:
            had_withdrawal = True
            time.sleep(3)  # Ждем обновления балансов
        else:
            safe_print(f"    ⊘ Не удалось вывести ликвидность из {pool_data['name']}", lock)
    
    return had_withdrawal


def safe_print(message, lock=None):
    """Безопасный вывод с учетом многопоточности"""
    if lock:
        with lock:
            print(message)
    else:
        print(message)


def check_gas_balance(w3, address, operation_name="операции", gas_limit=500000, lock=None, network_name=None):
    """
    Проверить достаточно ли нативного токена для оплаты gas
    Возвращает True если достаточно, False если нет
    """
    # Определяем символ нативного токена
    native_symbol = "ETH"  # По умолчанию
    if network_name and network_name in NETWORKS:
        native_symbol = NETWORKS[network_name]['native_symbol']
    
    native_balance = w3.eth.get_balance(address)
    gas_price = w3.eth.gas_price
    estimated_gas_cost = int(gas_price * gas_limit * 1.3)  # С запасом 30%
    
    if native_balance < estimated_gas_cost:
        safe_print(f"\n⚠️ Недостаточно {native_symbol} для gas ({operation_name})!", lock)
        safe_print(f"  💰 Баланс {native_symbol}: {native_balance / 1e18:.8f}", lock)
        safe_print(f"  ⛽ Нужно для gas: ~{estimated_gas_cost / 1e18:.8f} {native_symbol}", lock)
        safe_print(f"  ❌ Дефицит: ~{(estimated_gas_cost - native_balance) / 1e18:.8f} {native_symbol}", lock)
        return False
    
    return True


def refuel_gas_from_recipient(w3, donor_address, network_name, lock=None):
    """
    Автоматически пополнить gas для кошелька из RECIPIENT_ADDRESS_KEY
    Возвращает True если пополнение успешно, False если нет
    """
    if not AUTO_REFUEL_GAS or not RECIPIENT_ADDRESS_KEY:
        return False
    
    try:
        # Определяем символ нативного токена для сети
        native_symbol = NETWORKS[network_name]['native_symbol']
        
        # Получаем аккаунт получателя
        recipient_account = w3.eth.account.from_key(RECIPIENT_ADDRESS_KEY)
        recipient_balance = w3.eth.get_balance(recipient_account.address)
        
        # Рассчитываем сумму для отправки
        gas_price = w3.eth.gas_price
        
        # Специальный gas limit для разных сетей
        if network_name == "zkSync ERA":
            transfer_gas_limit = 250000
        elif network_name in ["Arbitrum", "Arbitrum Nova"]:
            transfer_gas_limit = 100000  # Arbitrum требует больше газа
        else:
            transfer_gas_limit = 21000
        
        # Увеличиваем сумму пополнения: газ на 3-5 транзакций
        # Для каждой транзакции ERC-20 нужно ~200k gas, для нативной ~21k
        base_refuel = MIN_GAS_REFUEL_AMOUNT
        
        # Рассчитываем стоимость нескольких транзакций
        # Берем запас на 5 транзакций токенов + 1 нативная
        multi_tx_cost = int(gas_price * (200000 * 5 + 21000) * 1.5)
        
        # Если стандартное пополнение меньше чем нужно на 5 транзакций, увеличиваем
        refuel_amount_wei = max(w3.to_wei(base_refuel, 'ether'), multi_tx_cost)
        
        # Стоимость самой транзакции пополнения
        transfer_cost = int(gas_price * transfer_gas_limit * 1.5)  # 50% запас на саму транзакцию
        
        total_needed = refuel_amount_wei + transfer_cost
        
        # Проверяем баланс получателя
        if recipient_balance < total_needed:
            safe_print(f"  ⚠️ Недостаточно средств у получателя для пополнения gas", lock)
            safe_print(f"  💰 Баланс: {recipient_balance / 1e18:.8f} {native_symbol}", lock)
            safe_print(f"  💸 Нужно: {total_needed / 1e18:.8f} {native_symbol}", lock)
            return False
        
        safe_print(f"\n⛽ Автопополнение gas из основного кошелька...", lock)
        safe_print(f"  → Отправка {refuel_amount_wei / 1e18:.8f} {native_symbol} для gas (на ~5 транзакций)", lock)
        safe_print(f"  → С кошелька: {recipient_account.address}", lock)
        safe_print(f"  → На кошелек: {donor_address}", lock)
        
        # ВАЖНО: Получаем баланс получателя ДО отправки транзакции
        balance_before_refuel = w3.eth.get_balance(donor_address)
        
        # Подготовка транзакции
        nonce = w3.eth.get_transaction_count(recipient_account.address)
        
        if network_name == "zkSync ERA":
            # EIP-1559 для zkSync ERA
            transaction = {
                'chainId': w3.eth.chain_id,
                'from': recipient_account.address,
                'to': Web3.to_checksum_address(donor_address),
                'value': refuel_amount_wei,
                'gas': transfer_gas_limit,
                'maxFeePerGas': int(gas_price * GAS_PRICE_MULTIPLIER),
                'maxPriorityFeePerGas': int(gas_price * GAS_PRICE_MULTIPLIER),
                'nonce': nonce,
                'type': 2,
            }
        else:
            # Legacy транзакция для других сетей
            transaction = {
                'chainId': w3.eth.chain_id,
                'to': Web3.to_checksum_address(donor_address),
                'value': refuel_amount_wei,
                'gas': transfer_gas_limit,
                'gasPrice': int(gas_price * GAS_PRICE_MULTIPLIER),
                'nonce': nonce,
            }
        
        # Подпись и отправка
        signed_txn = w3.eth.account.sign_transaction(transaction, RECIPIENT_ADDRESS_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        safe_print(f"  ✓ Транзакция пополнения: {tx_hash.hex()}", lock)
        
        # Ожидание подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            safe_print(f"  ✓ Gas успешно пополнен! ({refuel_amount_wei / 1e18:.8f} {native_symbol})", lock)
            
            # Ждем обновления баланса с повторными попытками (максимум 4 попытки)
            max_attempts = 4
            wait_time = 15  # секунд между попытками
            
            for attempt in range(1, max_attempts + 1):
                safe_print(f"  ⏳ Ожидание обновления баланса... (попытка {attempt}/{max_attempts}, ждем {wait_time} сек)", lock)
                time.sleep(wait_time)
                
                # Проверяем новый баланс
                new_balance = w3.eth.get_balance(donor_address)
                safe_print(f"  📊 Текущий баланс: {new_balance / 1e18:.8f} {native_symbol}", lock)
                
                # Проверяем что баланс увеличился (сравниваем с балансом ДО пополнения)
                if new_balance > balance_before_refuel:
                    balance_increase = (new_balance - balance_before_refuel) / 1e18
                    safe_print(f"  ✓ Баланс успешно обновлен! (+{balance_increase:.8f} {native_symbol})", lock)
                    return True
                else:
                    if attempt < max_attempts:
                        safe_print(f"  ⚠️ Баланс еще не обновился, продолжаем ожидание...", lock)
                    else:
                        safe_print(f"  ⚠️ Баланс не обновился после {max_attempts} попыток", lock)
                        safe_print(f"  ℹ️ Возможно, транзакция еще в обработке. Продолжаем работу...", lock)
                        return True  # Возвращаем True, так как транзакция подтверждена
            
            return True
        else:
            safe_print(f"  ✗ Транзакция пополнения не удалась", lock)
            return False
            
    except Exception as e:
        safe_print(f"  ✗ Ошибка пополнения gas: {e}", lock)
        return False


def check_and_refuel_gas(w3, address, network_name, operation_name="операции", gas_limit=500000, lock=None):
    """
    Проверить gas и автоматически пополнить если нужно
    Возвращает True если газа достаточно (или пополнение успешно), False если нет
    """
    # Сначала проверяем текущий баланс
    if check_gas_balance(w3, address, operation_name, gas_limit, lock, network_name):
        return True
    
    # Если газа недостаточно и включено автопополнение
    if AUTO_REFUEL_GAS and RECIPIENT_ADDRESS_KEY:
        safe_print(f"  🔄 Попытка автопополнения gas...", lock)
        
        if refuel_gas_from_recipient(w3, address, network_name, lock):
            # Проверяем еще раз после пополнения
            return check_gas_balance(w3, address, operation_name, gas_limit, lock, network_name)
    
    return False


def process_wallet_in_network(w3, private_key, network_name, network_config, recipient, all_networks, lock=None):
    """Обработать один кошелек в одной сети"""
    try:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        
        # Флаги для отслеживания транзакций
        had_defi_withdrawals = False
        had_transactions = False
        
        # ===== НОВОЕ: Проверка и вывод из LayerBank =====
        if network_name in LAYERBANK_CONFIG:
            safe_print(f"\n🏦 Проверка LayerBank...", lock)
            if process_layerbank_withdrawals(w3, private_key, network_name, lock):
                had_defi_withdrawals = True
            safe_print(f"✓ Проверка LayerBank завершена\n", lock)
        
        # ===== НОВОЕ: Проверка и вывод ликвидности из DEX пулов =====
        # SyncSwap
        if network_name in SYNCSWAP_CONFIG:
            safe_print(f"\n💧 Проверка SyncSwap...", lock)
            if process_syncswap_withdrawals(w3, private_key, network_name, lock):
                had_defi_withdrawals = True
            safe_print(f"✓ Проверка SyncSwap завершена\n", lock)
        

            # SyncSwap (если не zkSync ERA или zkSync ERA уже обработан выше)
            if network_name in SYNCSWAP_CONFIG and network_name != "zkSync ERA":
                safe_print(f"\n� Проверка SyncSwap...", lock)
                if process_syncswap_withdrawals(w3, private_key, network_name, lock):
                    had_defi_withdrawals = True
                safe_print(f"✓ Проверка SyncSwap завершена\n", lock)
            

        
        # ===== НОВОЕ: Проверка и вывод ликвидности из Swapr =====
        if network_name in SWAPR_CONFIG:
            safe_print(f"\n� Проверка Swapr...", lock)
            if process_swapr_withdrawals(w3, private_key, network_name, lock):
                had_defi_withdrawals = True
            safe_print(f"✓ Проверка Swapr завершена\n", lock)
        
        # ===== НОВОЕ: Таймер ожидания после выводов ликвидности =====
        if had_defi_withdrawals:
            safe_print(f"\n⏳ Ожидание обновления балансов после вывода ликвидности (60 секунд)...", lock)
            time.sleep(60)
            safe_print(f"✓ Балансы обновлены, продолжаем обработку токенов\n", lock)
        
        # ИЗМЕНЕНО: Сначала обрабатываем токены с явно указанными контрактами
        safe_print(f"\n📦 Обработка ERC-20 токенов...", lock)
            
        for token in network_config['tokens']:
            token_symbol = token['symbol']
            token_address = token['address']
            
            safe_print(f"\n[{token_symbol}]", lock)
            
            balance, decimals = get_token_balance(w3, token_address, address)
            balance_human = balance / (10 ** decimals)
            
            safe_print(f"  Баланс: {balance_human:.6f} {token_symbol}", lock)
            
            if balance == 0:
                safe_print(f"  ⊘ Баланс нулевой, пропускаем", lock)
                continue
            
            # Проверка минимального баланса в USD
            token_price = get_token_price_coingecko(token_symbol)
            balance_usd = balance_human * token_price
            if balance_usd < MIN_BALANCE_USD:
                safe_print(f"  ⊘ Баланс меньше ${MIN_BALANCE_USD} (~${balance_usd:.4f}), пропускаем", lock)
                continue
            
            # Проверка газа перед отправкой токена (с автопополнением если нужно)
            if not check_and_refuel_gas(w3, address, network_name, f"перевод {token_symbol}", 200000, lock):
                safe_print(f"  ⊘ Недостаточно gas для перевода {token_symbol}", lock)
                continue
            
            # Отправка токена
            safe_print(f"  → Отправка {balance_human:.6f} {token_symbol}...", lock)
            if send_token(w3, private_key, token_address, recipient, balance, network_config['chain_id'], network_name):
                had_transactions = True
            
            time.sleep(2)  # Пауза между транзакциями
        
        # ИЗМЕНЕНО: Нативный токен отправляется ПОСЛЕДНИМ после всех операций
        safe_print(f"\n💰 Обработка нативного токена (финальная отправка)...", lock)
        safe_print(f"\n[{network_config['native_symbol']}]", lock)
        native_balance = w3.eth.get_balance(address)
        native_balance_human = native_balance / (10 ** 18)
        
        safe_print(f"  Баланс: {native_balance_human:.6f} {network_config['native_symbol']}", lock)
        
        if native_balance == 0:
            safe_print(f"  ⊘ Баланс нулевой, пропускаем", lock)
            return
        
        # Проверка минимального баланса в USD
        native_price = get_token_price_coingecko(network_config['native_symbol'])
        native_balance_usd = native_balance_human * native_price
        if native_balance_usd < MIN_BALANCE_USD:
            safe_print(f"  ⊘ Баланс меньше ${MIN_BALANCE_USD} (~${native_balance_usd:.4f}), пропускаем", lock)
            return
        
        # Специальная проверка для zkSync ERA - минимум 0.0001 ETH (снижен порог)
        if network_name == "zkSync ERA" and native_balance_human < 0.0001:
            safe_print(f"  ⊘ Баланс слишком мал для zkSync ERA validation (минимум 0.0001 ETH)", lock)
            return
        
        # ИСПРАВЛЕНО: Более точный расчет комиссии для нативной валюты
        gas_price = w3.eth.gas_price
        gas_limit = 21000
        
        # Специальная обработка для разных типов сетей
        if network_name in ["zkSync ERA"]:
            # zkSync ERA использует EIP-1559 и требует большой gas_limit (250000)
            # Реальное использование обычно ~100-150k gas
            gas_limit = 250000
            gas_price_multiplied = int(gas_price * GAS_PRICE_MULTIPLIER)
            
            # Консервативная оценка максимальной стоимости транзакции
            max_tx_cost = gas_price_multiplied * gas_limit
            
            # Вычитаем стоимость с запасом
            amount_to_send = native_balance - int(max_tx_cost * 1.2)
            
            if amount_to_send <= 0:
                safe_print(f"  ⊘ Недостаточно средств для zkSync ERA после вычета комиссии", lock)
                safe_print(f"  (Макс. стоимость TX: ~{max_tx_cost * 1.2 / 1e18:.8f} ETH)", lock)
                return
            
            safe_print(f"  Макс. стоимость TX: ~{max_tx_cost / 1e18:.8f} ETH", lock)
            safe_print(f"  → Отправка {amount_to_send / 1e18:.8f} ETH", lock)
            # Для zkSync ERA amount_to_send уже установлен, пропускаем остальную логику
        else:
            # Для остальных сетей используем стандартный расчет
            if network_name in ["Scroll"]:
                # Scroll требует дополнительного расчета L1 Data Fee
                gas_limit = 21000
                base_cost = gas_price * gas_limit * GAS_PRICE_MULTIPLIER
                l1_fee_estimate = int(0.00003 * (10 ** 18))
                transfer_cost_with_buffer = int(base_cost * 1.5 + l1_fee_estimate)
            elif network_name in ["Optimism", "Arbitrum", "Arbitrum Nova", "BASE", "ZORA"]:
                # Другие Layer 2 сети с L1 Data Fee
                if network_name in ["Arbitrum", "Arbitrum Nova"]:
                    gas_limit = 100000  # Arbitrum требует больше газа для малых сумм
                else:
                    gas_limit = 21000
                transfer_cost_with_buffer = int(gas_price * gas_limit * GAS_PRICE_MULTIPLIER * 2.5)
            else:
                # Обычные L1 сети
                transfer_cost_with_buffer = int(gas_price * gas_limit * GAS_PRICE_MULTIPLIER * 1.3)
            
            # Проверяем, что после вычета комиссии останется что-то значимое
            amount_to_send = native_balance - transfer_cost_with_buffer
            
            if amount_to_send <= 0:
                safe_print(f"  ⊘ Недостаточно средств для перевода после вычета комиссии", lock)
                transfer_cost_human = transfer_cost_with_buffer / (10 ** 18)
                safe_print(f"  (Нужно минимум {transfer_cost_human:.8f} {network_config['native_symbol']} на комиссию)", lock)
                return
            
            amount_to_send_human = amount_to_send / (10 ** 18)
            transfer_cost_human = transfer_cost_with_buffer / (10 ** 18)
            
            safe_print(f"  Комиссия (с запасом): ~{transfer_cost_human:.8f} {network_config['native_symbol']}", lock)
            safe_print(f"  → Отправка {amount_to_send_human:.8f} {network_config['native_symbol']}...", lock)
        
        send_native(w3, private_key, recipient, amount_to_send, network_config['chain_id'], network_name)
        
        # Если были транзакции автопополнения, возвращаем остатки на основной кошелек
        if had_transactions and AUTO_REFUEL_GAS and RECIPIENT_ADDRESS_KEY:
            time.sleep(3)  # Ждем обновления баланса
            final_balance = w3.eth.get_balance(address)
            
            # Проверяем, остались ли значительные средства
            if final_balance > w3.to_wei(0.0001, 'ether'):
                safe_print(f"\n♻️ Возврат остатков gas на основной кошелек...", lock)
                
                # Рассчитываем сумму для возврата
                gas_limit_return = 250000 if network_name == "zkSync ERA" else 21000
                return_cost = int(w3.eth.gas_price * gas_limit_return * 1.5)
                amount_to_return = final_balance - return_cost
                
                if amount_to_return > 0:
                    safe_print(f"  → Возврат {amount_to_return / 1e18:.8f} {network_config['native_symbol']}", lock)
                    send_native(w3, private_key, RECIPIENT_ADDRESS, amount_to_return, network_config['chain_id'], network_name)
        
    except Exception as e:
        safe_print(f"✗ Ошибка обработки кошелька в сети {network_name}: {e}", lock)


def process_single_wallet(wallet_data, recipient, all_networks, print_lock):
    """Обработать один кошелек во всех сетях"""
    idx, private_key, total_wallets = wallet_data
    
    with print_lock:
        print(f"\n\n{'='*60}")
        print(f"ОБРАБОТКА КОШЕЛЬКА {idx}/{total_wallets}")
        print(f"{'='*60}")
    
    # Получаем адрес кошелька для отображения
    try:
        account = Web3().eth.account.from_key(private_key)
        with print_lock:
            print(f"Адрес: {account.address}")
    except Exception as e:
        with print_lock:
            print(f"✗ Ошибка загрузки кошелька: {e}")
        return
    
    # Проходим по всем сетям для этого кошелька
    for network_name, network_config in all_networks.items():
        with print_lock:
            print(f"\n{'#'*60}")
            print(f"# Сеть: {network_name}")
            print(f"{'#'*60}")
        
        try:
            w3 = Web3(Web3.HTTPProvider(network_config['rpc']))
            
            if not w3.is_connected():
                with print_lock:
                    print(f"✗ Не удалось подключиться к {network_name}")
                continue
            
            with print_lock:
                print(f"✓ Подключено к {network_name}")
            
            # Обработка кошелька в этой сети
            process_wallet_in_network(w3, private_key, network_name, network_config, recipient, all_networks, print_lock)
            time.sleep(2)  # Пауза между сетями
                
        except Exception as e:
            with print_lock:
                print(f"✗ Ошибка при работе с сетью {network_name}: {e}")
            continue
    
    with print_lock:
        print(f"\n{'='*60}")
        print(f"КОШЕЛЕК {idx}/{total_wallets} ОБРАБОТАН")
        print(f"{'='*60}")
    
    time.sleep(PAUSE_BETWEEN_WALLETS)


async def process_wallets_async(private_keys, recipient, all_networks):
    """Асинхронная обработка кошельков с использованием ThreadPoolExecutor"""
    print_lock = threading.Lock()
    
    # Подготовка данных для обработки
    wallet_data_list = [
        (idx, private_key, len(private_keys))
        for idx, private_key in enumerate(private_keys, 1)
    ]
    
    # Создание пула потоков
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WALLETS) as executor:
        loop = asyncio.get_event_loop()
        
        # Запуск задач в пуле потоков
        tasks = [
            loop.run_in_executor(
                executor,
                process_single_wallet,
                wallet_data,
                recipient,
                all_networks,
                print_lock
            )
            for wallet_data in wallet_data_list
        ]
        
        # Ожидание завершения всех задач
        await asyncio.gather(*tasks)


def main():
    """Главная функция"""
    print("="*60)
    print("СБОРЩИК ТОКЕНОВ ИЗ EVM СЕТЕЙ")
    print("="*60)
    
    # Проверка адреса получателя
    if "ВАШ_АДРЕС" in RECIPIENT_ADDRESS or not RECIPIENT_ADDRESS.startswith("0x"):
        print("\n✗ ОШИБКА: Укажите адрес получателя в переменной RECIPIENT_ADDRESS!")
        return
    
    try:
        recipient = Web3.to_checksum_address(RECIPIENT_ADDRESS)
    except:
        print("\n✗ ОШИБКА: Некорректный адрес получателя!")
        return
    
    print(f"\nАдрес получателя: {recipient}")
    
    # Загрузка приватных ключей
    private_keys = load_private_keys()
    
    if not private_keys:
        print("\n✗ Нет приватных ключей для обработки!")
        return
    
    print(f"\n{'='*60}")
    print(f"РЕЖИМ: Многопоточная обработка")
    print(f"Параллельных кошельков: {MAX_PARALLEL_WALLETS}")
    print(f"Всего кошельков: {len(private_keys)}")
    print(f"{'='*60}")
    
    # Запуск асинхронной обработки
    try:
        asyncio.run(process_wallets_async(private_keys, recipient, NETWORKS))
    except KeyboardInterrupt:
        print("\n\n⚠ Прервано пользователем")
        return
    
    print("\n\n" + "="*60)
    print("ВСЕ КОШЕЛЬКИ ОБРАБОТАНЫ!")
    print("="*60)


if __name__ == "__main__":
    main()
