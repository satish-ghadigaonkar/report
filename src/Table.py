from src.Column import *


class Page:
    def __init__(self, linesize, pagesize):
        self.pagesize = pagesize
        self.linesize = linesize


class Table:
    def __init__(self, *columns, page, file, title=None, footnote=None, spacing=0, before_header_line=True,
                 after_header_line=True, display_header=True, linechar='\u2014'):
        self.spacing = spacing
        self.columns = Columns(*columns, linesize=page.linesize, spacing=self.spacing).calculate_width()

        self.title = Cell(title)
        self.title.print_width = page.linesize

        self.footnote = Cell(footnote)
        self.footnote.print_width = page.linesize

        self.before_header_line = before_header_line
        self.after_header_line = after_header_line

        self.file = file
        self.page = page
        self.header = self.columns.get_header_row()
        self.linechar = linechar
        self.line = self.linechar * self.page.linesize
        self.display_header = display_header

    def get_fixed_lines(self):
        # A line before table start, a line before footnote is always printed, so the
        # constant 2 is added
        fixed_lines = self.title.get_max_lines() + (
                    self.title.get_max_lines() > 0) * 1 + self.footnote.get_max_lines() + 2

        if self.display_header:
            fixed_lines = fixed_lines + self.columns.get_header_row().max_lines

            if self.after_header_line:
                fixed_lines += 1

        return fixed_lines

    def print_header(self, header):
        if self.before_header_line:
            self.file.write(self.line)
            self.file.write('\n')

        header.print_row(self.file)

        if self.after_header_line:
            self.file.write(self.line)
            self.file.write('\n')

    def print_title(self):
        if self.title.content_width > 0:
            self.title.print_cell(self.file)
            self.file.write('\n')

    def print_footer(self):
        if self.footnote.content_width > 0:
            self.footnote.print_cell(self.file)

    def print_page(self, header, rows):
        self.print_title()

        if self.display_header:
            self.print_header(header)
        else:
            self.file.write(self.line + '\n')

        for row in rows:
            row.print_row(self.file)

        self.file.write(self.line + '\n')
        self.print_footer()

    def print_table(self):
        for columns in table.columns.columns_by_page:
            remaining_lines = self.page.pagesize - self.get_fixed_lines()
            rows_to_print = tuple()
            for row in columns.get_rows():
                if remaining_lines >= row.max_lines:
                    rows_to_print = rows_to_print + (row,)
                    remaining_lines = remaining_lines - row.max_lines
                else:
                    self.print_page(columns.get_header_row(), rows_to_print)
                    self.file.write("\u000C")
                    remaining_lines = self.page.pagesize - self.get_fixed_lines() - row.max_lines
                    rows_to_print = (row,)

            self.print_page(columns.get_header_row(), rows_to_print)


import lorem

col1 = Column(*(Cell(f'{i:0}') for i in range(100)), spacing=0, label=None, split='~',wrap=False, just='<')
col2 = Column(*(Cell(lorem.sentence()) for i in range(100)), Cell(None), Cell('Where is this?'), label='Column 2', min_width=60)
col3 = Column(*(Cell(lorem.sentence()) for i in range(100)), Cell(None), Cell(lorem.sentence()), label='Column 3', min_width=30)
col4 = Column(*(Cell(lorem.sentence()) for i in range(100)), label='Column 4', min_width=30)

page = Page(121, 56)
with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.text', 'w') as fl:
    table = Table(col1, col2, col3, col4, page=page, file=fl, spacing=1, display_header=True,
                  title=None,
                  footnote="Footnote")
    table.print_table()
