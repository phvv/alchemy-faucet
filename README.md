# Sepolia ETH Faucet

## Prerequisites

- Python
- macOS
- Wallet with sufficient Sepolia funds to act as faucet

## Installation & Set Up

### Dependencies

```bash
pip install -r requirements.txt
```

### Redis

```bash
# Install
brew install redis

# Start
redis-server
```

### Environment Variables

```bash
# Required: private key (to act as the faucet)
export PRIVATE_KEY="123..."

# Optional: custom Sepolia RPC endpoint
export SEPOLIA_RPC="https://sepolia-rpc-endpoint.com"
```

## Run the Faucet

```bash
python3 app.py
```

Access at: http://localhost:8080
