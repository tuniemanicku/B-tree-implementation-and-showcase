from Interfaces import *
from utils import *
from test import *
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
        self.tree_interface.display_tree(self.root, 0)
        print("///////////////////////////////////////////")

    def write_node(self, node_address, child_ptrs, keys, values, parent_pointer):
        """
        Writes a B-tree node into its page buffer.
        Node layout (all 4-byte ints):
            [child_ptr0 ... child_ptr2d]      -> (2d+1) entries
            [key0 value0 key1 value1 ... key(2d-1) value(2d-1)]
            [number_of_pairs]
            [parent_pointer]
        """

        page_size = self.tree_interface.page_size
        d = self.order
        max_keys = 2 * d
        max_child_ptrs = 2 * d + 1

        # # --- Sanity checks ---
        # assert len(child_ptrs) == max_child_ptrs, \
        #     f"child_ptrs must have length {max_child_ptrs}"
        # assert len(keys) == len(values), "keys and values must have equal length"
        # assert len(keys) <= max_keys, f"Too many keys ({len(keys)} > {max_keys})"

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

    def compensate(self):
        pass

    def add_record(self, key, record, data_address=None):
        if not self.root:
            self.root = self.tree_interface.get_new_node_address() # address in the interface
            # first 2 pointers are NONE
            # self.tree_interface.write(index=self.root, value=self.tree_interface.get_new_node_address())
            # self.tree_interface.write(index=self.root+POINTER_SIZE, value=self.tree_interface.get_new_node_address())
            # key value in the node
            self.tree_interface.write(index=self.root+self.tree_interface.keys_offset, value=key)
            # data file which returns address written in it
            data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
            # writing pointer to data file next to the key in the node
            self.tree_interface.write(index=self.root+self.tree_interface.keys_offset+KEY_SIZE, value=data_address)
            self.tree_interface.write(index=self.root+self.tree_interface.record_count_offset, value=1)
            # debug
            self.tree_interface.read_page(index=self.root)
            hexdump_4byte(DEFAULT_BTREE_FILENAME)
            return OK
        if self.search(search_key=key) == ALREADY_EXISTS:
            return ALREADY_EXISTS
        if not data_address and data_address != 0:
            data_address = self.data_interface.write_entry(index=None, record=(key, record[0], record[1]))
        # adding logic
        # search gives last node self.path_buffer[-1]
        # add the record here
        current = self.path_buffer[-1]
        node = self.tree_interface.read_page(index=current)
        # check if record count is appropriate
        m_offset = self.tree_interface.record_count_offset
        m = int.from_bytes(node[m_offset:m_offset+RECORD_COUNT_SIZE], byteorder='little')
        offset = self.tree_interface.keys_offset
        if m < 2*self.order:
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
            # try compensation (check for number of keys in neighbours m_neighbour < 2d)
            parent_offset = self.tree_interface.parent_pointer_offset
            parent_address = int.from_bytes(node[parent_offset:parent_offset+POINTER_SIZE], byteorder='little')
            if not parent_address == NULL_ADDRESS:
                # parent_node = self.node_buffer[parent_address]
                # parent_m = int.from_bytes(parent_node[m_offset:m_offset + RECORD_COUNT_SIZE], byteorder="little")
                keys, data_p = self.get_all_keys_and_pointers_from_node(node, m)
                # for i in range(0, parent_m * (KEY_SIZE + POINTER_SIZE), (KEY_SIZE + POINTER_SIZE)):
                #     read_parent_key = int.from_bytes(parent_node[offset + i:offset + i + KEY_SIZE], byteorder='little')
                #     l_child = int.from_bytes(parent_node[(i // 2) - POINTER_SIZE:(i // 2)], byteorder="little")
                #     r_child = int.from_bytes(parent_node[(i // 2) + POINTER_SIZE:(i // 2) + POINTER_SIZE * 2], byteorder="little")  # right child address
                # print("No compensation yet!")
                parent_node = self.node_buffer[parent_address]
                parent_m = int.from_bytes(parent_node[m_offset:m_offset + RECORD_COUNT_SIZE], byteorder="little")
                read_parent_key = None
                end = 0
                for i in range(0, parent_m * (KEY_SIZE + POINTER_SIZE), (KEY_SIZE + POINTER_SIZE)):
                    read_parent_key = int.from_bytes(parent_node[offset + i:offset + i + KEY_SIZE], byteorder='little')
                    read_parent_data = int.from_bytes(parent_node[offset + i + KEY_SIZE:offset + i + KEY_SIZE+POINTER_SIZE], byteorder='little')
                    if key < read_parent_key:
                        # take pointer and read amount of children
                        # try left neighbour
                        l_child = int.from_bytes(parent_node[(i//2)-POINTER_SIZE:(i//2)], byteorder="little") # left child address
                        if l_child >= parent_address:
                            l_node = self.tree_interface.read_page(index=l_child)
                            if self.get_node_m(l_node) < 2*self.order:
                                #switch keys with left child and parent
                                #keys[0] -> read_parent_key
                                parent_node[offset + i:offset + i + KEY_SIZE] = keys[0].to_bytes(KEY_SIZE, byteorder='little')
                                parent_node[offset + i + KEY_SIZE:offset + i + KEY_SIZE + POINTER_SIZE] = data_address.to_bytes(POINTER_SIZE, byteorder='little')
                                self.tree_interface.write_page(index=parent_address, node=parent_node)
                                #read_parent_key -> l_child[-1]
                                l_keys, l_data = self.get_all_keys_and_pointers_from_node(l_node, self.get_node_m(l_node))
                                l_children = self.get_all_child_pointers_from_node(l_node, self.get_node_m(l_node))
                                l_keys.append(read_parent_key)
                                l_data.append(read_parent_data)
                                l_children.append(NULL_ADDRESS)
                                self.write_node(
                                    node_address=l_child,
                                    child_ptrs=l_children,
                                    keys=l_keys,
                                    values=l_data,
                                    parent_pointer=parent_address
                                )
                                #key -> keys
                                child_pointers = self.get_all_child_pointers_from_node(node=node, m=m)
                                i = bisect.bisect_left(keys, key)
                                keys.insert(i, key)
                                data_p.insert(i, data_address)
                                child_pointers.insert(i + 1, NULL_ADDRESS)  # new null child
                                self.write_node(
                                    node_address=current,
                                    child_ptrs=child_pointers,
                                    keys=keys,
                                    values=data_p,
                                    parent_pointer=parent_address
                                )
                                return OK
                        # try right neighbour
                        r_child = int.from_bytes(parent_node[(i // 2) + POINTER_SIZE:(i // 2)+ POINTER_SIZE*2], byteorder="little") # right child address
                        if r_child <= parent_address + offset - POINTER_SIZE:
                            r_node = self.tree_interface.read_page(index=r_child)
                            if self.get_node_m(r_node) < 2*self.order:
                                pass
                                return OK
                    end = i
                end += POINTER_SIZE+KEY_SIZE
                if key > read_parent_key:
                    l_child = int.from_bytes(parent_node[(end // 2) - POINTER_SIZE:(end // 2)],
                                             byteorder="little")  # left child address
                    if True:
                        l_node = self.tree_interface.read_page(index=l_child)
                        if self.get_node_m(l_node) < 2 * self.order:
                            # switch keys with left child and parent
                            # keys[0] -> read_parent_key
                            parent_node[offset + i:offset + i + KEY_SIZE] = keys[0].to_bytes(KEY_SIZE,
                                                                                             byteorder='little')
                            parent_node[
                                offset + i + KEY_SIZE:offset + i + KEY_SIZE + POINTER_SIZE] = data_address.to_bytes(
                                POINTER_SIZE, byteorder='little')
                            self.tree_interface.write_page(index=parent_address, node=parent_node)
                            # read_parent_key -> l_child[-1]
                            l_keys, l_data = self.get_all_keys_and_pointers_from_node(l_node, self.get_node_m(l_node))
                            l_children = self.get_all_child_pointers_from_node(l_node, self.get_node_m(l_node))
                            l_keys.append(read_parent_key)
                            l_data.append(read_parent_data)
                            l_children.append(NULL_ADDRESS)
                            self.write_node(
                                node_address=l_child,
                                child_ptrs=l_children,
                                keys=l_keys,
                                values=l_data,
                                parent_pointer=parent_address
                            )
                            # key -> keys
                            child_pointers = self.get_all_child_pointers_from_node(node=node, m=m)
                            i = bisect.bisect_left(keys, key)
                            keys.insert(i, key)
                            data_p.insert(i, data_address)
                            child_pointers.insert(i + 1, NULL_ADDRESS)  # new null child
                            self.write_node(
                                node_address=current,
                                child_ptrs=child_pointers,
                                keys=keys,
                                values=data_p,
                                parent_pointer=parent_address
                            )
                            return OK
            # if it fails: split
            print("Split not implemented yet!")
            # get new page (new right node)
            new_page_address = self.tree_interface.get_new_node_address() # this also becomes the new child pointer
            new_node = bytearray(self.tree_interface.page_size)             # in the parent
            # distribute all the keys except the middle one
            all_keys, all_pointers = self.get_all_keys_and_pointers_from_node(node=node,m=m)
            all_child_pointers = self.get_all_child_pointers_from_node(node=node,m=m)
            i = bisect.bisect_left(all_keys, key)
            all_keys.insert(i, key)
            all_pointers.insert(i, data_address)
            all_child_pointers.insert(i + 1, NULL_ADDRESS) # new null child

            # middle key is always at index "d"
            middle_key = all_keys[self.order]
            middle_pointer = all_pointers[self.order]
            left_keys = all_keys[:self.order]
            left_pointers = all_pointers[:self.order]
            right_keys = all_keys[self.order+1:]
            right_pointers = all_pointers[self.order+1:]
            left_child_ptrs = all_child_pointers[:self.order + 1]
            right_child_ptrs = all_child_pointers[self.order + 1:]

            # # === 5. Write left node back (overwrite original) ===
            #
            self.write_node(
                node_address=current,
                child_ptrs=left_child_ptrs,
                keys=left_keys,
                values=left_pointers,
                parent_pointer=parent_address
            )
            #
            # # === 6. Write right node ===
            #
            self.write_node(
                node_address=new_page_address,
                child_ptrs=right_child_ptrs,
                keys=right_keys,
                values=right_pointers,
                parent_pointer=parent_address
            )
            # # === 7. Update children's parent pointer for children moved to RIGHT ===
            #
            # for ptr in right_child_ptrs:
            #     if ptr != NULL_ADDRESS:
            #         self.update_parent_pointer(ptr, right_node_addr)
            #
            # # === 8. Promote middle key to parent ===
            #
            if parent_address == NULL_ADDRESS:
                # Create new root
                new_root = self.tree_interface.get_new_node_address()

                root_child_ptrs = [current, new_page_address]
                root_keys = [middle_key]

                self.write_node(
                    node_address=new_root,
                    child_ptrs=root_child_ptrs,
                    keys=root_keys,
                    values=[middle_pointer],
                    parent_pointer=NULL_ADDRESS
                )

                self.root = new_root
                # update parent pointer for children
                self.write_node(
                    node_address=current,
                    child_ptrs=left_child_ptrs,
                    keys=left_keys,
                    values=left_pointers,
                    parent_pointer=new_root
                )
                self.write_node(
                    node_address=new_page_address,
                    child_ptrs=right_child_ptrs,
                    keys=right_keys,
                    values=right_pointers,
                    parent_pointer=new_root
                )
            else:
                # Normal parent insertion
                self.add_record(middle_key, (-1,-1), middle_pointer)

        #debug
        # self.tree_interface.read_page(index=self.root)
        # hexdump_4byte(DEFAULT_BTREE_FILENAME)
        return OK

    def read_record(self, key):
        if not self.root:
            return None
        result = self.search(key)
        if result or result == 0: # adresujemy w pliku z danymi od 0
            return self.data_interface.read_entry(index=result)
        else:
            return None

    def write_record(self):
        pass