# Security Best Practices

This document outlines critical security considerations when using the Multi-Chain EVM Token Collector.

---

## ⚠️ Critical Warnings

### 🔴 NEVER DO THIS

1. **Never commit `DONOR.txt` to Git**
   - Contains unencrypted private keys
   - Once public, funds can be stolen
   - Already in `.gitignore` - do NOT remove it

2. **Never share your private keys**
   - Not in Discord, Telegram, or any chat
   - Not via email or cloud storage
   - Not even with "support staff" (scam)

3. **Never run untrusted code**
   - Review changes before pulling updates
   - Check script source before running
   - Beware of malicious forks

4. **Never use main wallets as donors**
   - Always use separate wallets for collection
   - Keep main funds in cold storage
   - Assume donor wallets may be compromised

---

## 🔐 Private Key Management

### Storage Best Practices

#### ✅ DO:
- **Use separate wallets**: Create dedicated wallets for collection
- **Encrypt DONOR.txt**: Use tools like GPG
  ```bash
  gpg -c DONOR.txt  # Encrypt
  gpg DONOR.txt.gpg  # Decrypt when needed
  ```
- **Use environment variables**: Store keys in `.env` (not committed)
- **Backup securely**: Encrypted backups only
- **Delete after use**: Remove `DONOR.txt` when done

#### ❌ DON'T:
- Store keys in cloud sync folders (Dropbox, Google Drive)
- Leave keys in browser history or clipboard
- Email or message private keys
- Store keys in plain text long-term
- Reuse keys across multiple services

### Secure File Permissions

#### Linux/macOS:
```bash
# Make DONOR.txt readable only by you
chmod 600 DONOR.txt

# Verify permissions
ls -l DONOR.txt  # Should show: -rw-------
```

#### Windows:
```powershell
# Remove inheritance and grant only your user access
icacls DONOR.txt /inheritance:r
icacls DONOR.txt /grant:r "$env:USERNAME:(R,W)"
```

---

## 🛡️ Wallet Security

### Donor Wallet Setup

1. **Create Fresh Wallets**
   - Generate new wallets specifically for collection
   - Never reuse wallets with significant history
   - Consider them "burner" wallets

2. **Minimal Funding**
   - Only send tokens you need to collect
   - Don't store large amounts
   - Collect frequently

3. **Separate Recipient Wallet**
   - Use different wallet for receiving
   - Ideally a hardware wallet
   - Keep private key offline when possible

### Recipient Address Verification

**Before first run**, verify recipient address 3+ times:

```python
# In token_collector.py, add verification print
print(f"🔍 VERIFY: Tokens will be sent to: {RECIPIENT_ADDRESS}")
input("Press Enter if correct, Ctrl+C to abort...")
```

**Double-check**:
- Compare address character by character
- Use a block explorer to verify it's your address
- Send a test transaction first

---

## 🔒 Network Security

### RPC Endpoint Security

#### Trusted Public RPCs:
- Official network RPCs (e.g., `https://mainnet.era.zksync.io`)
- Reputable providers (LlamaNodes, Chainlist.org)
- Well-known services (Alchemy, Infura)

#### ⚠️ Risks of Unknown RPCs:
- May log your IP address
- Could intercept transaction data
- Might serve fake blockchain data
- Could inject malicious transactions

#### Mitigation:
```python
# Verify RPC connection before using
from web3 import Web3

def verify_rpc(rpc_url, expected_chain_id):
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("Not connected")
        
        actual_chain_id = w3.eth.chain_id
        if actual_chain_id != expected_chain_id:
            raise Exception(f"Chain ID mismatch: {actual_chain_id} != {expected_chain_id}")
        
        print(f"✓ RPC verified: {rpc_url}")
        return True
    except Exception as e:
        print(f"✗ RPC verification failed: {e}")
        return False

# Use before running
verify_rpc("https://mainnet.era.zksync.io", 324)
```

