import asyncio
import curses
import random

import itertools
import time

from curses_tools import draw_frame, read_controls
from fire import fire


def load_frame_from_file(filename):
    with open(filename, 'r') as fd:
        return fd.read()
async def sleep(tic_timeout=1):
    for _ in range(tic_timeout):
        await asyncio.sleep(0)

async def animate_spaceship(canvas, row, column, frames):
    frame_cycle = itertools.cycle(frames)
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed:
            pass
        if row + rows_direction < 1:
            row = 2
        if row + rows_direction >= curses.LINES - 9:
            row = curses.LINES - 11
        if column + columns_direction <= 0:
            column = 2
        if column + columns_direction >= curses.COLS - 5:
            column = curses.COLS - 7
        row += rows_direction
        column += columns_direction
        frame = next(frame_cycle)
        draw_frame(canvas, row, column, frame)
        canvas.refresh()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
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
    rocket_frames = [rocket_frame_1, rocket_frame_2]
    curses.curs_set(False)
    canvas.border(0, 0, 0, 0, 0, 0, 0, 0)
    coroutines = []
    coroutines_fire = []

    coroutine_spaceship = animate_spaceship(canvas, curses.LINES // 2, curses.COLS // 2 - 2, rocket_frames)
    coroutines.append(coroutine_spaceship)

    for _ in range(curses.LINES - 1 - curses.LINES // 2):
        shot_row, shot_col = curses.LINES // 2, curses.COLS // 2
        coroutine_fire = fire(canvas, shot_row, shot_col)
        coroutines_fire.append(coroutine_fire)
    for _ in range(50):
        coroutine = blink(canvas, random.randint(1, curses.LINES - 2), random.randint(1, curses.COLS - 2), random.randint(0, 20),
                          random.choice(SYMBOLS_STAR))
        coroutines.append(coroutine)
    while True:
        for coroutine in coroutines:
            coroutine.send(None)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)

        for coroutine_fire in coroutines_fire:
            try:
                coroutine_fire.send(None)
            except StopIteration:
                coroutines_fire.remove(coroutine_fire)
            if len(coroutines_fire) == 0:
                break


if __name__ == '__main__':
    curses.wrapper(draw)
