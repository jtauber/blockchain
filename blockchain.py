#!/usr/bin/env python3


class Base(object):
    def __init__(self, data, handler):
        self.data = data
        self.handler = handler
        self.index = 0
        self.init()
        self.parse()

    def init(self):
        pass

    def get_byte(self):
        data = self.data[self.index]
        self.index += 1
        return data

    def get_bytes(self, length=1):
        data = self.data[self.index:self.index + length]
        self.index += length
        return data

    def get_uint16(self):
        return self.get_byte() + self.get_byte() << 8

    def get_uint32(self):
        return self.get_uint16() + self.get_uint16() << 16

    def get_uint64(self):
        return self.get_uint32() + self.get_uint32() << 32

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


class Block(Base):

    def parse(self):
        magic_network_id = self.get_uint32()
        block_length = self.get_uint32()
        block_format_version = self.get_uint32()
        hash_of_previous_block = self.get_hash()
        merkle_root = self.get_hash()
        timestamp = self.get_uint32()
        bits = self.get_uint32()
        nonce = self.get_uint32()
        transaction_count = self.get_varlen_int()

        for i in range(transaction_count):
            Transaction(data)

        print(magic_network_id)


class Transaction(Base):

    def parse(self):
        version_number = self.get_uint32()
        input_count = self.get_varlen_int()

        for i in range(input_count):
            Input(data)

        output_count = self.get_varlen_int()

        for i in range(output_count):
            Output(data)

        transaction_lock_time = self.get_uint32()


class Input(Base):

    def parse(self):
        transaction_hash = self.get_hash()
        transaction_index = self.get_uint32()
        script_length = self.get_varlen_int()
        script = self.get_char(script_length)
        sequence_number = self.get_uint32()


class Output(Base):

    def parse(self):
        value = self.get_uint64()
        script_length = self.get_varlen_int()
        script = self.get_char(script_length)


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    with open(filename, "rb") as f:
        data = f.read()
        Block(data, None)