### Using VPN/Tor

**Pros**:
- Hides your real IP from RPC providers
- Adds privacy layer

**Cons**:
- May be blocked by some RPCs
- Slower connection speeds
- Tor not recommended (too slow for RPC calls)

**Recommendation**: Use trusted RPCs instead of relying on VPN.

---

## 🧪 Testing & Validation

### Pre-Production Checklist

Before running with real funds:

- [ ] **Test with 1 wallet** - Verify script works
- [ ] **Small amounts only** - Use $5-10 test tokens
- [ ] **Verify recipient address** - Check 3+ times
- [ ] **Monitor first transaction** - Watch on block explorer
- [ ] **Check gas calculations** - Ensure reasonable
- [ ] **Test auto-refuel** - If enabled, verify it works
- [ ] **Review logs** - Check for errors or warnings
- [ ] **Backup DONOR.txt** - Encrypted backup before deletion

### Transaction Verification

After each run:

1. **Check Block Explorers**
   - Verify all transactions confirmed
   - Check recipient address received funds
   - Review gas costs (should be reasonable)

2. **Compare Balances**
   ```python
   # Before run: Note balance of recipient
   # After run: Verify increase matches expected
   expected_tokens = sum_of_donor_balances
   actual_tokens = recipient_final_balance - recipient_initial_balance
   assert actual_tokens == expected_tokens, "Mismatch!"
   ```

3. **Review Logs**
   - Check for any errors
   - Verify all wallets processed
   - Ensure no failed transactions

---

## 🚨 Incident Response

### If Private Keys Compromised

1. **Immediate Actions**:
   - Stop running the script
   - Transfer remaining funds to new wallets ASAP
   - Revoke any approvals (use Revoke.cash)
   - Monitor for unauthorized transactions

2. **Investigation**:
   - How were keys exposed?
   - Were they committed to Git?
   - Was DONOR.txt in cloud storage?
   - Was computer infected with malware?

3. **Prevention**:
   - Generate new wallets
   - Secure storage (encrypted)
   - Review security practices

### If Tokens Sent to Wrong Address

1. **Verify Transaction**:
   - Check block explorer
   - Confirm destination address

2. **Recovery Options**:
   - If sent to your own address: No problem
   - If sent to exchange: Contact support (may recover)
   - If sent to random address: Likely unrecoverable
   - If sent to contract: Check if has recovery function

3. **Prevention**:
   - Always verify recipient address before running
   - Use checksums (capital letters in address)
   - Test with small amount first

---

## 🔍 Code Security

### Reviewing Updates

Before pulling updates:

```bash
# Check what changed
git diff origin/main

# Review specific file changes
git diff origin/main token_collector.py

# Check commit history
git log --oneline origin/main ^main
```

**Red flags**:
- New network requests to unknown domains
- Changes to recipient address handling
- Obfuscated code
- New dependencies without explanation
- Removal of security checks

### Dependency Security

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade web3 eth-account requests
```

### Running in Sandbox

For maximum security, run in isolated environment:

```bash
# Docker container (isolated)
docker run --rm -v $(pwd):/app -w /app python:3.9 python token_collector.py

# Virtual machine
# Run script in VM, not host machine
```

---

## 🔐 Encryption Guide

### Encrypting DONOR.txt with GPG

#### Installation:
```bash
# Linux
sudo apt-get install gnupg

# macOS
brew install gnupg

# Windows
# Download from: https://gnupg.org/download/
```

#### Usage:
```bash
# Encrypt DONOR.txt
gpg -c DONOR.txt
# Enter passphrase when prompted
# Creates DONOR.txt.gpg

# Delete original
shred -u DONOR.txt  # Linux
# or
rm DONOR.txt  # macOS/Windows

# Decrypt when needed
gpg DONOR.txt.gpg
# Enter passphrase
# Creates DONOR.txt

# Run script
python token_collector.py

