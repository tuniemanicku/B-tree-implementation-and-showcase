from BTree import BTree
from utils import *
from test import TreeLoader
import math
import matplotlib.pyplot as plt
import numpy as np
import random

SCALE = 10
MAX_N = 500

def extract_added_keys(filename):
    keys = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if parts[0] == "a":
                key = int(parts[1])
                keys.append(key)

    return keys


def get_read_accesses(btree, both=False):
    t_reads, _ = btree.get_access_counter()
    d_reads, _ = btree.get_data_access_counter()
    # print(t_reads, end=" ")
    if both:
        return t_reads, d_reads
    else:
        return t_reads

def get_all_accesses(btree):
    t_reads, t_writes = btree.get_access_counter()
    d_reads, d_writes = btree.get_data_access_counter()
    return t_reads, t_writes, d_reads, d_writes

# 1. test tree space occupied
def test_space_occupied(order=BTREE_ORDER):
    n_values = [i for i in range(100, 1000, 100)]
    print(n_values)
    space_occupied_x = []
    space_occupied_y = []
    for n in n_values:
        btree = BTree(order=order)
        tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME_TXT, btree=btree)
        tl.write_random_data(to_generate=n)
        tl.load()
        space_occupied = btree.get_space_occupied() * 100  # percentage
        print(f"n: {n}, space occupied: {space_occupied:.2f}%")
        space_occupied_x.append(n)
        space_occupied_y.append(space_occupied)

    space_mean = np.mean(space_occupied_y)
    plt.plot(space_occupied_x, space_occupied_y, "o--")
    plt.axhline(y=math.log(2) * 100, color="yellow", linestyle="-")
    plt.axhline(y=float(space_mean), color="red", linestyle="-")
    plt.title(f"Occupation of space in a B-tree for d = {order}")
    plt.xlabel("n")
    plt.ylabel("Occupation percentage")
    plt.legend(["Calculated occupation", "Theoretical occupation", "Average occupation"])
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
            tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME_TXT, btree=btree)
            tl.write_random_data(to_generate=n)
            tl.load()
            to_search = np.random.randint(1, KEY_MAX_VALUE-1, size=10)
            all = []
            for key in to_search:
                btree.tree_interface.reset_read_writes()
                btree.search(key)
                all.append(get_read_accesses(btree))
            print(np.mean(np.array(all)))

# 3. test average access count for exhaustive read (d, N)
def test_average_access_count_for_exhaustive_read():
    d_values = [2, 4, 10, 20, 100]
    n_values = [10, 20, 50, 100, 200, 500, 1000]
    for d in d_values:
        print("--------")
        print(f"d={d}")
        for n in n_values:
            print(f"\tn={n}")
            btree = BTree(order=d)
            tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME_TXT, btree=btree)
            tl.write_random_data(to_generate=n)
            tl.load()

            btree.display_data(node_address=NULL_ADDRESS, to_print=False)
            tree, data = get_read_accesses(btree, both=True)
            print(f"records: {btree.record_count}, rc+nc: {btree.node_count + btree.record_count}")
            print(f"nodes count: {btree.node_count}")
            print(f"tree reads: {tree}, data reads: {data}")
            #-------------------------------------------------
            print("--reorganized--")
            btree.reorganize_data(to_print=False)
            btree.display_data(node_address=NULL_ADDRESS, to_print=False)
            tree, data = get_read_accesses(btree, both=True)
            print(f"records: {btree.record_count}, rc+nc: {btree.node_count+btree.record_count}")
            print(f"nodes count: {btree.node_count}")
            print(f"tree reads: {tree}, data reads: {data}")

# 4. test average access count for add (d, N)
def test_average_access_count_for_add():
    d_values = [2, 4, 10, 20, 100]
    n_values = [10, 20, 50, 100, 200, 500, 1000]
    for d in d_values:
        print("--------")
        print(f"d={d}")
        for n in n_values:
            print(f"\tn={n}")
            btree = BTree(order=d)
            tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME_TXT, btree=btree)
            tl.write_random_data(to_generate=n)
            tl.load()

            to_add = np.random.randint(1, KEY_MAX_VALUE - 1, size=100)
            counts_r_t = []
            counts_w_t = []
            for key in to_add:
                btree.tree_interface.reset_read_writes()
                result = btree.add_record(int(key), record=(1.0, 1.0))
                if result != ALREADY_EXISTS:
                    crt, cwt, crd, cwd = get_all_accesses(btree)
                    counts_r_t.append(crt)
                    counts_w_t.append(cwt)
            print(f"tree reads: {np.mean(np.array(counts_r_t)):.2f}", end="\t")
            print(f"tree writes: {np.mean(np.array(counts_w_t)):.2f}")
            print()

# 5. test average access count for delete (d, N)
def test_average_access_count_for_delete():
    d_values = [2, 4, 10, 20, 100]
    n_values = [20, 50, 100, 200, 500, 1000, 2000]
    for d in d_values:
        print("--------")
        print(f"d={d}")
        for n in n_values:
            print(f"\tn={n}")
            btree = BTree(order=d)
            tl = TreeLoader(filename=DEFAULT_TEST_DATA_FILENAME_TXT, btree=btree)
            tl.write_random_data(to_generate=n)
            tl.load()
            keys = extract_added_keys(DEFAULT_TEST_DATA_FILENAME_TXT)
            to_delete = random.sample(keys, k=min(100, n))
            counts_r_t = []
            counts_w_t = []
            for key in to_delete:
                btree.tree_interface.reset_read_writes()
                result = btree.delete_record(key=key)
                while result == DOES_NOT_EXIST:
                    key = random.randint(1, KEY_MAX_VALUE - 1)
                    result = btree.delete_record(key=key)
                crt, cwt, crd, cwd = get_all_accesses(btree)
                counts_r_t.append(crt)
                counts_w_t.append(cwt)
            print(f"tree reads: {np.mean(np.array(counts_r_t)):.2f}", end="\t")
            print(f"tree writes: {np.mean(np.array(counts_w_t)):.2f}")
            print()

def main():
    # d_values = [2, 4, 10, 20, 100]
    # for d in d_values:
    #     test_space_occupied(order=d)
    print("AVERAGE ACCESS COUNT FOR READ TEST")
    print("----------------------------------")
    # test_average_access_count_for_read()

    print("AVERAGE ACCESS COUNT FOR EXHAUSTIVE READ TEST")
    print("----------------------------------")
    test_average_access_count_for_exhaustive_read()

    print("AVERAGE ACCESS COUNT FOR ADD TEST")
    print("----------------------------------")
    # test_average_access_count_for_add()

    print("AVERAGE ACCESS COUNT FOR DELETE TEST")
    print("----------------------------------")
    # test_average_access_count_for_delete()

if __name__ == "__main__":
    main()