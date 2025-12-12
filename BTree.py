from Interfaces import *
from utils import *
# from test import *
import bisect
from helper_functions import sort_parent_and_siblings

class BTree:
    def __init__(self):
        self.height = 0
        self.order = BTREE_ORDER
        self.tree_interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME, order=BTREE_ORDER)
        self.data_interface = DataInterface(filename=DEFAULT_DATA_FILENAME)

        # B-tree root node address (empty at the start)
        self.root = None
        self.last_search = NULL_ADDRESS
        self.last_search_address = NULL_ADDRESS
        self.path_buffer = []
        self.node_buffer = {}
        self.existing_nodes = []
        self.checked_siblings = None
    # record: (key, voltage, current)

    def get_access_counter(self):
        return self.tree_interface.get_access_counter()

    def get_data_access_counter(self):
        return self.data_interface.get_access_counter()

    def display(self):
        print("/////////////B-TREE DISPLAY////////////////")
        if self.root:
            self.tree_interface.display_tree(self.root, 0)
        else:
            print("NULL")
        print("///////////////////////////////////////////")

    def display_data(self, node_address=NULL_ADDRESS):
        if node_address == NULL_ADDRESS:
            node_address = self.root
            self.tree_interface.reset_read_writes()
            self.data_interface.reset_access_counter()
            print("----Display the file according to key----")
        node = self.tree_interface.read_page(node_address)
        node_m = self.get_node_m(node)
        children = self.get_all_child_pointers_from_node(node, node_m)
        keys, pointers = self.get_all_keys_and_pointers_from_node(node, node_m)
        end = 0
        for i in range(node_m):
            if children[i] != NULL_ADDRESS:
                self.display_data(node_address=children[i])
            record = self.data_interface.read_entry(pointers[i])
            print(f"key: {keys[i]}, record: {record}")
            end = i
        end += 1
        if children[end] != NULL_ADDRESS:
            self.display_data(node_address=children[end])

    def combine_node(self, node_address, child_ptrs, keys, values, parent_pointer):
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
        return page

    def write_node(self, node_address, child_ptrs, keys, values, parent_pointer):
        page = self.combine_node(node_address, child_ptrs, keys, values, parent_pointer)
        # --- Store page into disk/memory via tree interface ---
        self.node_buffer[node_address] = page
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
            # print(current)
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
                    self.last_search = search_key
                    self.last_search_address = current
                    return int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
                if search_key < key or key == 0:
                    # warunek stopu w nodzie
                    current = int.from_bytes(node[(i//2):(i//2)+POINTER_SIZE], byteorder='little')
                    break
                end = i
            if search_key > key:
                current = int.from_bytes(node[(end//2)+POINTER_SIZE:(end//2)+POINTER_SIZE*2], byteorder='little')
        self.last_search = NULL_ADDRESS
        self.last_search_address = NULL_ADDRESS
        return None

    def add_record(self, key: int, record: tuple):
        self.tree_interface.reset_read_writes()
        self.data_interface.reset_access_counter()
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
                                parent_pointer=self.get_parent_pointer_from_node(dst_node))
                return OK
            else:
                return self.handle_overflow(dst_node,dst, record, key, record_address=data_address)

    def handle_overflow(self, dst_node, dst, record, key, record_address):
        # try compensation
        idd, sibling, sibling_node, parent = None, None, None, None
        output = self.compensation_possible(node=dst_node, node_address=dst)
        if output:
            idd, sibling, sibling_node, parent = output
        if idd == 0:
            self.compensate_left(dst, dst_node, sibling, sibling_node, record, record_address, parent, key)
            return OK
        elif idd == 1:
            self.compensate_right(dst, dst_node, sibling, sibling_node, record, record_address, parent, key)
            return OK
        else:
            if self.get_parent_pointer_from_node(dst_node):
                self.split_node(dst, dst_node, key, record_address, NULL_ADDRESS)
                return OK
            else:
                self.split_root(dst, dst_node, key, record_address, NULL_ADDRESS)
                return OK

    def compensate_left(self, dst, dst_node, sibling, sibling_node, record, record_address, parent, key, dst_keys=None, dst_values=None):
        sibling_m = self.get_node_m(node=sibling_node)
        temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=sibling_node, m=sibling_m)
        dst_m = self.get_node_m(node=dst_node)
        keys, pointers = None, None
        if not dst_keys and not dst_values:
            keys, pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
        else:
            keys, pointers = dst_keys, dst_values
            dst_m -= 1 # because we just deleted one if we are here
        for x in range(len(keys)):
            i = bisect.bisect_left(temp_keys, keys[x])
            temp_keys.insert(i, keys[x])
            temp_pointers.insert(i, pointers[x])
        parent_node = self.node_buffer[parent]
        parent_m = self.get_node_m(node=parent_node)
        p_keys, p_ptrs = self.get_all_keys_and_pointers_from_node(node=parent_node, m=parent_m)
        children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
        child_index = children.index(dst)
        the_key = p_keys[child_index-1]
        the_ptr = p_ptrs[child_index-1]
        i = bisect.bisect_left(temp_keys, the_key)
        temp_keys.insert(i, the_key)
        temp_pointers.insert(i, the_ptr)
        # new key
        if key and record_address: # else it's after deletion
            i = bisect.bisect_left(temp_keys, key)
            temp_keys.insert(i, key)
            temp_pointers.insert(i, record_address)
        #
        mid_index = len(temp_keys)//2
        l_keys = temp_keys[:mid_index]
        l_ptrs = temp_pointers[:mid_index]
        parent_key = temp_keys[mid_index]
        parent_ptr = temp_pointers[mid_index]
        dst_keys = temp_keys[mid_index+1:]
        dst_ptrs = temp_pointers[mid_index+1:]
        # OF node
        self.write_node(node_address=dst,
                        child_ptrs=self.get_all_child_pointers_from_node(node=dst_node, m=dst_m), #update TODO -------------
                        keys=dst_keys,
                        values=dst_ptrs,
                        parent_pointer=parent
                        )
        # left node
        self.write_node(node_address=sibling,
                        child_ptrs=self.get_all_child_pointers_from_node(node=sibling_node, m=sibling_m), # TODO -------------
                        keys=l_keys,
                        values=l_ptrs,
                        parent_pointer=parent
                        )
        # parent
        p_keys[child_index - 1] = parent_key
        p_ptrs[child_index - 1] = parent_ptr
        self.write_node(node_address=parent,
                        child_ptrs=self.get_all_child_pointers_from_node(node=parent_node, m=parent_m),
                        keys=p_keys,
                        values=p_ptrs,
                        parent_pointer=self.get_parent_pointer_from_node(parent_node)
                        )
        # print("I can do this left!!!")

    def compensate_right(self, dst, dst_node, sibling, sibling_node, record, record_address, parent, key, dst_keys=None, dst_values=None):
        sibling_m = self.get_node_m(node=sibling_node)
        temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=sibling_node, m=sibling_m)
        dst_m = self.get_node_m(node=dst_node)
        keys, pointers = None, None
        if not dst_keys and not dst_values:
            keys, pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
        else:
            keys, pointers = dst_keys, dst_values
            dst_m -= 1  # because we just deleted one if we are here
        for x in range(len(keys)):
            i = bisect.bisect_left(temp_keys, keys[x])
            temp_keys.insert(i, keys[x])
            temp_pointers.insert(i, pointers[x])
        parent_node = self.node_buffer[parent]
        parent_m = self.get_node_m(node=parent_node)
        p_keys, p_ptrs = self.get_all_keys_and_pointers_from_node(node=parent_node, m=parent_m)
        children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
        child_index = children.index(dst)
        #######################################
        the_key = p_keys[child_index]
        the_ptr = p_ptrs[child_index]
        i = bisect.bisect_left(temp_keys, the_key)
        temp_keys.insert(i, the_key)
        temp_pointers.insert(i, the_ptr)
        # new key
        if key and record_address: # else it's after deletion
            i = bisect.bisect_left(temp_keys, key)
            temp_keys.insert(i, key)
            temp_pointers.insert(i, record_address)
        ###########################################
        mid_index = len(temp_keys) // 2
        r_keys = temp_keys[mid_index+1:]
        r_ptrs = temp_pointers[mid_index+1:]
        parent_key = temp_keys[mid_index]
        parent_ptr = temp_pointers[mid_index]
        dst_keys = temp_keys[:mid_index]
        dst_ptrs = temp_pointers[:mid_index]
        # OF node
        self.write_node(node_address=dst,
                        child_ptrs=self.get_all_child_pointers_from_node(node=dst_node, m=dst_m),
                        # update TODO -------------
                        keys=dst_keys,
                        values=dst_ptrs,
                        parent_pointer=parent
                        )
        # right node
        self.write_node(node_address=sibling,
                        child_ptrs=self.get_all_child_pointers_from_node(node=sibling_node, m=sibling_m),
                        # TODO -------------
                        keys=r_keys,
                        values=r_ptrs,
                        parent_pointer=parent
                        )
        # parent
        p_keys[child_index] = parent_key
        p_ptrs[child_index] = parent_ptr
        self.write_node(node_address=parent,
                        child_ptrs=self.get_all_child_pointers_from_node(node=parent_node, m=parent_m),
                        keys=p_keys,
                        values=p_ptrs,
                        parent_pointer=self.get_parent_pointer_from_node(parent_node)
                        )
        # print("I can do this right!!!")

    def split_node(self, dst, dst_node, key, record_address, new_child):
        dst_m = self.get_node_m(node=dst_node)
        dst_keys, dst_pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
        dst_children = self.get_all_child_pointers_from_node(node=dst_node, m=dst_m)

        i = bisect.bisect_left(dst_keys, key)
        dst_keys.insert(i, key)
        dst_pointers.insert(i, record_address)
        middle_key = len(dst_keys)//2

        # adjust new pointer
        dst_children.insert(i + 1, new_child)
        halfway = len(dst_children) // 2

        parent = self.get_parent_pointer_from_node(dst_node)
        # new node becomes right node
        new_right = self.tree_interface.get_new_node_address()
        self.write_node(node_address=new_right,
                        child_ptrs=dst_children[halfway:], ######################
                        keys=dst_keys[middle_key+1:],
                        values=dst_pointers[middle_key+1:],
                        parent_pointer=parent)
        # old node is left node
        self.write_node(node_address=dst,
                        child_ptrs=dst_children[:halfway], ######################
                        keys=dst_keys[:middle_key],
                        values=dst_pointers[:middle_key],
                        parent_pointer=parent)
        # TODO - insert that into parent
        parent_node = self.node_buffer[parent]
        parent_m = self.get_node_m(node=parent_node)
        parent_parent = self.get_parent_pointer_from_node(parent_node)
        key_to_go_up = dst_keys[middle_key]
        ptr_to_go_up = dst_pointers[middle_key]
        if not parent_parent and parent_m == 2*self.order:
            self.split_root(parent, parent_node, key_to_go_up, ptr_to_go_up, new_right)
        elif parent_m == 2*self.order:
            self.split_node(parent, parent_node, key_to_go_up, ptr_to_go_up, new_right)
            # self.handle_overflow(parent_node, parent, None, key_to_go_up, ptr_to_go_up, new_child)
        else:
            self.insert_into_parent(parent, parent_node, key_to_go_up, ptr_to_go_up, new_right)
        # print("I can split node!!!")
    def insert_into_parent(self, dst, dst_node, key, record_address, new_child):
        dst_m = self.get_node_m(node=dst_node)
        dst_keys, dst_pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
        dst_children = self.get_all_child_pointers_from_node(node=dst_node, m=dst_m)
        i = bisect.bisect_left(dst_keys, key)
        dst_keys.insert(i, key)
        dst_pointers.insert(i, record_address)
        dst_children.insert(i+1, new_child)
        parent = self.get_parent_pointer_from_node(dst_node)
        self.write_node(node_address=dst,
                        child_ptrs=dst_children,
                        keys=dst_keys,
                        values=dst_pointers,
                        parent_pointer=parent)

    def split_root(self, dst, dst_node, key, record_address, new_child):
        dst_m = self.get_node_m(node=dst_node)
        dst_keys, dst_pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)
        dst_children = self.get_all_child_pointers_from_node(node=dst_node, m=dst_m)

        i = bisect.bisect_left(dst_keys, key)
        dst_keys.insert(i, key)
        dst_pointers.insert(i, record_address)
        middle_key = len(dst_keys)//2

        # adjust new pointer
        dst_children.insert(i+1, new_child)
        halfway = len(dst_children)//2

        new_left = self.tree_interface.get_new_node_address()
        new_right = self.tree_interface.get_new_node_address()
        #root node
        root_key = [dst_keys[middle_key]]
        root_pointer = [dst_pointers[middle_key]]
        root_children = [new_left, new_right]
        root_address = self.root
        root_parent = NULL_ADDRESS
        self.write_node(node_address=root_address,
                        child_ptrs=root_children,
                        keys=root_key,
                        values=root_pointer,
                        parent_pointer=root_parent)
        #left node
        left_keys = dst_keys[:middle_key]
        left_pointers = dst_pointers[:middle_key]
        left_children = dst_children[:halfway] #????
        left_address = new_left
        left_parent = root_address
        self.write_node(node_address=left_address,
                        child_ptrs=left_children,
                        keys=left_keys,
                        values=left_pointers,
                        parent_pointer=left_parent)
        #right node
        right_keys = dst_keys[middle_key+1:]
        right_pointers = dst_pointers[middle_key+1:]
        right_children = dst_children[halfway:] #?????
        right_address = new_right
        right_parent = root_address
        self.write_node(node_address=right_address,
                        child_ptrs=right_children,
                        keys=right_keys,
                        values=right_pointers,
                        parent_pointer=right_parent)
        # update parent for all children of new left and right nodes
        p_ptr_offset = self.tree_interface.parent_pointer_offset
        for child in right_children:
            if child != NULL_ADDRESS:
                node = self.tree_interface.read_page(child)
                node[p_ptr_offset:p_ptr_offset + POINTER_SIZE] = right_address.to_bytes(POINTER_SIZE, byteorder='little')
                self.tree_interface.write_page(index=child, node=node)
        for child in left_children:
            if child != NULL_ADDRESS:
                node = self.tree_interface.read_page(child)
                node[p_ptr_offset:p_ptr_offset + POINTER_SIZE] = left_address.to_bytes(POINTER_SIZE, byteorder='little')
                self.tree_interface.write_page(index=child, node=node)
        # print("I can split root!!!")

    def compensation_possible(self, node, node_address, compensation_type="add"):
        self.checked_siblings = [None, None]
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
                self.checked_siblings[0] = left_node
                if compensation_type == "add":
                    if self.get_node_m(node=left_node) < 2*self.order:
                        return (0,left_sibling,left_node, parent_pointer)
                else: # type == "delete"
                    if self.get_node_m(node=left_node) > self.order:
                        return (0,left_sibling,left_node, parent_pointer)
            if right_sibling:
                right_node = self.tree_interface.read_page(index=right_sibling)
                self.checked_siblings[1] = right_node
                if compensation_type == "add":
                    if self.get_node_m(node=right_node) < 2*self.order:
                        return (1, right_sibling, right_node, parent_pointer)
                else: # type == "delete"
                    if self.get_node_m(node=right_node) > self.order:
                        return (1, right_sibling, right_node, parent_pointer)
            return None

    def read_record(self, key):
        self.tree_interface.reset_read_writes()
        self.data_interface.reset_access_counter()
        if not self.root:
            return None
        result = self.search(key)
        if result or result == 0: # addressing in data from 0
            return self.data_interface.read_entry(index=result)
        else:
            return None

    def delete_record(self, key):
        self.tree_interface.reset_read_writes()
        self.data_interface.reset_access_counter()
        if not self.root:
            return DOES_NOT_EXIST
        else:
            if not self.search(search_key=key):
                return DOES_NOT_EXIST
            else:
                current = self.path_buffer[-1]
                current_node = self.node_buffer[current]
                current_m = self.get_node_m(node=current_node)
                current_children = self.get_all_child_pointers_from_node(node=current_node, m=current_m)
                current_keys, current_pointers = self.get_all_keys_and_pointers_from_node(node=current_node, m=current_m)
                current_parent = self.get_parent_pointer_from_node(current_node)
                if not current_children[0]: # take first child to see if it is NULL -> leaf
                    self.leaf_pop(current, current_node, current_m, key)
                else: # subtree
                    # replace with smallest key from child on the right
                    i = current_keys.index(key)
                    # delete corresponding data
                    data_to_delete = current_pointers[i]
                    self.data_interface.write_entry(index=data_to_delete, record=DELETE_RECORD)
                    # get child for replacement
                    child = current_children[i+1]
                    self.path_buffer.append(child)
                    child_node = self.tree_interface.read_page(index=child)
                    self.node_buffer[child] = child_node
                    child_m = self.get_node_m(node=child_node)
                    # get child smallest key and write it to node and recursively delete this key
                    ch_keys, ch_pointers = self.get_all_keys_and_pointers_from_node(node=child_node, m=child_m)
                    new_key = ch_keys[0]
                    current_keys[i] = new_key
                    current_pointers[i] = ch_pointers[0]
                    self.write_node(node_address=current,
                                    child_ptrs=current_children,
                                    keys=current_keys,
                                    values=current_pointers,
                                    parent_pointer=current_parent)
                    if not self.get_all_child_pointers_from_node(child_node, child_m)[0]: # if leaf
                        self.leaf_pop(child, child_node, child_m, new_key, from_parent=True)
                    else:
                        # call recursively subtree_pop
                        self.subtree_pop(child, child_node, child_m, new_key, from_parent=True)
                        pass
                return OK

    def subtree_pop(self, dst, dst_node, dst_m, key, from_parent=False):
        dst_keys, dst_pointers = self.get_all_keys_and_pointers_from_node(dst_node, dst_m)
        dst_children = self.get_all_child_pointers_from_node(dst_node, dst_m)
        dst_parent = self.get_parent_pointer_from_node(dst_node)

        # replace with smallest key from child on the right
        i = dst_keys.index(key)
        # delete corresponding data
        data_to_delete = dst_pointers[i]
        if not from_parent:
            self.data_interface.write_entry(index=data_to_delete, record=DELETE_RECORD)
        # get child for replacement
        child = dst_children[i + 1]
        self.path_buffer.append(child)
        child_node = self.tree_interface.read_page(index=child)
        self.node_buffer[child] = child_node
        child_m = self.get_node_m(node=child_node)
        # get child smallest key and write it to node and recursively delete this key
        ch_keys, ch_pointers = self.get_all_keys_and_pointers_from_node(node=child_node, m=child_m)
        new_key = ch_keys[0]
        dst_keys[i] = new_key
        dst_pointers[i] = ch_pointers[0]
        self.write_node(node_address=dst,
                        child_ptrs=dst_children,
                        keys=dst_keys,
                        values=dst_pointers,
                        parent_pointer=dst_parent)
        if not self.get_all_child_pointers_from_node(child_node, child_m)[0]:  # if leaf
            self.leaf_pop(child, child_node, child_m, new_key, from_parent=True)
        else:
            # call recursively subtree_pop
            self.subtree_pop(child, child_node, child_m, new_key, from_parent=True)
            pass

    def leaf_pop(self, dst, dst_node, dst_m, key, from_parent=False):
        dst_keys, dst_pointers = self.get_all_keys_and_pointers_from_node(dst_node, dst_m)
        dst_children = self.get_all_child_pointers_from_node(dst_node, dst_m)
        dst_parent = self.get_parent_pointer_from_node(dst_node)
        i = dst_keys.index(key)
        dst_children.pop(i)
        dst_keys.pop(i)
        data_to_delete = dst_pointers.pop(i)
        if not from_parent:
            self.data_interface.write_entry(index=data_to_delete, record=DELETE_RECORD)
        dst_m -= 1
        if dst_m < self.order:
            # handle underflow
            self.handle_underflow(dst=dst, dst_node=dst_node, dst_keys=dst_keys, dst_values=dst_pointers)
        else:
            self.write_node(node_address=dst,
                            child_ptrs=dst_children,
                            keys=dst_keys,
                            values=dst_pointers,
                            parent_pointer=dst_parent)

    def handle_underflow(self, dst, dst_node, dst_keys, dst_values):
        if dst == self.root:
            if len(dst_keys) >= 1: # min 1 key for root
                return # ale to walnie
            else:
                pass
                # collect all keys on level 1 to root
                # take pointers from children
                # deallocate right and left children of root
                # refresh parent for all nodes below now
        # try compensation
        idd, sibling, sibling_node, parent = None, None, None, None
        output = self.compensation_possible(node=dst_node, node_address=dst, compensation_type="delete")
        if output:
            idd, sibling, sibling_node, parent = output
        if idd == 0:
            self.compensate_left(dst, dst_node, sibling, sibling_node, record=None, record_address=None, parent=parent, key=None,
                                 dst_keys=dst_keys, dst_values=dst_values)
        elif idd == 1:
            self.compensate_right(dst, dst_node, sibling, sibling_node, record=None, record_address=None, parent=parent, key=None,
                                  dst_keys=dst_keys, dst_values=dst_values)
        else:
            self.merge(dst, dst_node, dst_keys, dst_values)

    def merge(self, dst, dst_node, dst_keys, dst_values):
        # merge (with left first)
        parent_ptr_offset = self.tree_interface.parent_pointer_offset
        parent = int.from_bytes(dst_node[parent_ptr_offset:parent_ptr_offset + POINTER_SIZE],
                                        byteorder='little')
        if not parent:
            print("WHOOOOOOOOPS") #TODO #########################################
            raise Exception("WHOOOOOOOOOPS")
        else:
            parent_keys, parent_pointers = None, None
            parent_node = self.node_buffer[parent]
            parent_m = self.get_node_m(node=parent_node)
            children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
            i = children.index(dst)
            left_sibling = None
            right_sibling = None
            if i - 1 >= 0:
                left_sibling = children[i - 1]
            if i + 1 < parent_m + 1:
                right_sibling = children[i + 1]
            if left_sibling:
                left_node = self.checked_siblings[LEFT]
                left_m = self.get_node_m(node=left_node)
                left_keys, left_pointers = self.get_all_keys_and_pointers_from_node(left_node, left_m)
                parent_keys, parent_pointers = self.get_all_keys_and_pointers_from_node(parent_node, parent_m)
                parent_key = parent_keys.pop(i-1)
                parent_pointer = parent_pointers.pop(i-1)
                all_keys, all_pointers = sort_parent_and_siblings(dst_keys, left_keys, parent_key, dst_values, left_pointers, parent_pointer)
                # delete pointer i and write to left sibling
                self.tree_interface.free_node_address(children[i])
                children.pop(i)
                self.write_node(node_address=left_sibling,
                                child_ptrs=[NULL_ADDRESS], #TODO ##############################
                                keys=all_keys,
                                values=all_pointers,
                                parent_pointer=parent)
            elif right_sibling:
                right_node = self.checked_siblings[RIGHT]
                right_m = self.get_node_m(node=right_node)
                right_keys, right_pointers = self.get_all_keys_and_pointers_from_node(right_node, right_m)
                parent_keys, parent_pointers = self.get_all_keys_and_pointers_from_node(parent_node, parent_m)
                parent_key = parent_keys.pop(i)
                parent_pointer = parent_pointers.pop(i)
                all_keys, all_pointers = sort_parent_and_siblings(dst_keys, right_keys, parent_key, dst_values,
                                                                  right_pointers, parent_pointer)
                # delete pointer i+1 and write to dst
                self.tree_interface.free_node_address(children[i+1])
                children.pop(i+1)
                self.write_node(node_address=dst,
                                child_ptrs=[NULL_ADDRESS],  # TODO ##############################
                                keys=all_keys,
                                values=all_pointers,
                                parent_pointer=parent)
            # check if parent requires merge
            if len(parent_keys) < self.order:
            # if so call handle underflow on parent
                self.handle_underflow(parent, parent_node, parent_keys, parent_pointers) #TODO ########################
            else:
                self.write_node(node_address=parent,
                                child_ptrs=children,
                                keys=parent_keys,
                                values=parent_pointers,
                                parent_pointer=self.get_parent_pointer_from_node(parent_node))
