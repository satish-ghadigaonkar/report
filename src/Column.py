from textwrap import TextWrapper
from itertools import zip_longest
import math
from operator import itemgetter
from statistics import mean, median
from sys import stdout
from datetime import datetime


class Cell():
    def __init__(self, value, spacing=None, just=None, split=None, print_width=None, noprint=False):
        self.value = value

        if self.value is None:
            self.text = ''
        elif isinstance(value, str):
            self.text = self.value
        else:
            self.text = str(self.value)

        self.spacing = spacing
        self.just = just if just is not None else '<'
        self.split = split
        self.noprint = noprint if noprint is not None else False
        self._print_width = print_width

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        if self.value is None and other.value is None:
            return True
        elif self.value is None or other.value is None:
            return False
        else:
            return self.value == other.value

    def __lt__(self, other):
        if self.value is None and other.value is None:
            return False
        elif self.value is None:
            return True
        else:
            if other.value is None:
                return False
            else:
                return self.value < other.value

    def __gt__(self, other):
        if self.value is None and other.value is None:
            return False
        elif self.value is None:
            return False
        else:
            if other.value is None:
                return True
            else:
                return self.value > other.value

    def __mul__(self, other):
        return tuple(self for i in range(other))

    @property
    def content_width(self):
        if self.split is None:
            return len(self.text)
        else:
            return max(len(part) for part in self.text.split(self.split))

    @property
    def print_width(self):
        return self._print_width if self._print_width is not None else self.content_width

    @print_width.setter
    def print_width(self, new_print_width):
        self._print_width = new_print_width

    @property
    def wrapped_text(self):
        wrapper = TextWrapper(width=self.print_width)

        if self.text.isspace():
            wrapped_text = [' ']
        elif self.split is None:
            wrapped_text = wrapper.wrap(self.text)
        else:
            parts = self.text.split(self.split)
            wrapped_text = []
            for part in parts:
                wrapped_text = wrapped_text + wrapper.wrap(part)

        return wrapped_text

    @property
    def max_lines(self):
        return len(self.wrapped_text)

    def write_line(self, lineno, file):
        spacing = self.spacing if self.spacing is not None else 0
        wrapped_text = self.wrapped_text

        if lineno < len(wrapped_text):
            text = wrapped_text[lineno]
            file.write(f"{' ' * spacing}{text:{self.just}{self.print_width}}")
        else:
            file.write(f"{' ' * spacing}{' ' * self.print_width}")

    def write(self, file):
        for i in range(self.max_lines):
            self.write_line(i, file)
            file.write('\n')


class Column:
    def __init__(self, *cells, label=None, max_width=None, min_width=1, spacing=None, wrap=True, wrap_header=True,
                 just=None, split=None):
        self.cells = cells
        self.max_width = max_width if max_width is not None else math.inf
        self.min_width = min_width if min_width is not None else 1
        self.wrap = wrap
        self.wrap_header = wrap_header
        self.label = label
        self.set_spacing(spacing)
        self.set_just(just)
        self.set_split(split)
        self.set_width(min(self.max_width, max(self.max_content_width, self.pref_min_width)))

    def __repr__(self):
        return self.cells.__repr__()

    def __getitem__(self, index: int):
        return self.cells[index]

    @property
    def max_content_width(self):
        return max(cell.content_width for cell in self.cells)

    @property
    def pref_min_width(self):
        if not self.wrap:
            if not self.wrap_header:
                return max(self.min_width, self.max_content_width,
                           *(len(string) for string in self.label.split(self.split)))
            else:
                return max(self.min_width, self.max_content_width)
        else:
            if not self.wrap_header:
                return max(self.min_width, *(len(string) for string in self.label.split(self.split)))
            else:
                return self.min_width

    @property
    def pref_width(self):
        return min(self.max_width, max(self.max_content_width, self.pref_min_width))

    def set_spacing(self, spacing):
        self.spacing = spacing

        for cell in self.cells:
            cell.spacing = spacing

    def set_width(self, width):
        self.width = width

        for cell in self.cells:
            cell.print_width = width

    def set_just(self, just):
        self.just = just if just is not None else '<'

        for cell in self.cells:
            cell.just = self.just

    def set_split(self, split):
        self.split = split

        for cell in self.cells:
            cell.split = self.split

    def append_cells(self, *new_cells):
        self.cells = self.cells + new_cells
        self.set_spacing(self.spacing)
        self.set_just(self.just)
        self.set_split(self.split)

        return self

    def sort(self, reverse=False):
        self.cells = sorted(self.cells, reverse=reverse)
        return self


# test = Column(["This is no a test", "This is a test"])
# print(test.pref_width)

