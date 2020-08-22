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
                    footnotes = footnotes + (
                        Cell(footer[0], just=footer[1], split=self.split, print_width=self.linesize),)
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
    def __init__(self, columns, page, title=None, footnotes=None, before_header_line=True,
                 after_header_line=True, display_header=True, linechar='\u2014', double_spaced=False):
        self.columns = columns
        self.page = page
        self.display_header = display_header
        self.double_spaced = double_spaced
        self.linechar = linechar

        self.title = Title(title, print_width=self.page.linesize, split=self.columns.split)

        if isinstance(footnotes, (list, tuple)):
            self.footnotes = Footnotes(*footnotes, linesize=self.page.linesize, split=self.columns.split)
        else:
            self.footnotes = Footnotes(footnotes, linesize=self.page.linesize, split=self.columns.split)

        self.before_header_line = before_header_line
        self.after_header_line = after_header_line

        self.line = self.linechar * self.page.linesize

    def get_fixed_lines(self, pageindex):
        # A line before table start, a line before footnote is always printed, so the
        # constant 2 is added
        fixed_lines = self.title.max_lines + (
                self.title.max_lines > 0) * 1 + self.footnotes.max_lines + 2

        if self.display_header:
            fixed_lines = fixed_lines + self.columns.get_header_row(pageindex).max_lines

            if self.after_header_line:
                fixed_lines += 1

        return fixed_lines

    def print_header(self, header, file):
        if self.before_header_line:
            file.write(self.line)
            file.write('\n')

        header.write(file, align_bottom=True)

        if self.after_header_line:
            file.write(self.line)
            file.write('\n')

    def print_page(self, header, rowgroups, file):
        self.title.write(file)

        if self.display_header:
            self.print_header(header, file)
        else:
            file.write(self.line + '\n')

        for rowgroup in rowgroups:
            rowgroup.rowlabel.write(file)
            if self.double_spaced:
                file.write('\n')

            for row in rowgroup.rows:
                row.write(file)
                if self.double_spaced:
                    file.write('\n')

        file.write(self.line + '\n')
        self.footnotes.write(file)

    def print_table(self, file):
        self.columns.calculate_width(self.page.linesize)
        print(self.columns.pages)
        for i in self.columns.pages:
            self.columns.set_cell_width(self.columns.width[i])
            remaining_lines = self.page.pagesize - self.get_fixed_lines(i)
            rowgroups_to_print = tuple()

            for rowgroup in self.columns.getrowgroup(*self.columns.pages[i], width=self.columns.width[i], spacing=self.columns.spacing):
                if remaining_lines >= rowgroup.max_lines + (1 if self.double_spaced else 0):
                    rowgroups_to_print = rowgroups_to_print + (rowgroup,)
                    remaining_lines = remaining_lines - rowgroup.max_lines
                else:
                    self.print_page(self.columns.get_header_row(i), rowgroups_to_print, file)
                    file.write("\u000C")
                    rowgroup.rowlabel.print_index = 0
                    rowgroups_to_print = (rowgroup,)
                    remaining_lines = self.page.pagesize - self.get_fixed_lines(i) - rowgroup.max_lines

                if self.double_spaced:
                    remaining_lines = remaining_lines - 1

            self.print_page(self.columns.get_header_row(i), rowgroups_to_print, file)


# import lorem
# 
# col1 = Column(*(Cell(f'{i:0}') for i in range(50000)), wrap=False, wrap_header=False, label='Colu~mn 1', spacing=0, just='>')
# col2 = Column(*(Cell(lorem.sentence()) for i in range(50000)), Cell('efg'), Cell('abc'),label='Column 2', min_width=30)
# col3 = Column(*(Cell(lorem.sentence()) for i in range(50000)), Cell('This is a test'), Cell('This is a test'), label='Column 3', min_width=20)
# col4 = Column(*(Cell(lorem.sentence()) for i in range(50000)),label='Column 4', min_width=20)
# 
# from datetime import datetime
# print(datetime.now().strftime("%d%b%Y %H:%M:%S.%f").upper())
# page = Page(121, 50)
# with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.txt', 'w') as fl:
#     table = Table(col1, col2, col3, col4, page=page, file=fl, spacing=1, display_header=True,
#                   orderby=(col2, col3, col4),
#                   title='This is a title',
#                   footnotes=["This is a footnote",(datetime.now().strftime("%d%b%Y:%H:%M:%S").upper(),'>')],
#                   split='~', double_spaced=False)
#     table.print_table()
# 
# print(datetime.now().strftime("%d%b%Y %H:%M:%S.%f").upper())

# import lorem
#
# testcells = ()
# for column in range(4):
#     for row in range(10):
#         testcells = testcells + (Cell(lorem.sentence(), colindex=column, rowindex=row),)
#
# page = Page(145, 50)
#
# table = Table(Columns(*testcells, colorder=range(4), linesize=145, wrap=True, minwidth=10, spacing=1,
#                       label=('Column 0', 'Column 1', 'Column 2', 'Column 3'), just='^').calculate_width(), page,
#               title='This is a title',
#               footnotes=["This is a footnote", (datetime.now().strftime("%d%b%Y:%H:%M:%S").upper(), '>')],)
#
# print(table.columns.spacing)
#
# with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.txt', 'w') as fl:
#     table.print_table(fl)