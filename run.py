import asyncio
import curses
import random

import itertools
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from fire import fire


def load_frame_from_file(filename):
    with open(filename, 'r') as fd:
        return fd.read()


async def sleep(tic_timeout=1):
    for _ in range(tic_timeout):
        await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, spaceship_row, spaceship_column, frames):
    frame_cycle = itertools.cycle(frames)
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed:
            pass
        if 0 < row + rows_direction < curses.LINES - spaceship_row:
            row += rows_direction
        if 0 < column + columns_direction < curses.COLS - spaceship_column:
            column += columns_direction
        frame = next(frame_cycle)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


async def blink(canvas, row, column, offset_tics=1, symbol='*'):
    await sleep(offset_tics)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


def draw(canvas):
    canvas.nodelay(True)

    TIC_TIMEOUT = 0.1
    SYMBOLS_STAR = '+*.:'
    rocket_frame_1 = load_frame_from_file('rocket_frame_1.txt')
    rocket_frame_2 = load_frame_from_file('rocket_frame_2.txt')
    spaceship_row, spaceship_column = get_frame_size(rocket_frame_1)

    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]
    curses.curs_set(False)
    canvas.border(0, 0, 0, 0, 0, 0, 0, 0)
    coroutines = []

    coroutine_spaceship = animate_spaceship(
        canvas,
        curses.LINES // 2 - spaceship_row // 2,
        curses.COLS // 2 - 2,
        spaceship_row,
        spaceship_column,
        rocket_frames
    )
    coroutines.append(coroutine_spaceship)

    for _ in range(curses.LINES - 1 - curses.LINES // 2):
        shot_row, shot_col = (curses.LINES - spaceship_row) // 2, curses.COLS // 2
        coroutine_fire = fire(canvas, shot_row, shot_col)
        coroutines.append(coroutine_fire)
    for _ in range(50):
        coroutine = blink(canvas, random.randint(1, curses.LINES - 2), random.randint(1, curses.COLS - 2),
                          random.randint(0, 20),
                          random.choice(SYMBOLS_STAR))
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.wrapper(draw)
