import os
import json
import logging
import decimal
import math

from eth_account import Account
from web3 import Web3

logLevel = os.getenv('LOG_LEVEL', "info")
logLevels = {
    "error": logging.ERROR,
    "warn": logging.WARN,
    "debug": logging.DEBUG,
    "info": logging.INFO
}

# Reads the dictionary and returns the value of the key, the default value is set to loggin.INFO
loggedLevel = logLevels.get(logLevel, logging.INFO)

logging.basicConfig(level=loggedLevel,
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("Log level(LOG_LEVEL): {logLevel}".format(
    logLevel=logLevel))

dsbContractAddress = Web3.to_checksum_address(
    "0xdc4CbCbc5f5fd29E01bde4D7A76F0B1046f9Bfac")

dsbOperatorKey = "<YOUR_PRIVATE_KEY>"
dsbOperatorAddress = Account.from_key(dsbOperatorKey).address

rpcURL = "https://devnet.neonevm.org"
w3 = Web3(Web3.HTTPProvider(rpcURL,
                            request_kwargs={'timeout': 15}))

gasPrice = w3.eth.gas_price
totalGasFee = w3.from_wei(0, 'wei')


file_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "abi", "distribute.abi")
with open(file_path, "r") as f:
    abi_json = json.load(f)
abi = json.dumps(abi_json, indent=2)


w3Dsb = w3.eth.contract(
    abi=abi, address=dsbContractAddress)


def sendDistributeTX(fromKey, fromAddress, dsbAddress):
    nonce = w3.eth.get_transaction_count(
        fromAddress, block_identifier='finalized')

    sendData = w3Dsb.encodeABI('distribute')

    estimateGas = w3.eth.estimate_gas({
        'to': dsbAddress,
        'from': fromAddress,
        'data': sendData
    })

    logging.info("The estimate gas of distribute: {estimateGas}".format(
        estimateGas=estimateGas))

    logging.info("The estimate gas of distribute: {estimateGas}".format(
        estimateGas=math.ceil(estimateGas * 1.2)))

    logging.info("The gas price of distribute: {gasPrice}".format(
        gasPrice=gasPrice))

    logging.info("The estimate total fee: {fee}".format(
        fee=math.ceil(estimateGas * 1.2 * gasPrice)))

    transaction = {'to': dsbAddress,
                   'from': fromAddress,
                   'gas': math.ceil(estimateGas * 1.2),
                   'gasPrice': gasPrice,
                   'data': sendData,
                   'nonce': nonce}

    logging.info("The transaction: {transaction}".format(
        transaction=transaction))

    singnedTX = w3.eth.account.sign_transaction(transaction, fromKey)

    while True:
        try:
            logging.info("Send distribute raw TX")
            txHash = w3.eth.send_raw_transaction(singnedTX.rawTransaction)
            logging.info("Tx: {}".format(txHash.hex()))
        except Exception as e:
            logging.error('Exception: ' + str(e))
        break
    while True:
        try:
            logging.info("Get distribute receipt")
            w3.eth.wait_for_transaction_receipt(
                txHash, timeout=10, poll_latency=1)
        except Exception as e:
            logging.error('Exception: ' + str(e))
        break
    return txHash.hex()


balance = w3.from_wei(
    w3.eth.get_balance(dsbContractAddress), 'ether')
logging.info('Total collect gas fee: {totalGasFee}'.format(
    totalGasFee=totalGasFee / decimal.Decimal("1E18")))

logging.info("The distribute contract address {address}, amount: {balance}".format(
    address=dsbContractAddress, balance=balance))

sendDistributeTX(
    dsbOperatorKey, dsbOperatorAddress, dsbContractAddress)
