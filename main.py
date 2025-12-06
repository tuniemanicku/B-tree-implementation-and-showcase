import os.path

from BTree import BTree
from utils import *

def test_mode_loop():
    btree = BTree()
    print("----------------------------")
    print("Test data mode")
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
        return
    with open(fname, "rb") as test_file:
        instruction = test_file.read(INSTRUCTION_TYPE_LENGTH)
        if not instruction:
            print("Test file empty")
            return
        while instruction:
            print("Process instruction")
            instruction = test_file.read()
            break

def interactive_mode_loop():
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
        try:
            number = int(choice)
            if not number in options:
                print("Wrong input, try again")
                choice = None
        except:
            print("Wrong input, try again")
            choice = None
        if number == 1:
            print("add record")
        elif number == 2:
            print("read record")
        elif number == 3:
            print("view sorted file")
        elif number == 4:
            print("Delete record")
        elif number == 5:
            print("Update record")
        else:
            print("Interactive mode exitting")
            interactive_mode_running = False

def main_loop():
    program_running = True
    while program_running:
        print("----------------------------")
        print("SBD - Task 2 - B-tree")
        choice = None
        options = [1,2,3]
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
            test_mode_loop()
        elif number == 2:
            interactive_mode_loop()
        else:
            print("Program exitting")
            program_running = False

def main():
    main_loop()

if __name__ == "__main__":
    main()