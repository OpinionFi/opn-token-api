from flask import Flask, jsonify, send_from_directory
from web3 import Web3 # type: ignore
import requests
import json
import os
from eth_utils import to_checksum_address

app = Flask(__name__)

# BSC RPC URL
BSC_RPC = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Token Kontratı Detayları
TOKEN_CONTRACT_ADDRESS = "0xCAf76feee43a2A7DB0FBe23Ee4018757f352a1ff"

TOKEN_ABI_JSON = '''
[{"inputs":[{"internalType":"address","name":"initialOwner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
'''
TOKEN_ABI = json.loads(TOKEN_ABI_JSON)

# Kontratı başlat
contract = web3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS), abi=TOKEN_ABI)

# Kilitli bakiyeler veya dolaşıma çıkmaması gereken adresler
EXCLUDED_ADDRESSES = [
    "0x000000000000000000000000000000000000dEaD",  # Burn adresi
    "0xCAf76feee43a2A7DB0FBe23Ee4018757f352a1ff",  # Takım cüzdanı veya kilitli adres
]



# Dolaşımdaki arzı hesapla
def get_circulating_supply():
    total_supply = contract.functions.totalSupply().call() / DECIMALS
    excluded_supply = sum(contract.functions.balanceOf(Web3.to_checksum_address(addr)).call() for addr in EXCLUDED_ADDRESSES) / DECIMALS
    circulating_supply = total_supply - excluded_supply
    return circulating_supply

# Token fiyatını al (CoinGecko API)
def get_token_price():
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "opinion-finance", "vs_currencies": "usd"}  
        )
        response.raise_for_status()
        data = response.json()
        return data.get("opinion-finance", {}).get("usd", 0)  # Hata olursa 0 döndür
    except requests.exceptions.RequestException:
        return 0  # Hata durumunda fiyatı 0 olarak belirle


# 18 decimal faktörü
DECIMALS = 10**18  

# Toplam arzı döndüren endpoint
@app.route('/total_supply', methods=['GET'])
def total_supply():
    try:
        total_supply = contract.functions.totalSupply().call() / DECIMALS  # 10¹⁸'e bölerek düzelt
        return jsonify({
            "": total_supply
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dolaşımdaki arzı döndüren endpoint
@app.route('/circulating_supply', methods=['GET'])
def circulating_supply():
    try:
        circulating_supply = get_circulating_supply()
        return jsonify({
            "": circulating_supply
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Market cap hesaplama endpoint'i
@app.route('/market_cap', methods=['GET'])
def market_cap():
    try:
        circulating_supply = get_circulating_supply()
        token_price = get_token_price()
        market_cap = circulating_supply * token_price
        return jsonify({
            "market_cap_usd": market_cap,
            "circulating_supply": circulating_supply,
            "token_price_usd": token_price
        })
    except Exception as e:
        return jsonify({"message: this page is working": str(e)}), 500

@app.route('/')
def home():
    return "Opinion Finance API!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