class Columns():
    def __init__(self, *columns, linesize, spacing=0, orderby=None, split='~'):
        self.columns = self.align_column_length(*columns)
        self.linesize = linesize
        self.orderby = orderby
        self.spacing = spacing if spacing is not None else 0
        self.split = split if split is not None else '~'
        self.columns_by_page = []

        for column in self.columns:
            if column.spacing is None:
                column.set_spacing(self.spacing)

            if column.split is None:
                column.set_split(self.split)

    def align_column_length(self, *columns):
        no_of_rows = max(len(column.cells) for column in columns)
        result = ()

        for column in columns:
            if len(column.cells) < no_of_rows:
                column = column.append_cells(*(Cell(None) * (no_of_rows - len(column.cells))))

            result = result + (column,)

        return result

    def sort(self, reverse=False):
        if self.orderby is not None:
            sortindex = (index for index in (self.columns.index(column) for column in self.orderby))
            rows = (row for row in zip(*(column.cells for column in self.columns)))

            for i, cells in enumerate(
                    zip(*(row for row in sorted(rows, key=itemgetter(*sortindex), reverse=reverse)))):
                self.columns[i].cells = cells

        return self
        # sorted(*(row for row in zip(*(column.cells for column in self.columns))), key=)

    def recurse(self, cols):
        for columns in cols:
            tot_used_width = sum([column.width + column.spacing for column in columns])

            if tot_used_width < self.linesize:
                remain_width = self.linesize - tot_used_width
                while remain_width > 0 and any(column.width < column.max_width for column in columns):
                    tot_max_content_width = sum(
                        column.max_content_width for column in columns if column.width < column.max_width)
                    for i, column in enumerate(columns):
                        if column.width < column.max_width:
                            width_ratio = math.ceil(remain_width * (column.max_content_width / tot_max_content_width))
                            column.set_width(min(column.width + width_ratio
                                                 , column.max_width
                                                 , column.pref_width if any(
                                    column.width < column.pref_width for column in columns) else column.max_width
                                                 , column.width + self.linesize - sum(
                                    [column.width + column.spacing for column in columns])
                                                 , self.linesize - column.spacing))

                    tot_used_width = sum([column.width + column.spacing for column in columns])
                    remain_width = self.linesize - tot_used_width

                self.columns_by_page.append(Columns(*columns, linesize=self.linesize, spacing=self.spacing))
            elif tot_used_width > self.linesize:

                excess_width = tot_used_width - self.linesize
                while excess_width > 0 and any(column.width > column.pref_min_width for column in columns):
                    tot_max_content_width = sum(
                        column.max_content_width for column in columns if column.width > column.pref_min_width)
                    wgt_divisor = len([column for column in columns if column.width > column.pref_min_width]) - 1
                    for i, column in enumerate(columns):
                        if column.width > column.pref_min_width:
                            # print(tot_max_content_width, column.max_content_width, wgt_divisor)
                            # if wgt_divisor > 0:
                            #     width_ratio = math.ceil(
                            #         excess_width * ((
                            #                                 tot_max_content_width - column.max_content_width) / tot_max_content_width) / wgt_divisor)
                            # else:
                            #     width_ratio = excess_width
                            width_ratio = math.ceil(excess_width * (column.max_content_width / tot_max_content_width))
                            column.set_width(min(max(column.width - width_ratio, column.width - excess_width,
                                                     column.width + self.linesize - sum(
                                                         [column.width + column.spacing for column in columns]),
                                                     column.pref_min_width, column.pref_width if any(
                                    column.width > column.pref_width for column in columns) else column.pref_min_width),
                                                 self.linesize - column.spacing))

                    tot_used_width = sum([column.width + column.spacing for column in columns])
                    excess_width = tot_used_width - self.linesize

                if excess_width > 0:
                    cols1 = columns
                    cols2 = tuple()

                    while excess_width > 0:
                        cols2 = (cols1[-1],) + cols2
                        cols1 = cols1[:-1]
                        tot_used_width = sum([column.width + column.spacing for column in cols1])
                        excess_width = tot_used_width - self.linesize
                    self.recurse([cols1, cols2])
                else:
                    self.columns_by_page.append(Columns(*columns, linesize=self.linesize, spacing=self.spacing))
            else:
                self.columns_by_page.append(Columns(*columns, linesize=self.linesize, spacing=self.spacing))
        return

    def calculate_width(self):
        self.recurse([self.columns])
        return self

    def get_rows(self):
        return (Row(*row) for row in zip(*(column.cells for column in self.columns)))

    def get_header_row(self):
        header = tuple()
        for column in self.columns:
            label = Cell(column.label, column.spacing, column.just, column.split)
            label.print_width = column.width
            header = header + (label,)

        return Row(*header)


class Row():
    def __init__(self, *cells):
        self.cells = cells

    @property
    def max_lines(self):
        return max(cell.max_lines for cell in self.cells)

    def __repr__(self):
        return self.cells.__repr__()

    def write(self, file):
        for i in range(self.max_lines):
            for cell in self.cells:
                cell.write_line(i, file)

            file.write('\n')

# class GroupBy():
#     def __init__(self, *columns):
#         self.columns =  columns
#
#     def groupby(self):
