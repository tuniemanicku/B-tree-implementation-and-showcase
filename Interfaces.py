from utils import *
import struct

class BTreeInterface:
    def __init__(self, filename, order):
        self.file = filename
        with open(filename, 'wb') as f:
            pass
        self.base_address = 0
        self.read_buffer = None
        self.write_address = 0
        self.write_buffer = None
        self.order = order
        self.node_count = 0
        self.modified = False
        # maximum page_size is determined for:
        # maximum 2d+1 pointers
        # maximum 2d key and data pointer pairs
        # integer containing current number of records in a node
        # parent pointer
        self.page_size = (2*order+1)*POINTER_SIZE + (2*order)*(KEY_SIZE + POINTER_SIZE) + RECORD_COUNT_SIZE + POINTER_SIZE
        self.keys_offset = (2*order+1)*POINTER_SIZE
        self.record_count_offset = (2*order+1)*POINTER_SIZE + (2*order)*(KEY_SIZE + POINTER_SIZE)
        print("Node size:",self.page_size)

    def get_new_node_address(self):
        self.node_count += 1
        return (self.node_count-1)*self.page_size

    def get_new_read_buffer(self, index):
        with open(self.file, 'rb') as f:
            self.base_address = index - (index % self.page_size)
            f.seek(self.base_address)
            self.read_buffer = f.read(self.page_size).ljust(self.page_size, b'\x00')
            self.modified = False

    def read(self, index):
        if self.write_address <= index < self.write_address + self.page_size:
            self.write_cached_records()
        if not self.read_buffer:
            self.get_new_read_buffer(index)
        if not (self.base_address <= index < self.base_address + self.page_size):
            self.get_new_read_buffer(index)
        return_value = self.read_buffer[index - self.base_address:index - self.base_address + POINTER_SIZE]
        return return_value if return_value else None

    def read_page(self, index):
        self.write_cached_records()
        if not self.read_buffer or (self.write_address == self.base_address and self.modified):
            self.get_new_read_buffer(index)
        if not (self.base_address <= index < self.base_address + self.page_size):
            self.get_new_read_buffer(index)
        return_value = self.read_buffer
        return bytearray(return_value) if return_value else None

    def get_new_write_buffer(self, index):
        with open(self.file, 'rb') as f:
            self.write_address = index - (index % self.page_size)
            f.seek(self.write_address)
            self.write_buffer = f.read(self.page_size).ljust(self.page_size, b'\x00')
            self.write_buffer = bytearray(self.page_size)

    def write_cached_records(self):
        with open(self.file, 'r+b') as f:
            f.seek(self.write_address)
            f.write(self.write_buffer)
            self.modified = True

    def write(self, index, value):
        if not self.write_buffer:
            self.get_new_write_buffer(index)
        if not (self.write_address <= index < self.write_address + self.page_size):
            self.write_cached_records()
            self.get_new_write_buffer(index)
        print(type(value))
        to_write = bytearray(value.to_bytes(4, byteorder='little'))
        self.write_buffer[index - self.write_address:index - self.write_address + POINTER_SIZE] = to_write
        self.modified = True

    def write_page(self, index, node):
        if not (self.write_address <= index < self.write_address + self.page_size):
            self.write_cached_records()
            self.get_new_write_buffer(index)
        self.write_buffer = node
        self.write_cached_records()

# class DataInterface:
#     def __init__(self, filename):
#         self.file = filename
#         self.read_buffer = None
#         self.write_buffer = None
#         self.read_buffer_base_address = 0
#         self.
#         with open(self.file, "wb"):
#             pass
#     def add_entry(self, key, record):
#         data = struct.pack("<i dd", key, record[VOLTAGE_ID], record[CURRENT_ID])
#         with open(self.file, 'ab') as f:
#             f.write(data)
#     def read_entry(self, search_key):
#         with open(self.file, 'rb') as f:
#             voltage, current = None, None
#             data = f.read(PAIR_SIZE)
#             if data:
#                 key, voltage, current = struct.unpack("<i dd", data)
#             found = False
#             while not found and data:
#                 if data:
#                     key, voltage, current = struct.unpack("<i dd", data)
#                 if key == search_key:
#                     found = True
#                 data = f.read(PAIR_SIZE)
#             return (voltage, current) if found else None

import os

class DataInterface:
    def __init__(self, filename):
        self.file = filename
        self.read_buffer = []  # (key, voltage, current)
        self.write_buffer = []
        self.write_buffer_base_index = None
        self.read_buffer_base_index = None
        self.total_records = 0
        self.autoindexing = 0

        self.read_count = 0
        self.write_count = 0

        # Ensure file exists
        if not os.path.exists(self.file):
            with open(self.file, "wb"):
                pass
        else:
            self.total_records = os.path.getsize(self.file) // PAIR_SIZE

    def __del__(self):
        self.flush_write_buffer()

    # record: (key, voltage, current)
    def write_entry(self, index, record):
        if not index:
            index = self.autoindexing
            self.autoindexing += 1
        page_start = (index // DATA_PAGE_SIZE) * DATA_PAGE_SIZE

        if self.write_buffer_base_index != page_start:
            self.flush_write_buffer()
            self.write_buffer = [(0, 0.0, 0.0)] * DATA_PAGE_SIZE
            self.write_buffer_base_index = page_start

        rel_idx = index - page_start
        self.write_buffer[rel_idx] = record

        if page_start + DATA_PAGE_SIZE > self.total_records:
            self.flush_write_buffer()
        return index

    def flush_write_buffer(self):
        if not self.write_buffer or self.write_buffer_base_index is None:
            return

        with open(self.file, "r+b") as f:
            f.seek(self.write_buffer_base_index * PAIR_SIZE)
            for rec in self.write_buffer:
                f.write(struct.pack("<i dd", *rec))

        end_index = self.write_buffer_base_index + len(self.write_buffer)
        if end_index > self.total_records:
            self.total_records = end_index

        self.write_buffer = []
        self.write_buffer_base_index = None
        self.write_count += 1

    # -------------------- READ --------------------
    def read_entry(self, index):
        self.flush_write_buffer()
        if index < 0:
            return None

        if self.read_buffer_base_index is not None:
            start = self.read_buffer_base_index
            end = start + len(self.read_buffer)
            if start <= index < end:
                _, voltage, current = self.read_buffer[index - start]
                return (voltage, current)

        page_start = (index // DATA_PAGE_SIZE) * DATA_PAGE_SIZE
        with open(self.file, "rb") as f:
            f.seek(page_start * PAIR_SIZE)
            data = f.read(DATA_PAGE_SIZE * PAIR_SIZE)

        self.read_buffer = []
        for i in range(0, len(data), PAIR_SIZE):
            rec = struct.unpack("<i dd", data[i:i+PAIR_SIZE])
            self.read_buffer.append(rec)

        while len(self.read_buffer) < DATA_PAGE_SIZE:
            self.read_buffer.append((0, 0.0, 0.0))

        self.read_buffer_base_index = page_start
        self.read_count += 1

        buffer_index = index - page_start
        if 0 <= buffer_index < len(self.read_buffer):
            _, voltage, current = self.read_buffer[buffer_index]
            return (voltage, current)
        else:
            return None