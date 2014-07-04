#!/usr/bin/env python3

from blockchain import BlockChain, public_key_to_address, ripemd160_to_address

from collections import defaultdict

import sys

BALANCES = defaultdict(int)
OUTPUTS = {}

filename = sys.argv[1]
with open(filename, "rb") as f:
    data = f.read()
    block_chain = BlockChain(data)
    for block in block_chain.blocks():
        for transaction in block["transactions"]:
            for inp in transaction["inputs"]:
                if inp["transaction_hash"] == b"0000000000000000000000000000000000000000000000000000000000000000":
                    pass  # generated
                else:
                    address, value = OUTPUTS[(inp["transaction_hash"], inp["transaction_index"])]
                    BALANCES[address] -= value
            for output_num, output in enumerate(transaction["outputs"]):
                transaction_hash = transaction["hash"]
                index = output_num
                value = output["value"]
                script = output["script"]
                if len(script) == 2 and script[1] == "OP_CHECKSIG":
                    address = public_key_to_address(script[0])
                elif len(script) == 5 and (
                    script[0] == "OP_DUP" and
                    script[1] == "OP_HASH160" and
                    script[3] == "OP_EQUALVERIFY" and
                    script[4] == "OP_CHECKSIG"
                ):
                    address = ripemd160_to_address(script[2])
                else:
                    address = "invalid"
                OUTPUTS[(transaction_hash, output_num)] = address, value
                BALANCES[address] += value

for address, balance in sorted(BALANCES.items(), key=lambda x: x[1]):
    print(address, balance / 100000000)
