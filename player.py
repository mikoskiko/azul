# Plik player.py - bot1 vs user

from tile    import *
from factory import *
from board   import *
from state   import *

tile_to_number = {
    "blue": 0,
    "yellow": 1,
    "red": 2,
    "black": 3,
    "lightblue": 4
}

def manual_player(st, b):
    print(st.state_to_str() + "\n")
    print(f"You are player {st.t + 1} ")
    print("Input m represents the middle factory, a line number out of range goes in overflow.")
    if st.t == 1:  # Sprawdź, czy aktualnym graczem jest player 2 (bot)
        bot_move = bot_player(st, b)
        bot_move_str = " ".join(map(str, bot_move))  # Konwertuj krotkę na łańcuch
        print(bot_move_str)
        inp =bot_move_str
    else:
        inp = input("Input format (factory-number tile-number line-number): ")

    maybe_err = validate_input(st, b, parse_input(inp))
    while isinstance(maybe_err, str):
        print(maybe_err)
        print("Try again: ", end="")
        maybe_err = validate_input(st, b, parse_input(input()))
    return maybe_err



def bot_player(st, b):
    best_factory_idx = None
    best_tile = None
    max_tile_count = 0

    # Znajdź fabrykę z największą liczbą płytek jednego koloru
    for i, factory in enumerate(st.fset.factories):
        if len(factory) > 0:
            tile_counts = {}
            for tile in factory:
                if tile not in tile_counts:
                    tile_counts[tile] = 0
                tile_counts[tile] += 1
            most_common_tile = max(tile_counts, key=tile_counts.get)
            if tile_counts[most_common_tile] > max_tile_count:
                max_tile_count = tile_counts[most_common_tile]
                best_factory_idx = i + 1
                best_tile = most_common_tile

    # Sprawdź środek, jeśli ma więcej płytek jednego koloru
    tile_counts = {}
    for tile in st.fset.middle:
        if tile not in tile_counts:
            tile_counts[tile] = 0
        tile_counts[tile] += 1
    if tile_counts:
        most_common_tile = max(tile_counts, key=tile_counts.get)
        if tile_counts[most_common_tile] > max_tile_count:
            max_tile_count = tile_counts[most_common_tile]
            best_factory_idx = 'm'
            best_tile = most_common_tile

    # Znajdź najlepszą linię do umieszczenia płytek
    best_line_num = None
    overflow_line = 5  # Linia overflow
    for line_num, (num_tiles, tile) in enumerate(b.staging):
        # num_tiles to liczba płytek już w tej linii
        # tile to kolor płytek już w tej linii (lub None jeśli linia jest pusta)

        # Sprawdź, czy ten kolor płytek jest już w tej linii na tablicy
        if any([p[0] == best_tile and p[1] for p in b.wall[line_num]]):
            continue

        if not tile or tile == best_tile:
            space_left = line_num + 1  # linie są indeksowane od 0, więc linia 0 ma miejsce na 1 płytkę, linia 1 na 2 płytki, itd.
            if space_left >= max_tile_count:
                best_line_num = line_num
                break
            elif space_left >= 1 and best_line_num is None:
                best_line_num = line_num

    # Jeśli nie znaleziono odpowiedniej linii, użyj overflow
    if best_line_num is None:
        best_line_num = overflow_line

    best_tile_num = tile_to_number[best_tile]  # Konwertuj kolor na numer
    return (best_factory_idx, best_tile_num, best_line_num)



def parse_input(inp):
    pinp = inp.split()
    if len(pinp) == 3:
        pfid  = pinp[0] if pinp[0] == "m" or not pinp[0].isnumeric() else int(pinp[0])
        ptile = pinp[1] if not pinp[1].isnumeric() else int(pinp[1])
        pline = pinp[2] if not pinp[2].isnumeric() else int(pinp[2])
        return (pfid, ptile, pline)
    else: return pinp

def validate_input(st, b, i):
    print("Parsed input:", i)
    if len(i) != 3:
        return f"Expected at least 3 inputs, given {len(i)}"
    else:
        (f_id, tile, stg_lin_num) = i
        if not is_valid_f_id(f_id, necessary_factories(st.np)):
            return make_bad_f_id_str(f_id)
        elif not is_valid_tile(tile):
            return make_bad_tile_str(tile)
        elif not is_valid_line_num(stg_lin_num):
            return make_bad_line_str(tile)
        elif invalid_factory_move(idx_to_tile(tile), f_id, st.fset):
            return invalid_factory_move(idx_to_tile(tile), f_id, st.fset)
        elif invalid_tile_move(idx_to_tile(tile), stg_lin_num, b):
            return invalid_tile_move(idx_to_tile(tile), stg_lin_num, b)
        else:
            return sanitize(f_id, tile, stg_lin_num)

def sanitize(f_id, tile, line_num):
    return (clean_f_id(f_id), idx_to_tile(tile), clean_stg_line(line_num))

################################
# Validation Utilities         #
################################

def is_valid_f_id(f_id, num_factories):
    return f_id == "m" or (isinstance(f_id, int) and f_id > 0 and f_id <= num_factories)

def is_valid_tile(t):
    return isinstance(t, int) and t < len(tiles)

def is_valid_line_num(n):
    return isinstance(n, int)

def invalid_factory_move(tile, f_id, fset):
    factory_in_question = fset.middle if f_id == "m" else fset.factories[f_id - 1]
    if len(factory_in_question) == 0:
        return "can't ask for tiles from empty factory"
    elif factory_in_question[0] == one_tile and len(factory_in_question) == 1:
        return "can't only take the one_tile"
    elif not (tile in factory_in_question):
        return "can't take a color not in the chosen factory"
    else:
        return False

def invalid_tile_move(tile, stg_lin_num, b):
    if stg_lin_num >= len(b.staging):
        return False
    else:
        stg_line      = b.staging[stg_lin_num]
        is_valid_line = not stg_line[1] or stg_line[1][1] == tile
        if not is_valid_line:
            return "can't place a tile on a line that contains a different colored tile"
        elif any([p[0] == tile and p[1] for p in b.wall[stg_lin_num]]):
            return "can't place a tile on the same row as the wall where the tile is already placed"
        else: return False

def clean_f_id(f_id):
    if f_id == "m":
        return -1
    else:
        return f_id

def clean_stg_line(s_line):
    if s_line < 0 or s_line > 4:
        return 6
    else:
        return s_line

def make_bad_tile_str(x):
    return f"oops! expected tile to be one of the listed numbers, got: {x}"

def make_bad_line_str(x):
    return f"oops! expected line number to be between [0,4] or 6, got: {x}"

def make_bad_f_id_str(x):
    return f"oops! expected either \"m\" or a number between 1 and 5; got: {x}"