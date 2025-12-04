def test_mode_loop():
    print("Test data mode")

def interactive_mode_loop():
    print("Interactive mode")

def main_loop():
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

def main():
    main_loop()

if __name__ == "__main__":
    main()