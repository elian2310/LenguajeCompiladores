from unittest import result
import ñ

while True:
    text = input("ñ >> ")
    if text.strip() == "": continue
    res, error = ñ.exe("<input>",text)

    if error: print(error.como_str())
    elif res:
        if len(res.elementos) == 1:
            print(repr(res.elementos[0]))
        else:
            print(repr(res))