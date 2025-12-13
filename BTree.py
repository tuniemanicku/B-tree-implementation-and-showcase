from Interfaces import *
from test import display_data_file
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
        parent = self.get_parent_pointer_from_node(node)
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
                    address = int.from_bytes(node[offset+i+KEY_SIZE:offset+i+KEY_SIZE+POINTER_SIZE], byteorder='little')
                    return address
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
                result = self.handle_overflow(dst_node,dst, record, key, record_address=data_address)
                self.update_parent_pointers()
                return result

    def handle_overflow(self, dst_node, dst, record, key, record_address, new_child=NULL_ADDRESS):
        # try compensation
        idd, sibling, sibling_node, parent = None, None, None, None
        output = self.compensation_possible(node=dst_node, node_address=dst)
        if output:
            idd, sibling, sibling_node, parent = output
        if idd == 0:
            self.compensate_left(dst, dst_node, sibling, sibling_node, record, record_address, parent, key, new_child=new_child)
            return OK
        elif idd == 1:
            self.compensate_right(dst, dst_node, sibling, sibling_node, record, record_address, parent, key, new_child=new_child)
            return OK
        else:
            if self.get_parent_pointer_from_node(dst_node):
                self.split_node(dst, dst_node, key, record_address, new_child)
                return OK
            else:
                self.split_root(dst, dst_node, key, record_address, new_child)
                return OK

    def compensate_left(self, dst, dst_node, sibling, sibling_node, record, record_address, parent, key,
                        dst_keys=None, dst_values=None, new_child=None):
        sibling_m = self.get_node_m(node=sibling_node)
        temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=sibling_node, m=sibling_m)
        dst_m = self.get_node_m(node=dst_node)
        keys, pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)

        #get the children
        dst_children = self.get_all_child_pointers_from_node(node=dst_node, m=dst_m)
        sibling_children = self.get_all_child_pointers_from_node(node=sibling_node, m=sibling_m)
        temp_children = sibling_children
        temp_children += dst_children
        # print(temp_children)
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
        i = bisect.bisect_left(temp_keys, key)
        temp_keys.insert(i, key)
        temp_pointers.insert(i, record_address)
        #new children
        if new_child:
            temp_children.insert(i+1, new_child)
        # print(temp_children)
        mid_index = len(temp_keys)//2
        l_keys = temp_keys[:mid_index]
        l_children = temp_children[:mid_index+1]
        l_ptrs = temp_pointers[:mid_index]
        parent_key = temp_keys[mid_index]
        parent_ptr = temp_pointers[mid_index]
        dst_keys = temp_keys[mid_index+1:]
        d_children = temp_children[mid_index+1:]
        dst_ptrs = temp_pointers[mid_index+1:]

        # OF node
        self.write_node(node_address=dst,
                        child_ptrs=d_children,
                        keys=dst_keys,
                        values=dst_ptrs,
                        parent_pointer=parent
                        )
        # left node
        self.write_node(node_address=sibling,
                        child_ptrs=l_children,
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

    def compensate_right(self, dst, dst_node, sibling, sibling_node, record, record_address, parent, key,
                         dst_keys=None, dst_values=None, new_child=None):
        sibling_m = self.get_node_m(node=sibling_node)
        temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=sibling_node, m=sibling_m)
        dst_m = self.get_node_m(node=dst_node)
        keys, pointers = self.get_all_keys_and_pointers_from_node(node=dst_node, m=dst_m)

        #new children
        temp_children = self.get_all_child_pointers_from_node(node=dst_node, m=dst_m)
        sibling_children = self.get_all_child_pointers_from_node(node=sibling_node, m=sibling_m)
        temp_children += sibling_children

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
        i = bisect.bisect_left(temp_keys, key)
        temp_keys.insert(i, key)
        temp_pointers.insert(i, record_address)

        #child
        if new_child:
            temp_children.insert(i+1, new_child)
        ###########################################
        mid_index = len(temp_keys) // 2
        r_keys = temp_keys[mid_index+1:]
        r_ptrs = temp_pointers[mid_index+1:]
        r_children = temp_children[mid_index+1:]

        parent_key = temp_keys[mid_index]
        parent_ptr = temp_pointers[mid_index]

        dst_keys = temp_keys[:mid_index]
        dst_ptrs = temp_pointers[:mid_index]
        d_children = temp_children[:mid_index+1]
        # OF node
        self.write_node(node_address=dst,
                        child_ptrs=d_children,
                        keys=dst_keys,
                        values=dst_ptrs,
                        parent_pointer=parent
                        )
        # right node
        self.write_node(node_address=sibling,
                        child_ptrs=r_children,
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

        parent = self.get_parent_pointer_from_node(dst_node)
        # new node becomes right node
        new_right = self.tree_interface.get_new_node_address()

        # adjust new pointer and parent
        if new_child:
            dst_children.insert(i + 1, new_child)
            # print("blblbl",dst_children)
            for child in dst_children[middle_key+1:]:
                child_node = self.tree_interface.read_page(child)
                p_ptr_offset = self.tree_interface.parent_pointer_offset
                child_node[p_ptr_offset:p_ptr_offset+POINTER_SIZE] = new_right.to_bytes(POINTER_SIZE, 'little')
                self.tree_interface.write_page(child, child_node)

        self.write_node(node_address=new_right,
                        child_ptrs=dst_children[middle_key+1:], ######################
                        keys=dst_keys[middle_key+1:],
                        values=dst_pointers[middle_key+1:],
                        parent_pointer=parent)
        # old node is left node
        self.write_node(node_address=dst,
                        child_ptrs=dst_children[:middle_key+1], ######################
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
        elif parent_m >= 2*self.order:
            # self.split_node(parent, parent_node, key_to_go_up, ptr_to_go_up, new_right)
            self.handle_overflow(parent_node, parent, None, key_to_go_up, ptr_to_go_up, new_child=new_right)#TODO----------
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

    def update_parent_pointers(self, node_address=NULL_ADDRESS):
        temp = self.tree_interface.write_counter
        temp2 = self.tree_interface.read_counter
        if node_address == NULL_ADDRESS:
            node_address = self.root
        node = self.tree_interface.read_page(node_address)
        node_m = self.get_node_m(node=node)
        children = self.get_all_child_pointers_from_node(node=node, m=node_m)

        p_ptr_offset = self.tree_interface.parent_pointer_offset
        for child in children:
            if child != NULL_ADDRESS:
                child_node = self.tree_interface.read_page(child)
                child_node[p_ptr_offset:p_ptr_offset+POINTER_SIZE] = node_address.to_bytes(POINTER_SIZE, 'little')
                self.tree_interface.write_page(child, child_node)
                self.update_parent_pointers(node_address=child)
        if node_address == self.root:
            # without parent update cost
            self.tree_interface.read_counter = temp2
            self.tree_interface.write_counter = temp
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
            result = self.search(search_key=key)
            if not result and result != 0:
                return DOES_NOT_EXIST
            else:
                search_key = key
                current = self.path_buffer[-1]
                current_node = self.node_buffer[current]
                current_m = self.get_node_m(node=current_node)
                current_children = self.get_all_child_pointers_from_node(node=current_node, m=current_m)
                curr_keys, curr_pointers = self.get_all_keys_and_pointers_from_node(current_node, current_m)
                curr_parent = self.get_parent_pointer_from_node(current_node)
                key, pointer, leaf, index, keys, pointers, parent, children = None, None, None, None, None, None, None, None
                # check if in leaf
                if self.get_all_child_pointers_from_node(node=current_node, m=current_m)[0] == NULL_ADDRESS:
                    leaf = current
                    parent = self.get_parent_pointer_from_node(current_node)
                    children = current_children
                    keys, pointers = curr_keys, curr_pointers
                    index = keys.index(search_key) + 1
                else:
                    key_offset = curr_keys.index(search_key)
                    key, pointer, leaf, index, keys, pointers, parent, children = self.find_predecessor(key_offset, current_node, current)
                    curr_keys[key_offset] = key
                    curr_pointers[key_offset] = pointer
                    self.write_node(node_address=current,
                                    child_ptrs=current_children,
                                    keys=curr_keys,
                                    values=curr_pointers,
                                    parent_pointer=curr_parent)
                keys.pop(index-1)
                data_pointer = pointers.pop(index-1)
                children.pop(index)
                self.data_interface.write_entry(index=data_pointer, record=DELETE_RECORD)

                self.write_node(node_address=leaf,
                                child_ptrs=children,
                                keys=keys,
                                values=pointers,
                                parent_pointer=parent)
                index -= 1
                if len(keys) < self.order:
                    l_node = self.tree_interface.read_page(index=leaf)
                    self.handle_underflow(leaf, l_node, parent)
                self.update_parent_pointers()
                return OK

    def find_predecessor(self, key_offset, node, node_address):
        node_m = self.get_node_m(node=node)
        node_children = self.get_all_child_pointers_from_node(node=node, m=node_m)
        l_child = node_children[key_offset]
        self.path_buffer.append(l_child)
        l_node = self.tree_interface.read_page(index=l_child)
        self.node_buffer[l_child] = l_node
        parent = self.get_parent_pointer_from_node(node=l_node)

        l_m = self.get_node_m(node=l_node)
        l_keys, l_pointers = self.get_all_keys_and_pointers_from_node(node=l_node, m=l_m)
        l_children = self.get_all_child_pointers_from_node(node=l_node, m=l_m)
        largest_key, largest_pointer = l_keys[l_m-1], l_pointers[l_m-1]
        while l_children[l_m] != NULL_ADDRESS:
            l_child = l_children[l_m]
            self.path_buffer.append(l_child)
            l_node = self.tree_interface.read_page(index=l_child)
            self.node_buffer[l_child] = l_node
            parent = self.get_parent_pointer_from_node(node=l_node)

            l_m = self.get_node_m(node=l_node)
            l_keys, l_pointers = self.get_all_keys_and_pointers_from_node(node=l_node, m=l_m)
            l_children = self.get_all_child_pointers_from_node(node=l_node, m=l_m)
            largest_key, largest_pointer = l_keys[l_m - 1], l_pointers[l_m - 1]

        return largest_key, largest_pointer, l_child, l_m, l_keys, l_pointers, parent, l_children

    def handle_underflow(self, node_address, node, parent):
        # get child index from parent
        parent_node = self.node_buffer[parent]
        parent_m = self.get_node_m(node=parent_node)
        child_index = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m).index(node_address)
        if self.compensation_for_deletion(node, node_address, parent, parent_node, parent_m):
             return
        self.merge(node_address, node, parent, parent_node, child_index)
        # merge_res = self.merge_nodes(path, leaf_node, leaf_offset, child_index)
        # print(merge_res)
        # parent_node = self.read_page(parent_offset)
        # parent_occupied = self.count_occupied_rps(parent_node)
        #
        # if parent_offset == self.root_offset:
        #     return {"status": "merged_into_root"}
        #
        # if parent_occupied < (RECORDS_PER_NODE + 1) // 2:
        #     return self.handle_underflow(path[:-1], parent_node, parent_offset)

    def compensation_for_deletion(self, node, node_address, parent, parent_node, parent_m):
        parent_children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
        parent_keys, parent_pointers = self.get_all_keys_and_pointers_from_node(node=parent_node, m=parent_m)
        child_index = parent_children.index(node_address)
        node_m = self.get_node_m(node=node)
        node_children = self.get_all_child_pointers_from_node(node=node, m=node_m)
        # try left sibling
        if child_index > 0:
            left_sibling = parent_children[child_index-1]
            left_node = self.tree_interface.read_page(index=left_sibling)
            self.node_buffer[left_sibling] = left_node
            left_m = self.get_node_m(node=left_node)
            if left_m > self.order:
                temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=left_node, m=left_m)
                temp_keys.append(parent_keys[child_index-1])
                temp_pointers.append(parent_pointers[child_index-1])
                node_keys, node_pointers = self.get_all_keys_and_pointers_from_node(node=node, m=node_m)
                temp_keys += node_keys
                temp_pointers += node_pointers

                middle_key = len(temp_keys)//2
                left_keys = temp_keys[:middle_key]
                left_pointers = temp_pointers[:middle_key]

                parent_key = temp_keys[middle_key]
                parent_pointer = temp_pointers[middle_key]
                parent_keys[child_index-1] = parent_key
                parent_pointers[child_index-1] = parent_pointer

                node_keys = temp_keys[middle_key+1:]
                node_pointers = temp_pointers[middle_key+1:]

                l_children = self.get_all_child_pointers_from_node(node=left_node, m=left_m)
                all_children = l_children + node_children
                self.write_node(node_address=left_sibling,
                                child_ptrs=all_children[:middle_key+1], ##########
                                keys=left_keys,
                                values=left_pointers,
                                parent_pointer=parent)
                self.write_node(node_address=node_address,
                                child_ptrs=all_children[middle_key+1:], ###########
                                keys=node_keys,
                                values=node_pointers,
                                parent_pointer=parent)
                self.write_node(node_address=parent,
                                child_ptrs=parent_children,
                                keys=parent_keys,
                                values=parent_pointers,
                                parent_pointer=self.get_parent_pointer_from_node(node=parent_node))
                return True
        # try right sibling
        elif child_index < parent_m:
            right_sibling = parent_children[child_index + 1]
            right_node = self.tree_interface.read_page(index=right_sibling)
            self.node_buffer[right_sibling] = right_node
            right_m = self.get_node_m(node=right_node)
            if right_m > self.order:
                temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=node, m=node_m)
                temp_keys.append(parent_keys[child_index])
                temp_pointers.append(parent_pointers[child_index])
                r_keys, r_pointers = self.get_all_keys_and_pointers_from_node(node=right_node, m=right_m)
                temp_keys += r_keys
                temp_pointers += r_pointers

                middle_key = len(temp_keys) // 2
                right_keys = temp_keys[middle_key+1:]
                right_pointers = temp_pointers[middle_key+1:]

                parent_key = temp_keys[middle_key]
                parent_pointer = temp_pointers[middle_key]
                parent_keys[child_index] = parent_key
                parent_pointers[child_index] = parent_pointer

                node_keys = temp_keys[:middle_key]
                node_pointers = temp_pointers[:middle_key]

                r_children = self.get_all_child_pointers_from_node(node=right_node, m=right_m)
                all_children = node_children + r_children
                self.write_node(node_address=right_sibling,
                                child_ptrs=all_children[middle_key+1:],  ##########
                                keys=right_keys,
                                values=right_pointers,
                                parent_pointer=parent)
                self.write_node(node_address=node_address,
                                child_ptrs=all_children[:middle_key+1],  ###########
                                keys=node_keys,
                                values=node_pointers,
                                parent_pointer=parent)
                self.write_node(node_address=parent,
                                child_ptrs=parent_children,
                                keys=parent_keys,
                                values=parent_pointers,
                                parent_pointer=self.get_parent_pointer_from_node(node=parent_node))
                return True
        return False

    def merge(self, node_address, node, parent, parent_node, child_index):
        #cant merge on root?
        print("merging, merging you-u-u")
        node_m = self.get_node_m(node=node)
        parent_m = self.get_node_m(parent_node)
        parent_children = self.get_all_child_pointers_from_node(node=parent_node, m=parent_m)
        parent_keys, parent_pointers = self.get_all_keys_and_pointers_from_node(node=parent_node, m=parent_m)
        parent_parent = self.get_parent_pointer_from_node(node=parent_node)
        merged_address = None

        if child_index > 0:
            left_sibling = parent_children[child_index - 1]
            left_node = self.node_buffer[left_sibling]
            left_m = self.get_node_m(left_node)
            temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=left_node, m=left_m)
            parentkey = parent_keys.pop(child_index-1)
            parentpointer = parent_pointers.pop(child_index-1)
            temp_keys.append(parentkey)
            temp_pointers.append(parentpointer)
            node_keys, node_pointers = self.get_all_keys_and_pointers_from_node(node=node, m=node_m)
            temp_keys += node_keys
            temp_pointers += node_pointers
            #combine children
            node_children = self.get_all_child_pointers_from_node(node=node, m=node_m)
            left_children = self.get_all_child_pointers_from_node(node=left_node, m=left_m)
            all_children = left_children + node_children

            if parent_parent == NULL_ADDRESS and len(parent_keys) == 0:
                parent = NULL_ADDRESS

            #new parent
            self.tree_interface.free_node_address(address=parent_children.pop(child_index))
            self.write_node(node_address=parent,
                            child_ptrs=parent_children,
                            keys=parent_keys,
                            values=parent_pointers,
                            parent_pointer=parent_parent)

            #new merged to left
            self.write_node(node_address=left_sibling,
                            child_ptrs=all_children,
                            keys=temp_keys,
                            values=temp_pointers,
                            parent_pointer=parent)

            merged_address = left_sibling

        else:
            right_sibling = parent_children[child_index + 1]
            right_node = self.node_buffer[right_sibling]
            right_m = self.get_node_m(right_node)
            temp_keys, temp_pointers = self.get_all_keys_and_pointers_from_node(node=node, m=node_m)
            parentkey = parent_keys.pop(child_index)
            parentpointer = parent_pointers.pop(child_index)
            temp_keys.append(parentkey)
            temp_pointers.append(parentpointer)
            r_keys, r_pointers = self.get_all_keys_and_pointers_from_node(node=right_node, m=right_m)
            temp_keys += r_keys
            temp_pointers += r_pointers
            # combine children
            node_children = self.get_all_child_pointers_from_node(node=node, m=node_m)
            right_children = self.get_all_child_pointers_from_node(node=right_node, m=right_m)
            all_children = node_children + right_children

            if parent_parent == NULL_ADDRESS and len(parent_keys) == 0:
                parent = NULL_ADDRESS

            # new parent
            self.tree_interface.free_node_address(address=parent_children.pop(child_index+1))
            self.write_node(node_address=parent,
                            child_ptrs=parent_children,
                            keys=parent_keys,
                            values=parent_pointers,
                            parent_pointer=parent_parent)

            # new merged to left
            self.write_node(node_address=node_address,
                            child_ptrs=all_children,
                            keys=temp_keys,
                            values=temp_pointers,
                            parent_pointer=parent)

            merged_address = node_address

        if len(parent_keys) < self.order:
            if parent_parent == NULL_ADDRESS: # root underflow
                if len(parent_keys) == 0: # merge new root with two children
                    self.tree_interface.free_node_address(address=self.root)
                    self.root = merged_address
            else:
                parent_node = self.tree_interface.read_page(parent)
                self.handle_underflow(parent, parent_node, parent_parent)

    def update_record(self, key, record):
        if self.delete_record(key=key) == DOES_NOT_EXIST:
            return DOES_NOT_EXIST
        else:
            return self.add_record(key=key, record=record)

    def reorganize_data(self, node_address=NULL_ADDRESS, temp_data_interface=None):
        if node_address == NULL_ADDRESS:
            display_data_file(DEFAULT_DATA_FILENAME, lines=self.data_interface.autoindexing)
            temp_data_interface = DataInterface(filename=DEFAULT_REORGANIZE_FILENAME)
            node_address = self.root
            self.tree_interface.reset_read_writes()
            self.data_interface.reset_access_counter()
            print("----Reorganize the file----")
        node = self.tree_interface.read_page(node_address)
        node_m = self.get_node_m(node)
        children = self.get_all_child_pointers_from_node(node, node_m)
        keys, pointers = self.get_all_keys_and_pointers_from_node(node, node_m)
        parent = self.get_parent_pointer_from_node(node)
        end = 0
        new_pointers = []
        for i in range(node_m):
            if children[i] != NULL_ADDRESS:
                self.reorganize_data(node_address=children[i], temp_data_interface=temp_data_interface)
            record = self.data_interface.read_entry(pointers[i])
            # print(f"key: {keys[i]}, record: {record}")
            new_data_pointer = temp_data_interface.write_entry(index=None, record=(keys[i], record[0], record[1]))
            new_pointers.append(new_data_pointer)
            end = i
        # print(keys, new_pointers)
        self.write_node(node_address=node_address,
                        child_ptrs=children,
                        keys=keys,
                        values=new_pointers,
                        parent_pointer=parent)
        end += 1
        if children[end] != NULL_ADDRESS:
            self.reorganize_data(node_address=children[end], temp_data_interface=temp_data_interface)

        # write the buffer file to main DATA_FILE after reorganization
        if node_address == self.root:
            temp_data_interface.flush_write_buffer()
            display_data_file(filename=DEFAULT_REORGANIZE_FILENAME, lines=self.data_interface.autoindexing)
            self.data_interface.copy_from_data_interface(temp_data_interface)