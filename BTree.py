from Interfaces import *
from utils import *
from test import *

class BTree:
    def __init__(self):
        self.height = 0
        self.order = BTREE_ORDER
        self.tree_interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME, order=BTREE_ORDER)
        self.data_interface = DataInterface(filename=DEFAULT_DATA_FILENAME)

        # B-tree root node address (empty at the start)
        self.root = None
        self.path_buffer = []

    # record: (key, voltage, current)

    def search(self, search_key):
        current = self.root
        self.path_buffer = []
        first = True
        while current or first:
            first = False
            print(current)
            self.path_buffer.append(current)
            node = self.tree_interface.read_page(index=current)
            for i in range(0,2*self.order*(KEY_SIZE+POINTER_SIZE),(KEY_SIZE+POINTER_SIZE)):
                offset = self.tree_interface.keys_offset
                key = int.from_bytes(node[offset+i:offset+i+KEY_SIZE], byteorder='little')
                if search_key == key:
                    return int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
                if search_key < key or key == 0:
                    current = int.from_bytes(node[(i//2):(i//2)+POINTER_SIZE], byteorder='little')
                    break
        return None

    def add_record(self, key, record):
        if self.root != 0:
            self.root = self.tree_interface.get_new_node_address() # address in the interface
            # first 2 pointers are NONE
            # self.tree_interface.write(index=self.root, value=self.tree_interface.get_new_node_address())
            # self.tree_interface.write(index=self.root+POINTER_SIZE, value=self.tree_interface.get_new_node_address())

            # key value in the node
            self.tree_interface.write(index=self.tree_interface.keys_offset, value=key)
            # data file which returns address written in it
            data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
            # writing pointer to data file next to the key in the node
            self.tree_interface.write(index=self.tree_interface.keys_offset+KEY_SIZE, value=data_address)
            self.tree_interface.write(index=self.tree_interface.record_count_offset, value=1)
            # debug
            self.tree_interface.read_page(index=self.root)
            hexdump_4byte(DEFAULT_BTREE_FILENAME)
            return OK
        if self.search(search_key=key) == ALREADY_EXISTS:
            return ALREADY_EXISTS
        data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
        # adding logic
        # search gives last node self.path_buffer[-1]
        # add the record here
        current = self.path_buffer[-1]
        node = self.tree_interface.read_page(index=current)
        # check if record count is appropriate
        m_offset = self.tree_interface.record_count_offset
        m = int.from_bytes(node[m_offset:m_offset+RECORD_COUNT_SIZE], byteorder='little')
        if m < 2*self.order:
            offset = self.tree_interface.keys_offset
            end = 0
            for i in range(0, m * (KEY_SIZE + POINTER_SIZE), (KEY_SIZE + POINTER_SIZE)):
                read_key = int.from_bytes(node[offset + i:offset + i + KEY_SIZE], byteorder='little')
                read_address = int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
                if read_key > key:
                    # write key to where read_key is while storing read_key in key
                    node[offset + i:offset + i + KEY_SIZE] = bytearray(key.to_bytes(KEY_SIZE, byteorder='little'))
                    key = read_key
                    # do the same with pointers to data
                    node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE] = bytearray(data_address.to_bytes(POINTER_SIZE, byteorder='little'))
                    data_address = read_address
                end = i + KEY_SIZE + POINTER_SIZE # save last i value
            node[offset + end:offset + end + KEY_SIZE] = bytearray(key.to_bytes(KEY_SIZE, byteorder='little'))
            node[offset+end+KEY_SIZE:offset+end+KEY_SIZE+POINTER_SIZE] = bytearray(data_address.to_bytes(POINTER_SIZE, byteorder='little'))
            # new m value
            m += 1
            node[m_offset:m_offset + RECORD_COUNT_SIZE] = m.to_bytes(RECORD_COUNT_SIZE, byteorder='little')
            # add the whole node here
            print(node)
            self.tree_interface.write_page(index=current, node=node)
        else:
            print("No compensation yet!")
            # compensation

        #debug
        self.tree_interface.read_page(index=self.root)
        hexdump_4byte(DEFAULT_BTREE_FILENAME)
        return OK

    def read_record(self, key):
        if not self.root == 0:
            return None
        result = self.search(key)
        if result or result == 0:
            return self.data_interface.read_entry(index=result)
        else:
            return None

    def write_record(self):
        pass