#!/usr/bin/env python3

import binascii
import datetime
import hashlib
import pprint


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

    def __init__(self, data, handler=None):
        self.data = data
        self.handler = handler
        self.index = 0
        self.block_count = 0

        while self.block_count < 2: #self.index < len(self.data):
            print()
            print(self.block_count)
            pprint.pprint(self.parse_block())
            self.block_count += 1

    def hash_since(self, mark):
        """
        double hash data from given mark to current index and return in hex
        """
        return to_hex(double_hash(self.data[mark:self.index]))

    def get_byte(self):
        data = self.data[self.index]
        self.index += 1
        return data

    def get_bytes(self, length=1):
        data = self.data[self.index:self.index + length]
        self.index += length
        return data

    def get_uint16(self):
        return self.get_byte() + (self.get_byte() << 8)

    def get_uint32(self):
        return self.get_uint16() + (self.get_uint16() << 16)

    def get_uint64(self):
        return self.get_uint32() + (self.get_uint32() << 32)

    def get_timestamp(self):
        return datetime.datetime.utcfromtimestamp(self.get_uint32())

    def get_hash(self):
        return to_hex(self.get_bytes(32))

    def get_varlen_int(self):
        code = self.get_byte()
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
        return self.get_bytes(script_length)

    def parse_block(self):
        magic_network_id = self.get_uint32()
        block_length = self.get_uint32()

        mark = self.index

        block_format_version = self.get_uint32()
        hash_of_previous_block = self.get_hash()
        merkle_root = self.get_hash()
        timestamp = self.get_timestamp()
        bits = self.get_uint32()
        nonce = self.get_uint32()

        block_hash = self.hash_since(mark)

        transaction_count = self.get_varlen_int()
        transactions = [self.parse_transaction() for i in range(transaction_count)]

        return {
            "hash": block_hash,
            "var": block_format_version,
            "prev_block": hash_of_previous_block,
            "mrkl_root": merkle_root,
            "timestamp": timestamp,
            "bits": bits,
            "nonce": nonce,
            "n_tx": transaction_count,
            "size": block_length,
            "transactions": transactions,
        }

    def parse_transaction(self):

        mark = self.index

        version_number = self.get_uint32()
        inputs = self.parse_inputs()
        outputs = self.parse_outputs()
        lock_time = self.get_uint32()

        transaction_hash = self.hash_since(mark)

        return {
            "hash": transaction_hash,
            "var": version_number,
            "inputs": inputs,
            "outputs": outputs,
            "lock_time": lock_time,
        }

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
    import sys

    filename = sys.argv[1]
    with open(filename, "rb") as f:
        data = f.read()
        BlockChain(data)
