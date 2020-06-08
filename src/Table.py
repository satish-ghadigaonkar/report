from src.Column import *


class Page:
    def __init__(self, linesize, pagesize):
        self.pagesize = pagesize
        self.linesize = linesize

class Title(Cell):
    def write(self, file):
        if self.content_width > 0:
            super().write(file)
            file.write('\n')


class Footnotes():
    def __init__(self, *footnotes, split=None, linesize=None):
        self.split = split
        self.linesize = linesize
        self._footnotes = footnotes

    @property
    def footnotes(self):
        footnotes = tuple()
        if self._footnotes is None or isinstance(self._footnotes, str):
            footnotes = footnotes + (Cell(footnotes, split=self.split, print_width=self.linesize),)
        else:
            for footer in self._footnotes:
                if isinstance(footer, (list, tuple)):
                    footnotes = footnotes + (Cell(footer[0], just=footer[1], split=self.split, print_width=self.linesize),)
                else:
                    footnotes = footnotes + (Cell(footer, split=self.split, print_width=self.linesize),)

        return footnotes

    @footnotes.setter
    def footnotes(self, new_footnotes):
        self._footnotes = new_footnotes

    def __repr__(self):
        return self.footnotes.__repr__()

    @property
    def max_lines(self):
        return sum(footer.max_lines for footer in self.footnotes)

    def write(self, file):
        for footer in self.footnotes:
            footer.write(file)

class Table:
    def __init__(self, *columns, orderby=None, page, file, title=None, footnotes=None, spacing=0, split='~', before_header_line=True,
                 after_header_line=True, display_header=True, linechar='\u2014', double_spaced=False):
        self.orderby = orderby
        self.spacing = spacing
        self.split = split
        self.file = file
        self.page = page
        self.display_header = display_header
        self.double_spaced = double_spaced
        self.linechar = linechar

        self.columns = Columns(*columns, orderby=self.orderby, linesize=self.page.linesize, spacing=self.spacing, split=self.split).calculate_width().sort()
        self.title = Title(title, split=self.split, print_width=self.page.linesize)

        if isinstance(footnotes,(list, tuple)):
            self.footnotes = Footnotes(*footnotes, split=self.split, linesize=self.page.linesize)
        else:
            self.footnotes = Footnotes(footnotes, split=self.split, linesize=self.page.linesize)

        self.before_header_line = before_header_line
        self.after_header_line = after_header_line


        self.header = self.columns.get_header_row()
        self.line = self.linechar * self.page.linesize


    def get_fixed_lines(self):
        # A line before table start, a line before footnote is always printed, so the
        # constant 2 is added
        fixed_lines = self.title.max_lines + (
                    self.title.max_lines > 0) * 1 + self.footnotes.max_lines + 2

        if self.display_header:
            fixed_lines = fixed_lines + self.columns.get_header_row().max_lines

            if self.after_header_line:
                fixed_lines += 1

        return fixed_lines

    def print_header(self, header):
        if self.before_header_line:
            self.file.write(self.line)
            self.file.write('\n')

        header.write(self.file)

        if self.after_header_line:
            self.file.write(self.line)
            self.file.write('\n')

    def print_page(self, header, rows):
        self.title.write(self.file)

        if self.display_header:
            self.print_header(header)
        else:
            self.file.write(self.line + '\n')

        for row in rows:
            row.write(self.file)
            if self.double_spaced:
                self.file.write('\n')

        self.file.write(self.line + '\n')
        self.footnotes.write(self.file)

    def print_table(self):
        for columns in table.columns.columns_by_page:
            remaining_lines = self.page.pagesize - self.get_fixed_lines()
            rows_to_print = tuple()
            for row in columns.get_rows():
                if remaining_lines >= row.max_lines + (1 if self.double_spaced else 0):
                    rows_to_print = rows_to_print + (row,)
                    remaining_lines = remaining_lines - row.max_lines
                else:
                    self.print_page(columns.get_header_row(), rows_to_print)
                    self.file.write("\u000C")
                    rows_to_print = (row,)
                    remaining_lines = self.page.pagesize - self.get_fixed_lines() - row.max_lines

                if self.double_spaced:
                    remaining_lines = remaining_lines - 1

            self.print_page(columns.get_header_row(), rows_to_print)

import lorem

col1 = Column(*(Cell(f'{i:0}') for i in range(50000)), wrap=False, wrap_header=False, label='Colu~mn 1', spacing=0, just='>')
col2 = Column(*(Cell(lorem.sentence()) for i in range(50000)), Cell('efg'), Cell('abc'),label='Column 2', min_width=30)
col3 = Column(*(Cell(lorem.sentence()) for i in range(50000)), Cell('This is a test'), Cell('This is a test'), label='Column 3', min_width=20)
col4 = Column(*(Cell(lorem.sentence()) for i in range(50000)),label='Column 4', min_width=20)

from datetime import datetime
print(datetime.now().strftime("%d%b%Y %H:%M:%S.%f").upper())
page = Page(121, 50)
with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.txt', 'w') as fl:
    table = Table(col1, col2, col3, col4, page=page, file=fl, spacing=1, display_header=True,
                  orderby=(col2, col3, col4),
                  title='This is a title',
                  footnotes=["This is a footnote",(datetime.now().strftime("%d%b%Y:%H:%M:%S").upper(),'>')],
                  split='~', double_spaced=False)
    table.print_table()

print(datetime.now().strftime("%d%b%Y %H:%M:%S.%f").upper())