# Setup Guide

This guide will walk you through setting up and running the Multi-Chain EVM Token Collector for the first time.

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **OS**: Windows, Linux, or macOS
- **RAM**: 2GB minimum (4GB recommended)
- **Internet**: Stable connection for RPC calls

### Required Knowledge
- Basic command line usage
- Understanding of cryptocurrency wallets and private keys
- Familiarity with EVM networks

---

## Installation

### Step 1: Download the Project

```bash
# Clone from GitHub
git clone https://github.com/yourusername/token-collector.git
cd token-collector

# Or download ZIP and extract
```

### Step 2: Set Up Python Environment

#### Windows
```powershell
# Check Python version
python --version  # Should be 3.8+

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "from web3 import Web3; print('✓ Web3.py installed')"
python -c "from eth_account import Account; print('✓ eth-account installed')"
python -c "import requests; print('✓ requests installed')"
```

All three lines should print success messages.

---

## Configuration

### Option 1: Direct Configuration (Quickest)

1. Open `token_collector.py` in a text editor
2. Find lines 15-17 (around the top of the file)
3. Replace the placeholder values:

```python
# Before:
RECIPIENT_ADDRESS = "0xYourRecipientAddressHere"
RECIPIENT_ADDRESS_KEY = "YOUR_PRIVATE_KEY_HERE"
DONOR_FILE = "DONOR.txt"

# After:
RECIPIENT_ADDRESS = "0x1234567890abcdef1234567890abcdef12345678"  # Your wallet
RECIPIENT_ADDRESS_KEY = "0xabcd..."  # Your private key (for auto-refuel)
DONOR_FILE = "DONOR.txt"  # Keep as-is
```

### Option 2: Environment Variables (Recommended)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file:
```bash
RECIPIENT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
RECIPIENT_PRIVATE_KEY=0xabcd...
DONOR_FILE=DONOR.txt
MIN_BALANCE_USD=0.05
AUTO_REFUEL_GAS=True
```

3. Modify `token_collector.py` to load from `.env`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

RECIPIENT_ADDRESS = os.getenv('RECIPIENT_ADDRESS')
RECIPIENT_ADDRESS_KEY = os.getenv('RECIPIENT_PRIVATE_KEY')
```

### Configuration Parameters Explained

| Parameter | Purpose | Recommended Value |
|-----------|---------|-------------------|
| `RECIPIENT_ADDRESS` | Where tokens will be sent | Your main wallet address |
| `RECIPIENT_ADDRESS_KEY` | For auto-refuel feature | Private key of recipient (optional) |
| `DONOR_FILE` | File with donor private keys | `DONOR.txt` |
| `MIN_BALANCE_USD` | Skip tokens below this value | `0.05` ($0.05 USD) |
| `AUTO_REFUEL_GAS` | Auto-refuel low gas wallets | `True` |
| `MIN_GAS_REFUEL_AMOUNT` | Minimum refuel amount | `0.002` (in native token) |
| `MAX_PARALLEL_WALLETS` | Concurrent processing | `5-25` (start low) |
| `PAUSE_BETWEEN_WALLETS` | Delay between wallets | `7` seconds |
| `GAS_PRICE_MULTIPLIER` | Gas price buffer | `1.2` (20% extra) |

---

## Adding Donor Wallets

### Step 1: Create DONOR.txt

```bash
# Create the file
touch DONOR.txt

# Or on Windows:
type nul > DONOR.txt
```

### Step 2: Add Private Keys

Open `DONOR.txt` and add your private keys (one per line):

```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba
```

**Important**:
- One private key per line
- Can include or omit `0x` prefix
- No spaces or extra characters
- Maximum recommended: 100 wallets per run

### Step 3: Verify Format

```bash
# Should show number of lines (= number of wallets)
wc -l DONOR.txt

