from src.Column import *

class Table:
    def __init__(self, *columns, title, footnote, pagesize, linesize):
        self.columns = Columns(columns)
        self.linesize = linesize
        self.pagesize = pagesize

        self.title = Cell(title)
        self.title.print_width = self.linesize

        self.footnote = Cell(footnote)
        self.footnote.print_width = self.linesize
