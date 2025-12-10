from BTree import BTree
from Interfaces import *
import random

class TreeLoader:
    def __init__(self, filename, btree):
        self.filename = filename
        self.btree = btree

    def load(self):
        with open(self.filename, "rb") as f:
            instruction_type = int.from_bytes(f.read(INSTRUCTION_TYPE_LENGTH), byteorder="little")
            while instruction_type:
                if instruction_type == ADD_INSTR:
                    key, u, i = struct.unpack("<i dd", f.read(PAIR_SIZE))
                    self.btree.add_record(key=key, record=(u, i))
                elif instruction_type == DELETE_INSTR:
                    print("not yet implemented")
                elif instruction_type == UPDATE_INSTR:
                    print("not yet implemented")

                instruction_type = int.from_bytes(f.read(INSTRUCTION_TYPE_LENGTH), byteorder="little")

    def write(self):
        with open(DEFAULT_TEST_DATA_FILENAME, "wb") as f:
            for i in range(RECORDS_TO_GENERATE):
                f.write(ADD_INSTR.to_bytes(INSTRUCTION_TYPE_LENGTH, "little"))
                rand_key = random.randint(1,15)
                rand_u = random.random()*20
                rand_i = random.random()
                f.write(struct.pack("<i dd", rand_key, rand_u, rand_i))

    def write_test_data(self):
        with open(DEFAULT_TEST_DATA_FILENAME, "wb") as f:
            to_add = [1, 2, 3, 5, 6, 7, 8, 10]
            for i in range(len(to_add)):
                f.write(ADD_INSTR.to_bytes(INSTRUCTION_TYPE_LENGTH, "little"))
                f.write(struct.pack("<i dd", to_add[i], to_add[i], to_add[i]))

#tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME, btree=BTree())
#tl.write_test_data()

def dump_test_data(filename):
    print(f"--- Dumping contents of {filename} ---")

    with open(filename, "rb") as f:
        index = 0
        while True:
            instr_bytes = f.read(INSTRUCTION_TYPE_LENGTH)
            if not instr_bytes:
                break  # EOF reached cleanly

            instruction_type = int.from_bytes(instr_bytes, "little")

            print(f"[{index}] Instruction:", instruction_type)
            index += 1

            # Only ADD_INSTR exists in your generator
            if instruction_type == ADD_INSTR:
                key = int.from_bytes(f.read(KEY_SIZE), "little")
                u, i = struct.unpack("<dd", f.read(RECORD_SIZE))
                print(f"    Key   = {key}")
                print(f"    Value = (u={u}, i={i})")
            else:
                print(f"    Unknown instruction type: {instruction_type}")
                break

        print("--- End of file ---")
#dump_test_data(DEFAULT_TEST_DATA_FILENAME)

# ----------------------------TESTING THE B-TREE INTERFACE------------------------------
# # B-tree interface tests
# tmp = BTreeInterface("test.bin", 2)
# for i in range(10):
#     tmp.write(index=i, value=[i+97,0,0,0])
# for i in range(0,tmp.page_size,4):
#     print(tmp.read(index=i))
#
# tmp.write(44,[1,2,3,4])
# tmp.write_cached_records()
#
# # display bin file
def hexdump_4byte(file_path):
    with open(file_path, "rb") as f:
        offset = 0
        while chunk := f.read(4):
            # Hex representation of each byte
            hex_bytes = " ".join(f"{b:02X}" for b in chunk)

            # ASCII representation: printable characters, '.' otherwise
            ascii_chars = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

            print(f"{offset:08X}  {hex_bytes:<11}  {ascii_chars}")
            offset += 4
#
# hexdump_4byte("btree.bin")

# ----------------------------TESTING THE DATA INTERFACE------------------------------
# # Data interface tests
# tmp = DataInterface(DEFAULT_DATA_FILENAME)
# for i in range(15):
#     tmp.write_entry(i, (i+1, i*2.5, i*0.4))
# tmp.write_entry(18, (18, 10, 10))
#
# print(tmp.read_entry(1))
# print(tmp.read_entry(2))
# print(tmp.read_entry(4))
# print(tmp.read_entry(3))
# print(tmp.read_entry(12))
# print(tmp.read_entry(3))
#
# print("reads:", tmp.read_count)
# print("writes", tmp.write_count)
#
# import struct
# import os
#
# PAIR_SIZE = 20  # 4-byte int + 2 doubles
# PAGE_SIZE = 10  # number of records per page
#
def display_data_file(filename):
    if not os.path.exists(filename):
        print("File does not exist")
        return

    filesize = os.path.getsize(filename)
    total_records = filesize // PAIR_SIZE

    with open(filename, "rb") as f:
        print(f"Displaying {total_records} records from '{filename}':\n")
        for record_index in range(total_records):
            data = f.read(PAIR_SIZE)
            if not data:
                break
            key, voltage, current = struct.unpack("<i dd", data)
            if key != 0:
                print(f"Line {record_index:03d}: Key={key}, Voltage={voltage:.3f}, Current={current:.3f}")
#
# display_data_file(DEFAULT_DATA_FILENAME)
