from BTree import BTree
from utils import *
from test import TreeLoader
import math
import matplotlib.pyplot as plt
import numpy as np

SCALE = 10
MAX_N = 500

def get_read_accesses(btree):
    t_reads, t_writes = btree.get_access_counter()
    d_reads, d_writes = btree.get_data_access_counter()
    # print(t_reads, end=" ")
    return t_reads

# 1. test tree space occupied
def test_space_occupied(order=BTREE_ORDER):
    n_values = [i for i in range(10, 100)]
    print(n_values)
    space_occupied_x = []
    space_occupied_y = []
    for n in n_values:
        btree = BTree(order=order)
        tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME, btree=btree)
        tl.write_random_data(to_generate=n)
        tl.load()
        space_occupied = btree.get_space_occupied() * 100  # percentage
        print(f"n: {n}, space occupied: {space_occupied:.2f}%")
        space_occupied_x.append(n)
        space_occupied_y.append(space_occupied)

    space_mean = np.mean(space_occupied_y)
    plt.plot(space_occupied_x, space_occupied_y, "o--")
    plt.axhline(y=math.log(2) * 100, color="yellow", linestyle="-")
    plt.axhline(y=float(space_mean), color="yellow", linestyle="-")
    plt.title(f"Zajętość miejsca w drzewie dla danej liczby rekordów i d = {order}")
    plt.show()

# 2. test average access count for read (d, N)
def test_average_access_count_for_read():
    d_values = [2,4,10,20,100]
    n_values = [10,20,50,100,200,500,1000]
    for d in d_values:
        print("--------")
        print(f"d={d}")
        for n in n_values:
            print(f"\tn={n}")
            btree = BTree(order=d)
            tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME, btree=btree)
            tl.write_random_data(to_generate=n)
            tl.load()
            to_search = np.random.randint(1, KEY_MAX_VALUE-1, size=10)
            all = []
            for key in to_search:
                btree.tree_interface.reset_read_writes()
                btree.search(key)
                all.append(get_read_accesses(btree))
            print(np.mean(np.array(all)))

# 3. test average access count for add (d, N)

# 4. test average access count for delete (d, N)

def main():
    # for d in range(2, 10+1):
    #     test_space_occupied(order=d)
    print("AVERAGE ACCESS COUNT FOR READ TEST")
    print("----------------------------------")
    test_average_access_count_for_read()

    print("AVERAGE ACCESS COUNT FOR EXHAUSTIVE READ TEST")
    print("----------------------------------")
    test_average_access_count_for_exhaustive_read()

if __name__ == "__main__":
    main()