# Or on Windows:
powershell (Get-Content DONOR.txt).Count
```

---

## First Run (Test Mode)

### Step 1: Start with 1-2 Wallets

Edit `DONOR.txt` to include only 1-2 test wallets with small amounts.

### Step 2: Reduce Parallelism

Edit `token_collector.py`:
```python
MAX_PARALLEL_WALLETS = 1  # Process one at a time
PAUSE_BETWEEN_WALLETS = 15  # Longer pauses
```

### Step 3: Run the Script

```bash
python token_collector.py
```

### Step 4: Monitor Output

You should see output like:
```
================================================================================
Загружено 2 приватных ключей из DONOR.txt
================================================================================

############################################################
# Сеть: zkSync ERA
############################################################
✓ Подключено к zkSync ERA

[Кошелек: 0x1234...5678]
────────────────────────────────────────────────────────
[USDC]
  Баланс: 10.500000 USDC
  Цена: $1.00/USDC
  → Отправка 10.500000 USDC...
  ✓ Транзакция отправлена: 0xabcd...
  ✓ Транзакция подтверждена!
```

### Step 5: Verify Tokens Received

Check your `RECIPIENT_ADDRESS` on a block explorer:
- zkSync ERA: https://explorer.zksync.io
- Arbitrum: https://arbiscan.io
- Ethereum: https://etherscan.io

---

## Production Run

### Step 1: Increase Parallelism

After successful test:
```python
MAX_PARALLEL_WALLETS = 25  # Up to 25 concurrent
PAUSE_BETWEEN_WALLETS = 7  # Normal pauses
```

### Step 2: Add All Donor Wallets

Add all private keys to `DONOR.txt`.

### Step 3: Run Full Collection

```bash
python token_collector.py
```

### Step 4: Monitor Progress

The script will:
1. Process up to 25 wallets simultaneously
2. Show real-time progress for each wallet
3. Report total collected at the end

**Expected Time** (100 wallets):
- Single-threaded: ~7-8 hours
- 5 threads: ~1.5-2 hours
- 25 threads: ~20-30 minutes

---

## RPC Configuration

### Using Default Public RPCs

The script comes pre-configured with public RPCs that work for most users:

```python
"Ethereum": {
    "rpc": "https://eth.llamarpc.com",  # Free public RPC
    ...
}
```

### Upgrading to Paid RPCs (Recommended for Large Batches)

For better reliability with many wallets, consider paid RPCs:

#### Alchemy Setup

1. Sign up at https://www.alchemy.com
2. Create an app for each network you need
3. Copy your RPC URLs
4. Replace in `token_collector.py`:

```python
"Ethereum": {
    "rpc": "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY",
    ...
},
"Arbitrum": {
    "rpc": "https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY",
    ...
}
```

#### Infura Setup

Similar process:
1. Sign up at https://www.infura.io
2. Create project
3. Get API key
4. Replace RPC URLs:

```python
"Ethereum": {
    "rpc": "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
    ...
}
```

### Testing RPC Endpoints

```python
from web3 import Web3

