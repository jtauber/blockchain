#!/usr/bin/env python3

import binascii
import datetime
import hashlib


class BlockChain:
    def __init__(self, data, handler=None):
        self.data = data
        self.handler = handler
        self.index = 0
        self.block_count = 0

        while self.block_count < 2: #self.index < len(self.data):
            self.parse_block()
            self.block_count += 1

    def get_byte(self):
        data = self.data[self.index]
        self.index += 1
        return data

    def peek_bytes(self, length=1):
        data = self.data[self.index:self.index + length]
        return data[::-1]

    def get_bytes(self, length=1):
        data = self.data[self.index:self.index + length]
        self.index += length
        return data[::-1]

    def get_uint16(self):
        return self.get_byte() + (self.get_byte() << 8)

    def get_uint32(self):
        return self.get_uint16() + (self.get_uint16() << 16)

    def get_uint64(self):
        return self.get_uint32() + (self.get_uint32() << 32)

    def get_timestamp(self):
        return datetime.datetime.utcfromtimestamp(self.get_uint32())

    def get_hash(self):
        return self.get_bytes(32)

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

    def parse_block(self):
        magic_network_id = self.get_uint32()
        block_length = self.get_uint32()

        header_to_hash = self.peek_bytes(80)[::-1]
        block_hash = hashlib.sha256(hashlib.sha256(header_to_hash).digest()).digest()[::-1]

        block_format_version = self.get_uint32()
        hash_of_previous_block = self.get_hash()
        merkle_root = self.get_hash()
        timestamp = self.get_timestamp()
        bits = self.get_uint32()
        nonce = self.get_uint32()

        transaction_count = self.get_varlen_int()

        print("""
{}.
    hash: {}
    ver: {}
    prev_block: {}
    mrkl_root: {}
    timestamp: {}
    bits: {} [0x{:X}]
    nonce: {}
    n_tx: {}
    size: {}
        """.format(
            self.block_count,
            binascii.hexlify(block_hash),
            block_format_version,
            binascii.hexlify(hash_of_previous_block),
            binascii.hexlify(merkle_root),
            timestamp,
            bits, bits,
            nonce,
            transaction_count,
            block_length,
        ))

        for i in range(transaction_count):
            self.parse_transaction()

    def parse_transaction(self):
        version_number = self.get_uint32()
        input_count = self.get_varlen_int()

        for i in range(input_count):
            self.parse_input()

        output_count = self.get_varlen_int()

        for i in range(output_count):
            self.parse_output()

        transaction_lock_time = self.get_uint32()

    def parse_input(self):
        transaction_hash = self.get_hash()
        transaction_index = self.get_uint32()
        script_length = self.get_varlen_int()
        script = self.get_bytes(script_length)
        sequence_number = self.get_uint32()

    def parse_output(self):
        value = self.get_uint64()
        script_length = self.get_varlen_int()
        script = self.get_bytes(script_length)


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    with open(filename, "rb") as f:
        data = f.read()
        BlockChain(data)
