from BTreeInterface import BTreeInterface
from utils import *

class BTree:
    def __init__(self):
        self.height = 0
        self.order = BTREE_ORDER
        self.interface = BTreeInterface(filename=DEFAULT_BTREE_FILENAME, order=BTREE_ORDER)
