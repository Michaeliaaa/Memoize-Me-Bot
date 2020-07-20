from random import randint

quotes_file = "quotes.txt"

def get_random_quote():
    start_line  = None
    end_line    = None
    with open(quotes_file) as file:
        line = file.readlines()
    for i in range(len(line)-1):
        random_line = (randint(0, len(line)-1))
        if "%%" in line[random_line]:
            start_line = random_line
            break
    for i in range(start_line+1, len(line)):
        if "%%" in line[i]:
            end_line = i
            break
    start_line += 1
    quote = "".join(line[start_line:end_line])
    return quote
