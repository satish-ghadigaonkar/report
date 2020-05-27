from textwrap import TextWrapper
from itertools import zip_longest
import math

class Cell():
    def __init__(self, *text, width, spacing):
        self.text = text
        self.width = width
        self.spacing = spacing
        self.content_width = len(self.text)

class Column:
    def __init__(self, *rows, max_width=None, min_width=1, spacing=None, wrap=True):
        self.rows = rows

        if max_width is not None:
            self.max_width = max_width
        else:
            self.max_width = math.inf

        if min_width is not None:
            self.min_width = min_width
        else:
            self.min_width = 1

        self.spacing = spacing

        self.max_content_width = self.get_max_content_width()

        if not wrap:
            self.min_width = self.max_content_width

        self.pref_width = self.get_pref_width()
        self.width = self.pref_width

    def get_max_content_width(self):
        try:
            if isinstance(self.rows, str):
                colwidth = len(self.rows)
            else:
                colwidth = max(map(len, self.rows))
        except:
            raise TypeError(self.rows)

        return colwidth

    def get_pref_width(self):
        return min(self.max_width, max(self.max_content_width, self.min_width))


# test = Column(["This is no a test", "This is a test"])
# print(test.pref_width)

class Columns():
    def __init__(self, *columns, linesize, spacing=0):
        self.columns = columns
        self.linesize = linesize
        self.spacing = spacing if spacing is not None else 0

        for column in self.columns:
            column.spacing = column.spacing if column.spacing is not None else self.spacing

    def calculate_width(self):
        tot_used_width = sum([column.width + column.spacing for column in self.columns])

        if tot_used_width < self.linesize:
            remain_width = self.linesize - tot_used_width
            while remain_width > 0 and any(column.width < column.max_width for column in self.columns):
                tot_max_content_width = sum(
                    column.max_content_width for column in self.columns if column.width < column.max_width)
                for i, column in enumerate(self.columns):
                    if column.width < column.max_width:
                        width_ratio = math.ceil(remain_width * (column.max_content_width / tot_max_content_width))
                        column.width = min(column.width + width_ratio
                                           , column.max_width
                                           , column.width + self.linesize - sum(
                                [column.width + column.spacing for column in self.columns])
                                           , self.linesize - column.spacing)

                tot_used_width = sum([column.width + column.spacing for column in self.columns])
                remain_width = self.linesize - tot_used_width

        elif tot_used_width > self.linesize:

            excess_width = tot_used_width - self.linesize
            while excess_width > 0 and any(column.width > column.min_width for column in self.columns):
                tot_max_content_width = sum(
                    column.max_content_width for column in self.columns if column.width > column.min_width)
                wgt_divisor = len([column for column in self.columns if column.width > column.min_width]) - 1
                print(tot_max_content_width)
                for i, column in enumerate(self.columns):
                    if column.width > column.min_width:
                        print(tot_max_content_width, column.max_content_width, wgt_divisor)
                        # if wgt_divisor > 0:
                        #     width_ratio = math.ceil(
                        #         excess_width * ((
                        #                                 tot_max_content_width - column.max_content_width) / tot_max_content_width) / wgt_divisor)
                        # else:
                        #     width_ratio = excess_width
                        width_ratio = math.ceil(excess_width * (column.max_content_width / tot_max_content_width))
                        column.width = min(max(column.width - width_ratio, column.width - excess_width,
                                               column.width + self.linesize - sum(
                                                   [column.width + column.spacing for column in self.columns]),
                                               column.min_width), self.linesize - column.spacing)

                tot_used_width = sum([column.width + column.spacing for column in self.columns])
                excess_width = tot_used_width - self.linesize

        return self

    def split_into_rows(self):
        wrapper = TextWrapper()
        rows = zip_longest(*(colobj.rows for colobj in self.columns))

        split_rows = ()
        for row in rows:
            split_row = ()
            for i, cell in enumerate(row):
                wrapper.width = self.columns[i].width
                cellobj = Cell(*wrapper.wrap(cell), width=self.columns[i].width,
                               spacing=self.columns[i].spacing)

                split_row = split_row + (cellobj,)

            split_rows = split_rows + (split_row,)

        return split_rows

import lorem
col1 = Column(lorem.sentence(), lorem.sentence(), lorem.sentence(), spacing=0)
col2 = Column(lorem.sentence(), lorem.sentence(), lorem.sentence())
col3 = Column(lorem.sentence(), lorem.sentence(), lorem.sentence())

print(col1.rows)

test = Columns(col1, col2, col3, linesize=80, spacing=2)

print(test.calculate_width().split_into_rows())

with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.text', 'w') as fl:
    for row in test.calculate_width().split_into_rows():
        cell_widths = list(cell.width for cell in row)
        cell_spacings = list(cell.spacing for cell in row)
        print(cell_widths)
        for line in zip_longest(*(cellobj.text for cellobj in row)):
            print(line)
            for i, text in enumerate(line):
                if text is not None:
                    fl.write(f"{' '*cell_spacings[i]}{text:<{cell_widths[i]}}")
                else:
                    fl.write(f"{' ' * cell_spacings[i]}{' '*cell_widths[i]}")

            fl.write('\n')
        fl.write('\n')
