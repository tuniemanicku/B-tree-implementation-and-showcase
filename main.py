import os.path

from BTree import BTree
from utils import *
from test import TreeLoader, hexdump_4byte

def test_mode_loop():
    btree = BTree()
    print("----------------------------")
    print("Test data mode")
    print("Generate or load data?")
    print("[1] Generate")
    print("[2] Load")
    options = [1, 2]

    choice = input("Choice: ")
    number = None
    try:
        number = int(choice)
        if not number in options:
            print("Wrong input, try again")
    except:
        print("Wrong input, try again")
    if number == 1:
        to_generate = None
        while to_generate is None:
            try:
                to_generate = int(input("Number of records to generate: "))
            except:
                print("Wrong input, try again")
                to_generate = None
        tree_loader = TreeLoader(DEFAULT_TEST_DATA_FILENAME, btree)
        tree_loader.write_random_data(to_generate=to_generate)
        tree_loader.load()
        btree.display()
        return btree
    elif number == 2:
        file_exists = False
        fname = None
        while not file_exists:
            fname = input("Test data file: ")
            if os.path.isfile(fname):
                file_exists = True
            elif fname == "exit":
                break
            else:
                print("File does not exist")
        if fname == "exit":
            return None
        tree_loader = TreeLoader(fname, btree)
        tree_loader.write_test_data()
        tree_loader.load()
        btree.display()
        return btree
    else:
        return None

def interactive_mode_loop(btree):
    if not btree:
        btree = BTree()
    print("----------------------------")
    print("Interactive mode")
    interactive_mode_running = True
    while interactive_mode_running:
        options = [1,2,3,4,5,6]
        print("============================")
        print("Choose action to perform:")
        print("[1] Add record")
        print("[2] Read record")
        print("[3] View file sorted by key")
        print("[4] Delete record")
        print("[5] Update record")
        print("[6] Exit")
        print("============================")
        choice = input("Choice: ")
        number = None
        try:
            number = int(choice)
            if not number in options:
                print("Wrong input, try again")
                choice = None
        except:
            print("Wrong input, try again")
            choice = None
        if number == 1:
            print("add record:")
            key = int(input("Key: "))
            record = input("Record [U I]: ").split(" ")
            result = btree.add_record(key=key, record=(float(record[0]), float(record[1])))
            if result == ALREADY_EXISTS:
                print("Record with given key already exists")
            else:
                print(f"Record with key {key} added")
        elif number == 2:
            print("read record")
            key = int(input("Key: "))
            result = btree.read_record(key=key)
            if result:
                print(f"Record found: {result}")
            else:
                print("Record not found")
        elif number == 3:
            print("view sorted file")
        elif number == 4:
            print("Delete record")
            key = int(input("Key: "))
            result = btree.delete_record(key=key)
            if result == DOES_NOT_EXIST:
                print("Record with given key doesn't exist")
            else:
                print(f"Record with key {key} deleted")
        elif number == 5:
            print("Update record")
        else:
            print("Interactive mode exitting")
            interactive_mode_running = False
        #display tree structure if choice and not exit
        if choice and interactive_mode_running:
            btree.display()
        # hexdump_4byte("btree.bin")

def main_loop():
    program_running = True
    btree = None
    while program_running:
        print("----------------------------")
        print("SBD - Task 2 - B-tree")
        choice = None
        options = [1,2,3]
        number = None
        while not choice:
            print("============================")
            print("Choose program mode or exit:")
            print("[1] Test data mode")
            print("[2] Interactive mode")
            print("[3] Exit")
            print("============================")
            choice = input("Choice: ")
            try:
                number = int(choice)
                if not number in options:
                    print("Wrong input, try again")
                    choice = None
            except:
                print("Wrong input, try again")
                choice = None
        if number == 1:
            btree = test_mode_loop()
        elif number == 2:
            interactive_mode_loop(btree)
        else:
            print("Program exitting")
            program_running = False

def main():
    main_loop()

if __name__ == "__main__":
    main()