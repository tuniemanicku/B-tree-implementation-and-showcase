from BTreeInterface import BTreeInterface
from utils import *

class BTree:
    def __init__(self):
        self.interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME)
        self.height = 0
        self.order = BTREE_ORDER
        self.page_size