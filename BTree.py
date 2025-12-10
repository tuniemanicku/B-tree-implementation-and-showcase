from Interfaces import *
from utils import *
# from test import *
import bisect

class BTree:
    def __init__(self):
        self.height = 0
        self.order = BTREE_ORDER
        self.tree_interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME, order=BTREE_ORDER)
        self.data_interface = DataInterface(filename=DEFAULT_DATA_FILENAME)

        # B-tree root node address (empty at the start)
        self.root = None
        self.path_buffer = []
        self.node_buffer = {}
        self.existing_nodes = []
    # record: (key, voltage, current)

    def display(self):
        print("/////////////B-TREE DISPLAY////////////////")
        if self.root:
            self.tree_interface.display_tree(self.root, 0)
        else:
            print("NULL")
        print("///////////////////////////////////////////")

    def write_node(self, node_address, child_ptrs, keys, values, parent_pointer):
        page_size = self.tree_interface.page_size
        d = self.order
        max_keys = 2 * d
        max_child_ptrs = 2 * d + 1

        # --- Create page buffer ---
        page = bytearray(page_size)

        # === 1. Write child pointers ===
        offset = 0
        for ptr in child_ptrs:
            page[offset:offset + 4] = ptr.to_bytes(4, "little", signed=True)
            offset += 4
        offset = self.tree_interface.keys_offset
        # === 2. Write key/value pairs ===
        # Only write the real pairs, zero-fill the rest.
        n = len(keys)
        for i in range(max_keys):
            if i < n:
                # write key
                page[offset:offset + 4] = keys[i].to_bytes(4, "little", signed=True)
                offset += 4
                # write value
                page[offset:offset + 4] = values[i].to_bytes(4, "little", signed=True)
                offset += 4
            else:
                # zero-fill unused key/value slots
                page[offset:offset + 8] = b"\x00" * 8
                offset += 8

        # === 3. Write number_of_pairs ===
        page[offset:offset + 4] = n.to_bytes(4, "little", signed=True)
        offset += 4

        # === 4. Write parent pointer ===
        page[offset:offset + 4] = parent_pointer.to_bytes(4, "little", signed=True)
        offset += 4

        # --- Store page into disk/memory via tree interface ---
        self.tree_interface.write_page(node_address, page)

    def get_node_m(self, node):
        m_offset = self.tree_interface.record_count_offset
        return int.from_bytes(node[m_offset:m_offset + RECORD_COUNT_SIZE], byteorder='little')

    def get_all_keys_and_pointers_from_node(self, node, m):
        keys = []
        pointers = []
        offset = self.tree_interface.keys_offset
        for i in range(0, m * (KEY_SIZE + POINTER_SIZE), (KEY_SIZE + POINTER_SIZE)):
            read_key = int.from_bytes(node[offset + i:offset + i + KEY_SIZE], byteorder='little')
            read_address = int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
            keys.append(read_key)
            pointers.append(read_address)
        return keys, pointers

    def get_all_child_pointers_from_node(self, node, m):
        pointers = []
        for i in range(0, (m+1) * POINTER_SIZE, POINTER_SIZE):
            read_pointer = int.from_bytes(node[i:i + POINTER_SIZE], byteorder='little')
            pointers.append(read_pointer)
        return pointers

    def get_parent_pointer_from_node(self, node):
        offset = self.tree_interface.parent_pointer_offset
        return int.from_bytes(node[offset:offset + POINTER_SIZE], byteorder='little')

    def search(self, search_key):
        current = self.root
        self.path_buffer = []
        self.node_buffer = {}
        first = True
        while current or first:
            first = False
            print(current)
            self.path_buffer.append(current)
            node = self.tree_interface.read_page(index=current)
            self.node_buffer[current] = node
            end = 0
            key = -1
            for i in range(0,2*self.order*(KEY_SIZE+POINTER_SIZE),(KEY_SIZE+POINTER_SIZE)):
                offset = self.tree_interface.keys_offset
                key = int.from_bytes(node[offset+i:offset+i+KEY_SIZE], byteorder='little')
                if search_key == key:
                    # pointer do danych
                    return int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
                if search_key < key or key == 0:
                    # warunek stopu w nodzie
                    current = int.from_bytes(node[(i//2):(i//2)+POINTER_SIZE], byteorder='little')
                    break
                end = i
            if search_key > key:
                current = int.from_bytes(node[(end//2)+POINTER_SIZE:(end//2)+POINTER_SIZE*2], byteorder='little')
        return None

    def add_record(self, key: int, record: tuple):
        if not self.root:
            data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
            self.root = self.tree_interface.get_new_node_address()
            node = bytearray(self.tree_interface.page_size)
            offset = self.tree_interface.keys_offset
            node[offset:offset + KEY_SIZE] = key.to_bytes(KEY_SIZE, "little")
            node[offset+KEY_SIZE:offset + KEY_SIZE + POINTER_SIZE] = data_address.to_bytes(POINTER_SIZE, "little")
            rcoffset = self.tree_interface.record_count_offset
            m = 1
            node[rcoffset:rcoffset + RECORD_COUNT_SIZE] = m.to_bytes(RECORD_COUNT_SIZE, "little")
            self.tree_interface.write(index=self.root+self.tree_interface.page_size-POINTER_SIZE, value=0)
            self.tree_interface.write_page(index=self.root, node=node)
            # hexdump_4byte(DEFAULT_BTREE_FILENAME)
            return OK
        if self.search(search_key=key):
            return ALREADY_EXISTS
        else:
            data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
            dst = self.path_buffer[-1] # last node from search
            dst_node = self.node_buffer[dst]
            dst_m = self.get_node_m(node=dst_node)
            if dst_m < 2*self.order:
                dst_keys, dst_data = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
                i = bisect.bisect_left(dst_keys, key)
                dst_keys.insert(i, key)
                dst_data.insert(i, data_address)
                self.write_node(node_address=dst,
                                child_ptrs=self.get_all_child_pointers_from_node(node=dst_node, m=dst_m),
                                keys=dst_keys,
                                values=dst_data,
                                parent_pointer=0)
                return OK
            else:
                # try compensation
                sibling = self.compensation_possible(node=dst_node, node_address=dst)
                if sibling:
                    print("Compensation not implemented yet")
                else:
                    print("Split not implemented yet")
                return ALREADY_EXISTS

    def compensate(self):
        print("I can do this!!!")

    def split(self):
        print("I can do this too!!!")

    def compensation_possible(self, node, node_address):
        parent_ptr_offset = self.tree_interface.parent_pointer_offset
        parent_pointer = int.from_bytes(node[parent_ptr_offset:parent_ptr_offset + POINTER_SIZE],byteorder='little')
        if not parent_pointer:
            return None
        else:
            parent_node = self.node_buffer[parent_pointer]
            parent_m = self.get_node_m(node=parent_node)
            children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
            i = children.index(node_address)
            # check for siblings with less than 2d keys
            left_sibling = None
            right_sibling = None
            if i-1 >= 0:
                left_sibling = children[i-1]
            if i+1 < parent_m + 1:
                right_sibling = children[i+1]
            if left_sibling:
                left_node = self.tree_interface.read_page(index=left_sibling)
                if self.get_node_m(node=left_node) < 2*self.order:
                    return left_sibling
            if right_sibling:
                right_node = self.tree_interface.read_page(index=right_sibling)
                if self.get_node_m(node=right_node) < 2*self.order:
                    return right_sibling
            # return the sibling to compensate (address, whatever needed...)
            return None

    def read_record(self, key):
        if not self.root:
            return None
        result = self.search(key)
        if result or result == 0: # adresujemy w pliku z danymi od 0
            return self.data_interface.read_entry(index=result)
        else:
            return None
