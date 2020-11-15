import pygame
import sys
import os
import random
import surface
import time
import color as c
import menu
import copy
import pickle
from abc import ABC, abstractmethod


class Painter(ABC):
    @abstractmethod
    def draw(self):
        pass


class HintError(Exception):
    pass


class Game(surface.Surface, Painter):

    def __init__(self):
        super().__init__()
        self.tables = Tables()
        self.cells_list = self.__set_cells()
        self.__buttons_list = self.__set_buttons()
        self.__cursor = None

        self.start_time = time.time()
        self.penalty_time = 0
        self.game_time = round(time.time() - self.start_time + self.penalty_time)

        self.hints = 5

        self.is_solve_button_used = False
        self.end = False

    def __set_cells(self):
        cells_list = []
        height_start = 142
        height_stop = 190
        pos_0 = 0

        for index in range(9):
            width_start = 17
            width_stop = 65
            pos_1 = 0

            for row_index in range(9):
                box = 0
                if pos_0 < 3:
                    if pos_1 < 3:
                        box = 1
                    elif pos_1 < 6:
                        box = 2
                    elif pos_1 < 9:
                        box = 3
                elif pos_0 < 6:
                    if pos_1 < 3:
                        box = 4
                    elif pos_1 < 6:
                        box = 5
                    elif pos_1 < 9:
                        box = 6
                elif pos_0 < 9:
                    if pos_1 < 3:
                        box = 7
                    elif pos_1 < 6:
                        box = 8
                    elif pos_1 < 9:
                        box = 9
                digit = self.tables.unsolved[index][row_index]
                cell = Cell(width_start, width_stop, height_start, height_stop, digit, (pos_0, pos_1), box,
                            (False if digit != 0 else True))
                cells_list.append(cell)

                if row_index in (2, 5):
                    width_start += 52
                    width_stop += 52
                else:
                    width_start += 48
                    width_stop += 48
                pos_1 += 1
            if index in (2, 5):
                height_start += 52
                height_stop += 52
            else:
                height_start += 48
                height_stop += 48
            pos_0 += 1

        return cells_list

    def __set_buttons(self):
        button_image = pygame.image.load('icon/game_option.png')
        hint_button = surface.ButtonInterface(self.screen, button_image, 465, 140, "Hint", self.hint)
        check_button = surface.ButtonInterface(self.screen, button_image, 465, 205, "Check", self.check)
        clear_button = surface.ButtonInterface(self.screen, button_image, 465, 270, "Clear", self.clear)
        solve_button = surface.ButtonInterface(self.screen, button_image, 465, 335, "Solve", self.solve)
        save_game_button = surface.ButtonInterface(self.screen, button_image, 465, 400, "Save Game", self.save_game)
        exit_game_button = surface.ButtonInterface(self.screen, button_image, 465, 465, "Quit", self.exit_game)
        buttons_list = [hint_button, check_button, clear_button, solve_button, save_game_button, exit_game_button]
        return buttons_list

    def __set_cursor(self, cell):
        if cell.cursor_on_cell(cell, self.__cursor):
            self.__cursor = None
        else:
            line_list = [(cell.x_start, cell.y_start), (cell.x_stop, cell.y_start), (cell.x_stop, cell.y_stop),
                         (cell.x_start, cell.y_stop)]
            self.__cursor = Cursor(self.screen, line_list)

    def draw(self):
        self.draw_background()
        self.__draw_buttons()
        self.__draw_statistics_text()
        self.__draw_grid()
        self.__draw_incorrect()
        if self.__cursor:
            self.__cursor.draw()
        self.__draw_digits()

    def __draw_buttons(self):
        button_font = pygame.font.Font(self.font_path, 20)

        for button in self.__buttons_list:
            button.add()
            mouse_on_button = self.mouse_on_button(button, 135, 62)
            self.add_text_on_button(button, button_font, (c.white if mouse_on_button else c.black),
                                    (button.x_start + 67, button.y_start + 30))

    def __draw_statistics_text(self):
        stats_font = pygame.font.Font(self.font_path, 25)

        self.add_text_on_screen(self.screen, f"Time: {self.format_time(self.game_time)}", stats_font, c.white,
                                (90, 130))
        self.add_text_on_screen(self.screen, f"Hints: {self.hints}", stats_font, c.white, (390, 130))

    def __draw_grid(self):
        # draw white background of grid
        pygame.draw.rect(self.screen, c.white, (15, 142, 444, 444))

        # draw thick lines
        thick_line_y = 140
        thick_line_x = 15
        for i in range(4):
            pygame.draw.line(self.screen, self.color, (15, thick_line_y), (459, thick_line_y), 6)
            pygame.draw.line(self.screen, self.color, (thick_line_x, 140), (thick_line_x, 584), 6)
            thick_line_y += 148
            thick_line_x += 148

        # draw thin lines
        thin_line_y = 142
        thin_line_x = 17
        for i in range(12):
            pygame.draw.line(self.screen, self.color, (17, thin_line_y), (457, thin_line_y), 2)
            pygame.draw.line(self.screen, self.color, (thin_line_x, 142), (thin_line_x, 582), 2)
            if i == 3 or i == 7:
                thin_line_y += 4
                thin_line_x += 4
            else:
                thin_line_y += 48
                thin_line_x += 48

    def __draw_incorrect(self):
        for cell in self.cells_list:
            if cell.incorrect:
                pygame.draw.rect(self.screen, c.red, (cell.x_start, cell.y_start, 48, 48))

    def __draw_digits(self):
        digit_font = pygame.font.Font(self.font_path, 30)
        for cell in self.cells_list:
            if cell.digit > 0:
                self.add_text_on_screen(self.screen, f"{cell.digit}", digit_font,
                                        (c.blue if cell.editable else c.red if cell.hint else c.black),
                                        (cell.x_start+24, cell.y_start+24))

    @staticmethod
    def format_time(tm):
        second = tm % 60
        minute = tm // 60
        if minute < 10 and second < 10:
            time_str = f"0{minute}:0{second}"
        elif minute < 10:
            time_str = f"0{minute}:{second}"
        elif second < 10:
            time_str = f"{minute}:0{second}"
        else:
            time_str = f"{minute}:{second}"
        return time_str

    def check_is_solved(self):
        solved_cells = [cell for cell in self.cells_list if cell.digit == self.tables.solved[cell.pos[0]][cell.pos[1]]]
        if len(solved_cells) == len(self.cells_list):
            self.end = True

    def move_cursor(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        for cell in self.cells_list:
            mouse_on_cell = cell.mouse_on_cell(cell, mouse)
            if mouse_on_cell:
                if click[0] == 1:
                    self.__set_cursor(cell)

    def hint(self):
        if self.hints > 0 and not self.end:
            list_of_cells_for_hint = [cell for cell in self.cells_list if (cell.editable and cell.digit == 0)]
            try:
                if len(list_of_cells_for_hint) > 0:
                    selected_cell = random.choice(list_of_cells_for_hint)
                    selected_cell.digit = self.tables.solved[selected_cell.pos[0]][selected_cell.pos[1]]
                    selected_cell.editable = False
                    selected_cell.hint = True
                    if selected_cell.incorrect:
                        selected_cell.incorrect = False
                else:
                    raise HintError
            except HintError:
                pass

            self.hints -= 1
            self.penalty_time += 15

    def check(self):
        for cell in self.cells_list:
            if cell.digit > 0 and cell.digit != self.tables.solved[cell.pos[0]][cell.pos[1]]:
                cell.incorrect = True
        self.penalty_time += 15

    def clear(self):
        if not self.end:
            for cell in self.cells_list:
                if cell.editable and cell.digit > 0:
                    cell.digit = 0
                    cell.incorrect = False

    def solve(self):
        for cell in self.cells_list:
            if cell.editable:
                cell.digit = self.tables.solved[cell.pos[0]][cell.pos[1]]
                cell.incorrect = False
        self.is_solve_button_used = True

    def save_game(self):
        path = "game_save.txt"
        with open(path, "wb") as file:
            pickle.dump(self.hints, file)
            pickle.dump(self.cells_list, file)
            pickle.dump(self.tables.unsolved, file)
            pickle.dump(self.tables.solved, file)
            pickle.dump(self.game_time, file)

    @staticmethod
    def exit_game():
        menu.run()

    @staticmethod
    def end_game():
        pygame.display.update()
        time.sleep(1)
        menu.run()

    def handle_events(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for button in self.__buttons_list:
                        mouse_is_pressed_on_button = self.mouse_is_pressed_on_button(button, 135, 62)
                        if mouse_is_pressed_on_button:
                            button.action()

                    self.move_cursor()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.exit_game()
                    for cell in self.cells_list:
                        cursor_on_cell = cell.cursor_on_cell(cell, self.__cursor)
                        key_dictionary = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
                                          pygame.K_5: 5, pygame.K_6: 6, pygame.K_7: 7, pygame.K_8: 8,
                                          pygame.K_9: 9}
                        if cursor_on_cell and cell.editable:
                            for key in key_dictionary:
                                if event.key == key:
                                    cell.digit = key_dictionary[key]
                                    if cell.incorrect:
                                        cell.incorrect = False
                            if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                                cell.digit = 0
                                if cell.incorrect:
                                    cell.incorrect = False

            self.draw()
            self.check_is_solved()
            if not self.end:
                self.game_time = round(time.time() - self.start_time + self.penalty_time)
            else:
                self.end_game()

            pygame.display.update()


class LoadedGame(Game):
    def __init__(self, hints, cells_list, unsolved_table, solved_table, saved_game_time):
        super().__init__()
        self.hints = hints
        self.cells_list = cells_list
        self.tables.unsolved = unsolved_table
        self.tables.solved = solved_table
        self.start_time = time.time() - saved_game_time


class Cursor(Painter):
    def __init__(self, surf, line_list):
        self.surf = surf
        self.line_list = line_list

    def draw(self):
        pygame.draw.lines(self.surf, c.red, True, self.line_list)


class SingletonMeta(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Tables(metaclass=SingletonMeta):
    def __init__(self):
        self.level = self.set_level()
        self.solved = self.solved_table()
        if self.level == 1:
            self.number_of_digits_to_change = random.randint(15, 20)
        if self.level == 2:
            self.number_of_digits_to_change = random.randint(30, 35)
        if self.level == 3:
            self.number_of_digits_to_change = random.randint(45, 50)

        self.unsolved = self.unsolved_table()

    @staticmethod
    def set_level():
        path = "settings.txt"
        if os.path.isfile(path):
            file = open(path, "r")
            file_list = [line.strip() for line in file.readlines()]
            level = int(file_list[1])
        else:
            level = 1
        return level

    def solved_table(self):
        finish = False

        while not finish:
            try:
                solved_table = self.solved_table_generator()
                finish = True
                return solved_table
            except IndexError:
                pass

    def solved_table_generator(self):
        table = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0]]

        number_of_0 = 81

        while number_of_0 != 0:
            digits = [i for i in range(1, 10)]
            row = [i for i in range(len(table))]
            col = [i for i in range(len(table[0]))]

            cells_tuples = []
            for i in row:
                for j in col:
                    number_of_possible_digits = self.number_of_possible_digits(table, i, j, digits)
                    if number_of_possible_digits > 0:
                        cells_tuples.append((number_of_possible_digits, i, j))
            cells_tuples.sort()
            x_row = cells_tuples[0][1]
            y_col = cells_tuples[0][2]

            cell_to_change = random.choice(self.possible_digits(table, x_row, y_col, digits))
            table[x_row][y_col] = cell_to_change
            number_of_0 -= 1

        return table

    def possible_digits(self, table, row, col, digits):
        possible_digits = [digit for digit in digits if self.check_is_valid(table, row, col, digit)]
        return possible_digits

    def number_of_possible_digits(self, table, row, col, digits):
        possible_digits = self.possible_digits(table, row, col, digits)
        number_of_possible_digits = len(possible_digits)
        return number_of_possible_digits

    def unsolved_table(self):
        finish = False

        while not finish:
            try:
                unsolved_table = self.unsolved_table_generator()
                finish = True
                return unsolved_table
            except ValueError:
                pass

    def unsolved_table_generator(self):
        attemps = 5
        table = copy.deepcopy(self.solved)
        number_of_digits_to_change = copy.deepcopy(self.number_of_digits_to_change)
        while number_of_digits_to_change != 0:
            row = random.randint(0, 8)
            col = random.randint(0, 8)
            if table[row][col] != 0:
                if self.check_if_only_one_solution(copy.deepcopy(table), row, col):
                    table[row][col] = 0
                    number_of_digits_to_change -= 1
                    attemps = 5
                else:
                    if attemps != 0:
                        attemps -= 1
                        continue
                    else:
                        raise ValueError
            else:
                continue
        return table

    def check_if_only_one_solution(self, table, row, col):
        table[row][col] = 0
        digits = [i for i in range(1, 10)]
        table_row = [i for i in range(len(table))]
        table_col = [i for i in range(len(table[0]))]
        while self.number_of_0(table) > 0:
            cells_tuples = []
            for i in table_row:
                for j in table_col:
                    if table[i][j] == 0:
                        number_of_possible_digits = self.number_of_possible_digits(table, i, j, digits)
                        cells_tuples.append((number_of_possible_digits, i, j))
            cells_tuples.sort()
            if cells_tuples[0][0] == 1:
                x_row = cells_tuples[0][1]
                y_col = cells_tuples[0][2]
                possible_digits = self.possible_digits(table, x_row, y_col, digits)
                table[x_row][y_col] = possible_digits[0]
            if cells_tuples[0][0] > 1:
                return False
        return True

    def number_of_0(self, table):
        number_of_0 = 0
        for row in table:
            for number in row:
                if number == 0:
                    number_of_0 += 1
        return number_of_0

    @staticmethod
    def check_is_valid(table, row, col, digit):
        # define box
        box = []

        # check if the field is not already filled in
        if table[row][col] != 0:
            return False

        # check row
        if digit in table[row]:
            return False

        # check column
        for i in range(len(table)):
            if digit == table[i][col]:
                return False

        # check 9x9 box
        if row < 3:
            if col < 3:
                box = [table[i][0:3] for i in range(0, 3)]
            elif col < 6:
                box = [table[i][3:6] for i in range(0, 3)]
            elif col < 9:
                box = [table[i][6:9] for i in range(0, 3)]
        elif row < 6:
            if col < 3:
                box = [table[i][0:3] for i in range(3, 6)]
            elif col < 6:
                box = [table[i][3:6] for i in range(3, 6)]
            elif col < 9:
                box = [table[i][6:9] for i in range(3, 6)]
        elif row < 9:
            if col < 3:
                box = [table[i][0:3] for i in range(6, 9)]
            elif col < 6:
                box = [table[i][3:6] for i in range(6, 9)]
            elif col < 9:
                box = [table[i][6:9] for i in range(6, 9)]

        for box_row in box:
            if digit in box_row:
                return False

        else:
            return True


class Cell:
    def __init__(self, x_start, x_stop, y_start, y_stop, digit, position, box, editable):
        self.x_start = x_start
        self.x_stop = x_stop
        self.y_start = y_start
        self.y_stop = y_stop
        self.digit = digit
        self.pos = position
        self.box = box
        self.editable = editable
        self.hint = False
        self.incorrect = False

    @staticmethod
    def mouse_on_cell(cell, mouse):
        if cell.x_stop > mouse[0] > cell.x_start and cell.y_stop > mouse[1] > cell.y_start:
            mouse_on_cell = True
        else:
            mouse_on_cell = False
        return mouse_on_cell

    @staticmethod
    def cursor_on_cell(cell, cursor):
        if cursor and cursor.line_list == [(cell.x_start, cell.y_start), (cell.x_stop, cell.y_start),
                                           (cell.x_stop, cell.y_stop), (cell.x_start, cell.y_stop)]:
            cursor_on_cell = True
        else:
            cursor_on_cell = False
        return cursor_on_cell


def run():
    game = Game()
    game.handle_events()