# Re-encrypt
gpg -c DONOR.txt
shred -u DONOR.txt
```

### Encrypting with Python (Alternative)

```python
from cryptography.fernet import Fernet

# Generate key (save this securely!)
key = Fernet.generate_key()
print(f"Save this key: {key.decode()}")

# Encrypt DONOR.txt
cipher = Fernet(key)
with open('DONOR.txt', 'rb') as f:
    data = f.read()
encrypted = cipher.encrypt(data)

with open('DONOR.txt.enc', 'wb') as f:
    f.write(encrypted)

# Decrypt when needed
with open('DONOR.txt.enc', 'rb') as f:
    encrypted = f.read()
decrypted = cipher.decrypt(encrypted)

with open('DONOR.txt', 'wb') as f:
    f.write(decrypted)
```

---

## 🌐 Operational Security (OpSec)

### Information Leakage

**Avoid sharing**:
- Wallet addresses (can link to identity)
- Transaction hashes (can trace activity)
- Token amounts (reveals financial info)
- Exact timing of operations

**When asking for help**:
- Use example addresses (0x1234...5678)
- Share only necessary error messages
- Redact sensitive information
- Use new accounts for public questions

### IP Address Protection

**Considerations**:
- RPC providers see your IP address
- Blockchain transactions are public (but not linked to IP)
- Some providers may log requests

**Options**:
1. Use VPN (hides IP from RPC)
2. Use trusted RPCs only
3. Self-host RPC node (advanced)

### Computer Security

**Before running script**:
- [ ] Antivirus up to date
- [ ] No suspicious programs running
- [ ] Firewall enabled
- [ ] OS fully patched
- [ ] No remote access enabled

**Best practices**:
- Dedicated computer for crypto operations
- Linux generally more secure than Windows
- macOS good middle ground
- Keep system updated

---

## 📊 Monitoring & Logging

### Safe Logging Practices

**Default behavior**: Script prints to console  
**Risk**: Console output may contain addresses

**Mitigation**:
```python
# In token_collector.py, add address masking
def mask_address(address):
    return f"{address[:6]}...{address[-4:]}"

# Use in prints
print(f"Processing wallet: {mask_address(address)}")
```

### Transaction Monitoring

**Set up alerts**:
1. Use block explorer notifications (e.g., Etherscan)
2. Monitor recipient address for unexpected activity
3. Set up balance alerts

**Example (Etherscan API)**:
```python
import requests

