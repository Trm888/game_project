import asyncio
import curses
import os
import random

import itertools
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from explosion import explode
from obstacles import Obstacle
from physics import update_speed
from game_scenario import PHRASES, get_garbage_delay_tics

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
year = 1957


def load_frame_from_file(filename):
    with open(filename, 'r') as fd:
        return fd.read()


async def sleep(tic_timeout=1):
    for _ in range(tic_timeout):
        await asyncio.sleep(0)


async def show_gameover(canvas):
    with open(os.path.join('gameover', 'gameover.txt'), 'r') as fd:
        gameover_frame = fd.read()
    rows, columns = get_frame_size(gameover_frame)
    row = curses.LINES // 2 - rows // 2
    column = curses.COLS // 2 - columns // 2
    while True:
        draw_frame(canvas, row, column, gameover_frame)
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')
    row += rows_speed
    column += columns_speed
    symbol = '-' if columns_speed else '|'
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1
    curses.beep()
    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed
        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                obstacles_in_last_collisions.append(obstacle)
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    row = 0
    rows_size, columns_size = get_frame_size(garbage_frame)
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        obstacle = Obstacle(row, column, rows_size, columns_size)
        obstacles.append(obstacle)
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacles.remove(obstacle)
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            await explode(canvas, row + rows_size // 2, column + columns_size // 2)
            return


async def fill_orbit_with_garbage(canvas, garbage_frames, tic_timeout=10):
    while True:
        column = random.randint(1, curses.COLS - 2)
        frame = random.choice(garbage_frames)
        garbage_row, garbage_column = get_frame_size(frame)
        proposed_end_column = column + garbage_column

        if proposed_end_column > curses.COLS - 2:
            column = curses.COLS - garbage_column - 2
        if proposed_end_column < 0:
            column = 0
        coroutines.append(fly_garbage(canvas, column=column, garbage_frame=frame))
        if year > 1961:
            await sleep(get_garbage_delay_tics(year))
        else:
            await sleep(tic_timeout)


async def show_phrase(canvas, row, column):
    global year
    while True:
        phrase = PHRASES.get(year, '')
        if phrase:
            canvas.derwin(row, column).addstr(phrase)
        await sleep(1)



async def show_year(canvas):
    global year
    while True:
        year += 1
        canvas.addstr(1, 1, f'Year: {year}')
        await sleep(5)


async def animate_spaceship(canvas, row, column, spaceship_row, spaceship_column, frames):
    frame_cycle = itertools.cycle(frames)
    row_speed = column_speed = 0
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed and year > 2020:
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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column, spaceship_row, spaceship_column):
                coroutines.append(show_gameover(canvas))
                return


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
    coroutines.append(show_year(canvas))
    coroutines.append(show_phrase(canvas, 2, 1))


    for _ in range(50):
        coroutine = blink(canvas,
                          random.randint(1, curses.LINES - 2),
                          random.randint(1, curses.COLS - 2),
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
