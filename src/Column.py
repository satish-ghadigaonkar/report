from textwrap import TextWrapper
from itertools import zip_longest
import math

class Cell():
    def __init__(self, text, spacing=None, just=None, split=None):
        self.text = text if text is not None else ''
        #self.text = text
        self.spacing = spacing
        self.split = split

        if split is None:
            self.content_width = len(self.text)
        else:
            self.content_width = max(len(part) for part in self.text.split(self.split))

        self.print_width = self.content_width
        self.just = just if just is not None else '<'

    def get_wrapped_text(self):
        wrapper = TextWrapper(width=self.print_width,drop_whitespace=True)

        if self.split is None:
            wrapped_text = wrapper.wrap(self.text)
        else:
            parts = self.text.split(self.split)
            wrapped_text = []
            for part in parts:
                wrapped_text = wrapped_text + wrapper.wrap(part)

        return wrapped_text

    def get_max_lines(self):
        return len(self.get_wrapped_text())

    def print_cell_line(self, lineno, file):
        spacing = self.spacing if self.spacing is not None else 0
        wrapped_text = self.get_wrapped_text()
        if lineno < len(wrapped_text):
            text = wrapped_text[lineno]
            file.write(f"{' ' * spacing}{text:{self.just}{self.print_width}}")
        else:
            file.write(f"{' ' * spacing}{' ' * self.print_width}")

    def print_cell(self, file):
        for i in range(self.get_max_lines()):
            self.print_cell_line(i, file)
            file.write('\n')


class Column:
    def __init__(self, *cells, label=None, max_width=None, min_width=1, spacing=None, wrap=True, just=None, split=None):
        self.cells = cells
        self.max_width = max_width if max_width is not None else math.inf
        self.min_width = min_width if min_width is not None else 1
        self.max_content_width = self.get_max_content_width()
        self.wrap = wrap
        self.split=split

        if not self.wrap:
            self.min_width = self.max_content_width

        self.pref_width = self.get_pref_width()
        self.set_width(self.pref_width)
        self.set_spacing(spacing)
        self.set_just(just)
        self.set_split(split)

        self.label=label

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
            cell.split = split

    def get_max_content_width(self):
        return max(cell.content_width for cell in self.cells)

    def get_pref_width(self):
        return min(self.max_width, max(self.max_content_width, self.min_width))

    def append_cell(self, new_cell):
        self.cells = self.cells + (new_cell,)
        self.max_content_width = self.get_max_content_width()

        if not self.wrap:
            self.min_width = self.max_content_width

        self.pref_width = self.get_pref_width()
        self.set_width(self.pref_width)
        self.set_spacing(self.spacing)
        self.set_just(self.just)

        return self

# test = Column(["This is no a test", "This is a test"])
# print(test.pref_width)

class Columns():
    def __init__(self, *columns, linesize, spacing=0, groupby=None):
        self.columns = columns
        self.linesize = linesize
        self.groupby = groupby
        self.spacing = spacing if spacing is not None else 0

        for column in self.columns:
            if column.spacing is None:
                column.set_spacing(self.spacing)

    def align_column_length(self):
        no_of_rows = max(len(column.cells) for column in self.columns)

        for column in self.columns:
            #print(f'Here {len(column.cells)}')
            while len(column.cells) < no_of_rows:
                column.append_cell(Cell(None))

        return self

    def calculate_width(self):
        self.align_column_length()
        tot_used_width = sum([column.width + column.spacing for column in self.columns])

        if tot_used_width < self.linesize:
            remain_width = self.linesize - tot_used_width
            while remain_width > 0 and any(column.width < column.max_width for column in self.columns):
                tot_max_content_width = sum(
                    column.max_content_width for column in self.columns if column.width < column.max_width)
                for i, column in enumerate(self.columns):
                    if column.width < column.max_width:
                        width_ratio = math.ceil(remain_width * (column.max_content_width / tot_max_content_width))
                        column.set_width(min(column.width + width_ratio
                                             , column.max_width
                                             , column.width + self.linesize - sum(
                                [column.width + column.spacing for column in self.columns])
                                             , self.linesize - column.spacing))

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
                                                     [column.width + column.spacing for column in self.columns]),
                                                 column.min_width), self.linesize - column.spacing))

                tot_used_width = sum([column.width + column.spacing for column in self.columns])
                excess_width = tot_used_width - self.linesize

        return self

    def get_rows(self):
        return (Row(*row) for row in zip_longest(*(column.cells for column in self.columns)))

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
        self.max_lines = max(cell.get_max_lines() for cell in self.cells)

    def print_row(self, file):
        for i in range(self.max_lines):
            for cell in self.cells:
                cell.print_cell_line(i, file)

            file.write('\n')


# import lorem
#
# col1 = Column(Cell(lorem.sentence()), Cell(lorem.sentence()), Cell(lorem.sentence()), Cell(lorem.sentence()), spacing=0, label='column1')
# col2 = Column(Cell(lorem.sentence()), Cell(None), Cell(lorem.sentence()), label='column2')
# col3 = Column(Cell(lorem.sentence()), Cell(None), Cell(None), Cell(lorem.sentence()), label='column3')
# col4 = Column(Cell(lorem.sentence()), Cell(lorem.sentence()), Cell(lorem.sentence()), Cell(lorem.sentence()))
#
# test = Columns(col1, col2, col3, col4, linesize=121, spacing=2)
#
# with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.text', 'w') as fl:
#     for row in test.calculate_width().get_rows():
#         row.print_row(fl)
#         fl.write('\n')

# title = Cell("This is very long§text", split='§', just='^')
#
# with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.text', 'w') as fl:
#     title.print_cell(fl)