def check_balance(address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&apikey={api_key}"
    response = requests.get(url)
    balance = int(response.json()['result']) / 1e18
    return balance

# Alert if balance changes unexpectedly
initial_balance = check_balance(RECIPIENT_ADDRESS, API_KEY)
# ... run script ...
final_balance = check_balance(RECIPIENT_ADDRESS, API_KEY)
if final_balance < initial_balance:
    print("⚠️ WARNING: Balance decreased!")
```

---

## 🛠️ Security Tools

### Useful Security Tools

1. **Revoke.cash**
   - URL: https://revoke.cash
   - Purpose: Revoke token approvals
   - Use: After collecting, revoke any leftover approvals

2. **Etherscan / Block Explorers**
   - Monitor transactions in real-time
   - Verify contract interactions
   - Check address history

3. **MythX / Slither**
   - Smart contract security analysis
   - Use if integrating new DeFi protocols

4. **Hardware Wallets**
   - Ledger, Trezor for recipient address
   - Maximum security for collected funds

### Malware Scanning

```bash
# Linux
sudo apt-get install clamav
clamscan -r /path/to/token-collector

# Windows
# Use Windows Defender or Malwarebytes

# macOS
# Use built-in XProtect or ClamXAV
```

---

## 📝 Security Checklist

### Before Every Run

- [ ] `DONOR.txt` is not in cloud sync folder
- [ ] Recipient address verified
- [ ] Script reviewed (no unexpected changes)
- [ ] Computer free of malware
- [ ] RPC endpoints trusted
- [ ] Private keys backed up (encrypted)
- [ ] Test run completed (if first time)

### After Every Run

- [ ] Verify transactions on block explorer
- [ ] Check recipient balance increased correctly
- [ ] Delete or re-encrypt `DONOR.txt`
- [ ] Review logs for errors
- [ ] Revoke unnecessary approvals (Revoke.cash)
- [ ] Monitor for 24h for unexpected activity

### Monthly Security Review

- [ ] Update dependencies (`pip list --outdated`)
- [ ] Check for script updates
- [ ] Review security practices
- [ ] Rotate wallets if needed
- [ ] Audit transaction history
- [ ] Verify no unauthorized access

---

## 🚀 Advanced Security

### Air-Gapped Signing (Maximum Security)

1. **Offline Computer**:
   - Never connected to internet
   - Holds private keys
   - Signs transactions

2. **Online Computer**:
   - Runs script
   - Broadcasts signed transactions
   - No private keys

3. **Process**:
   ```python
   # Online: Generate unsigned transaction
   tx = contract.functions.transfer(...).build_transaction(...)
   # Save to USB: unsigned_tx.json
   
   # Offline: Sign transaction
   signed_tx = account.sign_transaction(tx)
   # Save to USB: signed_tx.json
   
   # Online: Broadcast
   w3.eth.send_raw_transaction(signed_tx.rawTransaction)
   ```

### Multi-Signature Recipient

For maximum security, use multi-sig for recipient:

- **Gnosis Safe**: Requires multiple keys to spend
- **Benefit**: Even if one key compromised, funds safe
- **Setup**: https://safe.global

---

## 📚 Resources

### Security Guides
- **CryptoSec.info**: https://cryptosec.info
- **OWASP Blockchain**: https://owasp.org/www-project-blockchain-security/
- **Ethereum Security**: https://ethereum.org/en/security/

### Emergency Contacts
- **Etherscan Support**: https://etherscan.io/contactus
- **Exchange Support**: If tokens sent to exchange accidentally

### Security Audit Services
If adding custom code or integrations:
- **OpenZeppelin**: https://openzeppelin.com/security-audits/
- **CertiK**: https://certik.com
- **Trail of Bits**: https://www.trailofbits.com

---

## ⚖️ Legal & Compliance

### Know Your Jurisdiction

- **Tax Reporting**: Collecting tokens may be taxable event
- **AML/KYC**: Ensure compliance with local regulations
- **Record Keeping**: Maintain transaction records

### Disclaimer

This software is for educational purposes. Users are responsible for:
- Securing their private keys
- Complying with local laws
- Understanding risks involved
- Any financial losses incurred

**USE AT YOUR OWN RISK**

---

## 🆘 Getting Help Securely

### If You Need Support

1. **Check Documentation First**
   - README.md
   - SETUP.md
   - This file (SECURITY.md)

2. **Search Existing Issues**
   - GitHub Issues tab
   - Similar problems may be solved

3. **Open New Issue** (GitHub)
   - Describe problem clearly
   - **Redact all private information**
   - Include error messages (redacted)
   - Specify OS, Python version

4. **What NOT to Share**
   - Private keys (NEVER)
   - Seed phrases (NEVER)
   - Full addresses (mask: 0x1234...5678)
   - Exact transaction hashes (unless necessary)
   - Personal identifying information

---

## 🎯 Final Thoughts

Security is not optional. Follow these practices:

1. **Assume Compromise**: Operate as if someone is watching
2. **Defense in Depth**: Multiple layers of security
3. **Minimize Trust**: Verify everything, trust nothing
4. **Stay Updated**: Security landscape constantly evolves
5. **Be Paranoid**: Better safe than sorry

**Remember**: Cryptocurrency transactions are irreversible. Once tokens are sent to wrong address or keys are compromised, recovery is unlikely.

Stay safe! 🛡️
