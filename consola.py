from unittest import result
import ñ

while True:
    text = input("ñ >> ")
    res, error = ñ.exe("<input>",text)

    if error: print(error.como_str())
    elif res: print(repr(res))