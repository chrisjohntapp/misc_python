#!/usr/bin/env python3

# Removes a number of lines from a file in-place, and without
# writing another copy of the whole file (like sed does).

import os, sys

if len(sys.argv) != 3:
    print(sys.argv[0] + ": Invalid number of arguments.")
    print ("Usage: " + sys.argv[0] + " <linecount> <filename>")
    print ("To remove <linecount> lines from the end of the file.")
    exit(2)

number = int(sys.argv[1])
file = sys.argv[2]
count = 0

with open(file,'r+b', buffering=0) as f:
    f.seek(0, os.SEEK_END)
    end = f.tell()
    while f.tell() > 0:
        f.seek(-1, os.SEEK_CUR)
        print(f.tell())
        char = f.read(1)
        if char != b'\n' and f.tell() == end:
            print ("No change: file does not end with a newline.")
            exit(1)
        if char == b'\n':
            count += 1
        if count == number + 1:
            f.truncate()
            print ("Removed " + str(number) + " lines from end of file.")
            exit(0)
        f.seek(-1, os.SEEK_CUR)

if count < number + 1:
    print("No change: requested removal would leave empty file.")
    exit(3)
