from Interfaces import *
from utils import *

class BTree:
    def __init__(self):
        self.height = 0
        self.order = BTREE_ORDER
        self.tree_interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME, order=BTREE_ORDER)
        self.data_interface = DataInterface(filename=DEFAULT_DATA_FILENAME)

        # B-tree root node address
        self.root = None

    def add_record(self, element):
        pass

    def read_record(self):
        pass

    def write_record(self):
        pass