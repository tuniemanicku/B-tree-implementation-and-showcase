import bisect

def sort_parent_and_siblings(keys1, keys2, key, pointers1, pointers2, pointer):
    for x in range(len(keys2)):
        i = bisect.bisect_left(keys1, keys2[x])
        keys1.insert(i, keys2[x])
        pointers1.insert(i, pointers2[x])
    i = bisect.bisect_left(keys1, key)
    keys1.insert(i, key)
    pointers1.insert(i, pointer)
    return keys1, pointers1