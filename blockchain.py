#!/usr/bin/env python3

import binascii
import datetime
import hashlib


def to_hex(bytestring):
    """
    convert given little-endian bytestring to hex
    """
    return binascii.hexlify(bytestring[::-1])


def double_hash(bytestring):
    """
    double SHA256 hash given bytestring
    """
    return hashlib.sha256(hashlib.sha256(bytestring).digest()).digest()


class BlockChain:

    def __init__(self, data):
        self.data = data
        self.index = 0
        self.block_count = 0

    def blocks(self):
        """
        yields blocks one at a time
        """
        while self.index < len(self.data):
            yield self.parse_block()
            self.block_count += 1

    def hash_since(self, mark):
        """
        double hash data from given mark to current index and return in hex
        """
        return to_hex(double_hash(self.data[mark:self.index]))


    ## basic reading of little-endian integers of different widths

    def get_uint8(self):
        data = self.data[self.index]
        self.index += 1
        return data

    def get_uint16(self):
        return self.get_uint8() + (self.get_uint8() << 8)

    def get_uint32(self):
        return self.get_uint16() + (self.get_uint16() << 16)

    def get_uint64(self):
        return self.get_uint32() + (self.get_uint32() << 32)


    ## more involved data reading

    def get_bytestring(self, length=1):
        data = self.data[self.index:self.index + length]
        self.index += length
        return data

    def get_timestamp(self):
        return datetime.datetime.utcfromtimestamp(self.get_uint32())

    def get_hash(self):
        return to_hex(self.get_bytestring(32))

    def get_varlen_int(self):
        code = self.get_uint8()
        if code < 0xFD:
            return code
        elif code == 0xFD:
            return self.get_uint16()
        elif code == 0xFE:
            return self.get_uint32()
        elif code == 0xFF:
            return self.get_uint64()

    def get_script(self):
        script_length = self.get_varlen_int()
        script = self.get_bytestring(script_length)

        script_tokens = []

        script_index = 0
        while script_index < script_length:
            op_code = script[script_index]
            script_index += 1

            if op_code <= 75:
                script_tokens.append(script[script_index:script_index + op_code])
                script_index += op_code
            elif op_code == 118:
                script_tokens.append("OP_DUP")
            elif op_code == 136:
                script_tokens.append("OP_EQUALVERIFY")
            elif op_code == 169:
                script_tokens.append("OP_HASH160")
            elif op_code == 172:
                script_tokens.append("OP_CHECKSIG")
            else:
                print("unknown opcode", op_code)
                raise ValueError

        return script_tokens

    ## parsing data structures in block chain

    def parse_block(self):
        assert self.get_uint32() == 0xD9B4BEF9  # magic network id

        block_length = self.get_uint32()

        # mark current position for block hash calculation
        mark = self.index

        # read rest of block header
        block_data = {
            "size": block_length,
            "ver": self.get_uint32(),
            "prev_block": self.get_hash(),
            "mrkl_root": self.get_hash(),
            "timestamp": self.get_timestamp(),
            "bits": self.get_uint32(),
            "nonce": self.get_uint32()
        }

        # calculate hash
        block_data["hash"] = self.hash_since(mark)

        # read transactions
        transaction_count = self.get_varlen_int()
        block_data["transactions"] = [
            self.parse_transaction() for i in range(transaction_count)
        ]

        return block_data

    def parse_transaction(self):

        # mark current position for transaction hash calculation
        mark = self.index

        # read rest of transaction data
        transaction_data = {
            "ver": self.get_uint32(),
            "inputs": self.parse_inputs(),
            "outputs": self.parse_outputs(),
            "lock_time": self.get_uint32(),
        }

        # calculate hash
        transaction_data["hash"] = self.hash_since(mark)

        return transaction_data

    def parse_inputs(self):
        count = self.get_varlen_int()
        return [{
            "transaction_hash": self.get_hash(),
            "transaction_index": self.get_uint32(),
            "script": self.get_script(),
            "sequence_number": self.get_uint32(),
        } for i in range(count)]

    def parse_outputs(self):
        count = self.get_varlen_int()
        return [{
            "value": self.get_uint64(),
            "script": self.get_script(),
        } for i in range(count)]


if __name__ == "__main__":
    import pprint
    import sys

    filename = sys.argv[1]
    with open(filename, "rb") as f:
        data = f.read()
        block_chain = BlockChain(data)
        for block in block_chain.blocks():
            print()
            pprint.pprint(block)
