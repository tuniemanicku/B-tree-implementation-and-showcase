from utils import *

class BTreeInterface:
    def __init__(self, filename, order):
        self.file = filename
        self.base_address = 0
        self.read_buffer = None
        self.write_address = 0
        self.write_buffer = None
        self.order = order
        self.page_size = (2*order+1)*POINTER_SIZE + (2*order)*KEY_SIZE + RECORD_COUNT_SIZE + POINTER_SIZE
        print("Page size:",self.page_size)

    def get_new_read_buffer(self, index):
        with open(self.file, 'rb') as f:
            self.base_address = index - (index % self.page_size)
            f.seek(self.base_address)
            self.read_buffer = f.read(self.page_size).ljust(self.page_size, b'\x00')

    def read(self, index):
        if self.write_address <= index < self.write_address + self.page_size:
            self.write_cached_records()
        if not self.read_buffer:
            self.get_new_read_buffer(index)
        if not (self.base_address <= index < self.base_address + self.page_size):
            self.get_new_read_buffer(index)
        return_value = self.read_buffer[index - self.base_address:index - self.base_address + POINTER_SIZE]
        return return_value if return_value else None

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

    def write(self, index, value):
        if not self.write_buffer:
            self.get_new_write_buffer(index)
        if not (self.write_address <= index < self.write_address + self.page_size):
            self.write_cached_records()
            self.get_new_write_buffer(index)
        self.write_buffer[index - self.write_address:index - self.write_address + POINTER_SIZE] = value