# Test connection
w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
print(f"Connected: {w3.is_connected()}")
print(f"Latest block: {w3.eth.block_number}")
```

---

## Performance Tuning

### Conservative (Most Stable)
```python
MAX_PARALLEL_WALLETS = 5
PAUSE_BETWEEN_WALLETS = 15
GAS_PRICE_MULTIPLIER = 1.5  # 50% buffer
```
- Best for: First runs, unreliable internet
- Speed: Slow
- Reliability: Highest

### Balanced (Recommended)
```python
MAX_PARALLEL_WALLETS = 15
PAUSE_BETWEEN_WALLETS = 7
GAS_PRICE_MULTIPLIER = 1.2  # 20% buffer
```
- Best for: Most users
- Speed: Medium
- Reliability: Good

### Aggressive (Fast but Risky)
```python
MAX_PARALLEL_WALLETS = 25
PAUSE_BETWEEN_WALLETS = 3
GAS_PRICE_MULTIPLIER = 1.1  # 10% buffer
```
- Best for: Paid RPCs, good internet
- Speed: Fastest
- Reliability: Lower (more RPC errors)

---

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'web3'"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "SyntaxError" or "Invalid syntax"

**Solution**: Check Python version
```bash
python --version  # Should be 3.8+
```

### "FileNotFoundError: [Errno 2] No such file or directory: 'DONOR.txt'"

**Solution**: Create DONOR.txt in same directory as script
```bash
touch DONOR.txt
```

### "ValueError: {'code': -32000, 'message': 'insufficient funds for gas'}"

**Solutions**:
1. Enable auto-refuel: `AUTO_REFUEL_GAS = True`
2. Manually add gas to donor wallets
3. Lower gas multiplier: `GAS_PRICE_MULTIPLIER = 1.1`

### "Connection timeout" or "RPC error"

**Solutions**:
1. Check internet connection
2. Try different RPC endpoint
3. Reduce parallelism: `MAX_PARALLEL_WALLETS = 5`
4. Upgrade to paid RPC (Alchemy, Infura)

### Script Stops or Hangs

**Solutions**:
1. Check RPC rate limits
2. Lower parallelism
3. Increase pauses between wallets
4. Check for stuck transactions on block explorer

---

## Running as Background Service

### Linux (systemd)

1. Create service file `/etc/systemd/system/token-collector.service`:
```ini
[Unit]
Description=Token Collector Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/token-collector
ExecStart=/path/to/venv/bin/python token_collector.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

2. Start service:
```bash
sudo systemctl start token-collector
sudo systemctl status token-collector
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `token_collector.py`
7. Start in: `C:\path\to\token-collector`

### Docker (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY token_collector.py .
COPY DONOR.txt .

CMD ["python", "token_collector.py"]
```

Build and run:
```bash
docker build -t token-collector .
docker run --rm token-collector
```

---

## Security Checklist

Before first run:

- [ ] `DONOR.txt` is in `.gitignore`
- [ ] Private keys never committed to Git
- [ ] Recipient address verified multiple times
- [ ] Test run completed with small amounts
- [ ] Backup of DONOR.txt stored securely
- [ ] Auto-refuel disabled if not needed
- [ ] RPC endpoints trusted and secure
- [ ] Python environment is clean (no malware)

---

## Next Steps

After successful setup:

1. **Read NETWORKS.md** - Understand supported networks
2. **Read DEFI.md** - Learn about DeFi integrations
3. **Read SECURITY.md** - Best practices for safety
4. **Monitor first runs** - Check transactions on block explorers
5. **Optimize settings** - Tune for your use case
6. **Schedule runs** - Set up automation if needed

---

## Getting Help

### Check Logs

The script outputs detailed logs. Look for:
- ✓ Success indicators
- ⚠ Warning messages
- ✗ Error messages

### Common Issues

See **Troubleshooting** section above.

### Community Support

- **GitHub Issues**: Report bugs or ask questions
- **Documentation**: Read NETWORKS.md and DEFI.md
- **Block Explorers**: Verify transactions on-chain

---

## Advanced Configuration

### Custom Token Addition

Add tokens to specific networks in `token_collector.py`:

```python
"YourNetwork": {
    "rpc": "...",
    "chain_id": 123,
    "native_symbol": "ETH",
    "tokens": [
        {
            "symbol": "CUSTOM",
            "address": "0x..."
        }
    ]
}
```

### Custom DeFi Protocol

See **DEFI.md** for guide on integrating new protocols.

### Network Addition

See **NETWORKS.md** for guide on adding new chains.

---

## Maintenance

### Regular Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```

### Log Rotation

If running long-term, consider log rotation:
```bash
# Linux cron job
0 0 * * * find /path/to/logs -name "*.log" -mtime +30 -delete
```

### Wallet Cleanup

Periodically remove processed wallets from `DONOR.txt` to avoid reprocessing.

---

## Conclusion

You're now ready to run the Multi-Chain EVM Token Collector! 

**Remember**:
- Start small (1-2 wallets)
- Verify transactions
- Monitor for errors
- Optimize gradually

Happy collecting! 🪙
