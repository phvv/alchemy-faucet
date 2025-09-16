import os
import re
from flask import Flask, render_template, request, jsonify
from web3 import Web3
import redis

app = Flask(__name__)

PRIVATE_KEY = os.getenv('PRIVATE_KEY')
SEPOLIA_RPC = os.getenv('SEPOLIA_RPC', 'https://ethereum-sepolia-rpc.publicnode.com')
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
faucet_addr = w3.eth.account.from_key(PRIVATE_KEY).address

FAUCET_AMOUNT = Web3.to_wei(0.001, 'ether')
RATE_LIMIT_TIME = 12

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def valid_addr(addr):
    return re.match(r'^0x[a-fA-F0-9]{40}$', addr) is not None

def is_rate_limited(ip, addr):
    return r.exists(ip, addr.lower()) > 0

def set_rate_limit(ip, addr):
    expiry = int(RATE_LIMIT_TIME * 3600)
    r.set(ip, "1", ex=expiry)
    r.set(addr.lower(), "1", ex=expiry)

def send_eth(to_addr):
    gas_amt = 21000 # standard for ETH transfer
    gas_price = w3.eth.gas_price
    tx_fee = gas_amt * gas_price

    if w3.eth.get_balance(faucet_addr) < FAUCET_AMOUNT + tx_fee:
        return
    
    transaction = {
        'to': Web3.to_checksum_address(to_addr),
        'value': FAUCET_AMOUNT,
        'gas': gas_amt,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(faucet_addr),
        'chainId': 11155111
    }
    
    signed_txn = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    return tx_hash.hex()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faucet', methods=['POST'])
def faucet():
    try:
        addr = request.get_json()['addr']
        if not valid_addr(addr):
            return jsonify({'error': 'Invalid Ethereum address'}), 400
        
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if is_rate_limited(ip, addr):
            return jsonify({'error': f"IPs and addresses can request only once per {RATE_LIMIT_TIME} hours"}), 429
        
        tx_hash = send_eth(addr)
        if tx_hash is None:
            return jsonify({'error': "Faucet balance is too low"}), 500
        
        set_rate_limit(ip, addr)

        return jsonify({'tx_hash': tx_hash}), 200
        
    except Exception as error:
        return jsonify({'error': error}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
