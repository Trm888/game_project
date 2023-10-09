import asyncio
import curses
import os
import random

import itertools
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from fire import fire
from space_garbage import fly_garbage
from physics import update_speed

coroutines = []
def load_frame_from_file(filename):
    with open(filename, 'r') as fd:
        return fd.read()


async def sleep(tic_timeout=1):
    for _ in range(tic_timeout):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames, tic_timeout=10):


    while True:
        column = random.randint(1, curses.COLS - 2)
        frame = random.choice(garbage_frames)
        garbage_row, garbage_column = get_frame_size(frame)

        if column + garbage_column > curses.COLS - 2:
            column = curses.COLS - garbage_column - 2


        coroutines.append(fly_garbage(canvas, column=column, garbage_frame=frame))

        await sleep(tic_timeout)




async def animate_spaceship(canvas, row, column, spaceship_row, spaceship_column, frames):
    frame_cycle = itertools.cycle(frames)
    row_speed = column_speed = 0
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed:
            coroutines.append(fire(canvas, row, column + spaceship_column // 2))


        if 0 < row + rows_direction + row_speed < curses.LINES - spaceship_row:
            row += rows_direction
            row += row_speed
        if 0 < column + columns_direction + column_speed < curses.COLS - spaceship_column:
            column += columns_direction
            column += column_speed
        frame = next(frame_cycle)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)




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


    garbage_frames = []
    for garbage in os.listdir('garbage'):
        garbage_frames.append(load_frame_from_file(os.path.join('garbage', garbage)))

    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]
    curses.curs_set(False)
    canvas.border(0, 0, 0, 0, 0, 0, 0, 0)


    coroutine_spaceship = animate_spaceship(
        canvas,
        curses.LINES // 2 - spaceship_row // 2,
        curses.COLS // 2 - 2,
        spaceship_row,
        spaceship_column,
        rocket_frames
    )
    coroutines.append(coroutine_spaceship)
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames))


    # for _ in range(curses.LINES - 1 - curses.LINES // 2):
    #     shot_row, shot_col = (curses.LINES - spaceship_row) // 2, curses.COLS // 2
    #     coroutine_fire = fire(canvas, shot_row, shot_col)
    #     coroutines.append(coroutine_fire)
    for _ in range(50):
        coroutine = blink(canvas, random.randint(1, curses.LINES - 2), random.randint(1, curses.COLS - 2),
                          random.randint(0, 20),
                          random.choice(SYMBOLS_STAR))
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.wrapper(draw)
