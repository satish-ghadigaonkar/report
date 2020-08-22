from textwrap import TextWrapper
from itertools import zip_longest
import math
from operator import attrgetter
from statistics import mean, median
from sys import stdout
from datetime import datetime


class Cell():
    def __init__(self, value, colindex=None, rowindex=None, spacing=None, just=None, split=None,
                 print_width=None, noprint=False, label=None, initial_indent=''):
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
        self.colindex = colindex
        self.rowindex = rowindex
        self.label = label
        self.initial_indent = initial_indent

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        if self.value == other.value and self.rowindex == other.rowindex and self.colindex == other.colindex:
            return True
        else:
            return False

    def __lt__(self, other):
        if self.rowindex < other.rowindex:
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.value, self.rowindex, self.colindex))

    def __mul__(self, other):
        return tuple(self for i in range(other))

    @property
    def content_width(self):
        if self.split is None:
            return len(self.initial_indent + self.text)
        else:
            return max(len(part) for part in (self.initial_indent + self.text).split(self.split))

    @property
    def print_width(self):
        return self._print_width if self._print_width is not None else self.content_width

    @print_width.setter
    def print_width(self, new_print_width):
        self._print_width = new_print_width

    @property
    def wrapped_text(self):
        wrapper = TextWrapper(width=self.print_width, initial_indent=self.initial_indent)

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

        if 0<= lineno < len(wrapped_text):
            text = wrapped_text[lineno]
            file.write(f"{' ' * spacing}{text:{self.just}{self.print_width}}")
        else:
            file.write(f"{' ' * spacing}{' ' * self.print_width}")

    def write(self, file):
        for i in range(self.max_lines):
            self.write_line(i, file)
            file.write('\n')


# test = Column(["This is no a test", "This is a test"])
# print(test.pref_width)

class Cells:
    def __init__(self, *cells):
        self.cells = cells
        self.table = self._tabulate()

    def _tabulate(self):
        table = {}
        for cell in self.cells:
            if cell.colindex in table:
                table[cell.colindex][cell.rowindex] = table[cell.colindex].get(cell.rowindex, tuple()) + (cell,)
            else:
                table[cell.colindex] = {}
                table[cell.colindex][cell.rowindex] = (cell,)

        return table

    def set_cell_width(self, width):
        for cell in self.cells:
            if cell.colindex in width:
                cell.print_width = width[cell.colindex]

        return self

    def _sortedrowindices(self):
        return sorted(tuple(set(cell.rowindex for cell in self.cells)))

    def _getrow(self, rowindex, *colindices, width, spacing):
        row = ()
        for colindex in colindices:
            row = row + self.table[colindex].get(rowindex, (Cell(None, print_width=width[colindex], spacing=spacing[colindex]),))

        return Row(*row)

    def _getrowlabels(self, row):
        labels = tuple()
        for cell in row.cells:
            if cell.label is not None:
                for i, label in enumerate(cell.label):
                    if i < len(labels) and label != labels[i]:
                        labels = labels + (label,)
                    elif i >= len(labels):
                        labels = labels + (label,)

        return labels

    def _make_rowlabel(self, previous_row_label, current_row_label):
        j = 0
        for i in range(len(current_row_label)):
            if i < len(previous_row_label):
                if current_row_label[i] != previous_row_label[i]:
                    j = i
                    break

        return j

    def getrowgroup(self, *colindices, width, spacing):
        for i, rowindex in enumerate(self._sortedrowindices()):
            current_row = self._getrow(rowindex, *colindices, width=width, spacing=spacing)
            current_row_label = self._getrowlabels(current_row)

            if i == 0:
                differ_at = 0
                rows = (current_row,)
                previous_row_label = current_row_label
            else:
                if previous_row_label == current_row_label:
                    rows = rows + (current_row,)
                else:
                    yield RowGroup(*rows, rowlabel=RowLabel(*previous_row_label, print_index=differ_at))
                    differ_at = self._make_rowlabel(previous_row_label, current_row_label)
                    rows = (current_row,)
                    previous_row_label = current_row_label

        yield RowGroup(*rows, rowlabel=RowLabel(*previous_row_label, print_index=differ_at))


class Columns(Cells):
    def __init__(self, *cells, colorder=tuple(), idcols=tuple(), maxwidth=math.inf, minwidth=1, spacing=0, split='~',
                 wrap=True,
                 wrap_header=True, orderby=None, label=None, just='<', header_just=None):
        Cells.__init__(self, *cells)
        self._columns = self.columns = self.cells
        self._rows = self.rows = self.cells
        self.colorder = colorder
        self.idcols = idcols
        self._maxwidth = self.maxwidth = maxwidth
        self._minwidth = self.minwidth = minwidth
        self._spacing = self.spacing = spacing
        self._wrap = self.wrap = wrap
        self._wrap_header = self.wrap_header = wrap_header
        self._label = self.label = label
        self._just = self.just = just
        self._header_just = self.header_just = header_just
        self.split = split if split is not None else '~'
        self.pages = {0: self.colorder}

        for cell in self.cells:
            cell.spacing = self.spacing.get(cell.colindex, 0)
            cell.just = self.just.get(cell.colindex, '<')
            cell.split = self.split

        self.width = {0: {}}
        for column in self.colorder:
            self.width[0][column] = self.get_pref_width(column)

    def set_width(self, pageindex, column, value):
        self.width[pageindex][column] = value

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, cells):
        self._columns = {}
        for cell in cells:
            if cell.colindex in self._columns:
                self._columns[cell.colindex] = self._columns[cell.colindex] + (cell,)
            else:
                self._columns[cell.colindex] = (cell,)

    def set_property(self, value, default):
        if isinstance(value, dict):
            prop = value
            for column in self.colorder:
                if column not in prop:
                    prop[column] = default
                elif prop[column] is None:
                    prop[column] = default
        elif isinstance(value, (list, tuple)):
            prop = {}
            for i, column in enumerate(self.colorder):
                if value[i] is not None:
                    prop[column] = value[i]
                else:
                    prop[column] = default
        else:
            prop = {}
            if value is not None:
                for column in self.colorder:
                    prop[column] = value
            else:
                for column in self.colorder:
                    prop[column] = default

        return prop

    @property
    def maxwidth(self):
        return self._maxwidth

    @maxwidth.setter
    def maxwidth(self, value):
        self._maxwidth = self.set_property(value, math.inf)

    @property
    def minwidth(self):
        return self._minwidth

    @minwidth.setter
    def minwidth(self, value):
        self._minwidth = self.set_property(value, 1)

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = self.set_property(value, 0)

    @property
    def wrap(self):
        return self._wrap

    @wrap.setter
    def wrap(self, value):
        self._wrap = self.set_property(value, True)

    @property
    def wrap_header(self):
        return self._wrap_header

    @wrap_header.setter
    def wrap_header(self, value):
        self._wrap_header = self.set_property(value, True)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = self.set_property(value, '')

    @property
    def just(self):
        return self._just

    @just.setter
    def just(self, value):
        self._just = self.set_property(value, '<')

    @property
    def header_just(self):
        return self._header_just

    @header_just.setter
    def header_just(self, value):
        if isinstance(value, dict):
            self._header_just = value
            for column in self.colorder:
                if column not in self._header_just:
                    self._header_just[column] = self.just[column]
                elif self._header_just[column] is None:
                    self._header_just[column] = self.just[column]
        elif isinstance(value, (list, tuple)):
            self._header_just = {}
            for i, column in enumerate(self.colorder):
                if value[i] is not None:
                    self._header_just[column] = value[i]
                else:
                    self._header_just[column] = self.just[column]
        else:
            self._header_just = {}
            if value is not None:
                for column in self.colorder:
                    self._header_just[column] = value
            else:
                for column in self.colorder:
                    self._header_just[column] = self.just[column]

    def get_max_content_width(self, column):
        return max(cell.content_width for cell in self.columns[column])

    def get_avg_content_width(self, column):
        return mean(cell.content_width for cell in self.columns[column])

    def get_pref_min_width(self, column):
        if not self.wrap[column]:
            if not self.wrap_header[column]:
                return max(self.minwidth[column], self.get_max_content_width(column),
                           *(len(string) for string in self.label[column].split(self.split)))
            else:
                return max(self.minwidth[column], self.get_max_content_width(column))
        else:
            if not self.wrap_header[column]:
                return max(self.minwidth[column], *(len(string) for string in self.label[column].split(self.split)))
            else:
                return self.minwidth[column]

    def get_pref_width(self, column):
        return min(self.maxwidth[column], max(self.get_max_content_width(column), self.get_pref_min_width(column)))

    def recurse(self, cols, linesize, depth):
        for i, columns in enumerate(cols):
            pageindex = i + depth if depth > 0 else i
            tot_used_width = sum([self.width[pageindex][column] + self.spacing[column] for column in columns])
            if tot_used_width < linesize:
                remain_width = linesize - tot_used_width
                while remain_width > 0 and any(
                        self.width[pageindex][column] < self.maxwidth[column] for column in columns):
                    tot_max_content_width = sum(
                        self.get_max_content_width(column) for column in columns if
                        self.width[pageindex][column] < self.maxwidth[column])
                    tot_avg_content_width = sum(
                        self.get_avg_content_width(column) for column in columns if
                        self.width[pageindex][column] < self.maxwidth[column])
                    for column in columns:
                        if self.width[pageindex][column] < self.maxwidth[column]:
                            width_ratio = math.ceil(
                                remain_width * (self.get_avg_content_width(column) / tot_avg_content_width))
                            # width_ratio = math.ceil(
                            #    remain_width * (self.get_max_content_width(column) / tot_max_content_width))
                            self.set_width(pageindex, column, max(min(self.width[pageindex][column] + width_ratio
                                                                      , self.maxwidth[column]
                                                                      , self.get_pref_width(column) if any(
                                    self.width[pageindex][column] < self.get_pref_width(column) for column in
                                    columns) else
                                                                      self.maxwidth[column]
                                                                      , self.width[pageindex][column] + linesize - sum(
                                    [self.width[pageindex][column] + self.spacing[column] for column in columns])
                                                                      , linesize - self.spacing[column]),
                                                                  self.get_pref_min_width(column)))

                    tot_used_width = sum([self.width[pageindex][column] + self.spacing[column] for column in columns])
                    remain_width = linesize - tot_used_width

            if tot_used_width > linesize:
                excess_width = tot_used_width - linesize
                while excess_width > 0 and any(
                        self.width[pageindex][column] > self.get_pref_min_width(column) for column in columns):
                    tot_max_content_width = sum(
                        self.get_max_content_width(column) for column in columns if
                        self.width[pageindex][column] > self.get_pref_min_width(column))
                    tot_avg_content_width = sum(
                        self.get_avg_content_width(column) for column in columns if
                        self.width[pageindex][column] > self.get_pref_min_width(column))
                    wgt_divisor = len(
                        [column for column in columns if
                         self.width[pageindex][column] > self.get_pref_min_width(column)]) - 1
                    for i, column in enumerate(columns):
                        if self.width[pageindex][column] > self.get_pref_min_width(column):
                            # print(tot_max_content_width, self.get_max_content_width(column), wgt_divisor)
                            # if wgt_divisor > 0:
                            #     width_ratio = math.ceil(
                            #         excess_width * ((
                            #                                 tot_max_content_width - self.get_max_content_width(column)) / tot_max_content_width) / wgt_divisor)
                            # else:
                            #     width_ratio = excess_width
                            # width_ratio = math.ceil(
                            #    excess_width * (self.get_max_content_width(column) / tot_max_content_width))
                            width_ratio = math.ceil(
                                excess_width * (self.get_avg_content_width(column) / tot_avg_content_width))
                            self.set_width(pageindex, column,
                                           min(max(self.width[pageindex][column] - width_ratio,
                                                   self.width[pageindex][column] - excess_width,
                                                   self.width[pageindex][column] + linesize - sum(
                                                       [self.width[pageindex][column] + self.spacing[column] for column
                                                        in
                                                        columns]),
                                                   self.get_pref_min_width(column),
                                                   self.get_pref_width(column) if any(
                                                       self.width[pageindex][column] > self.get_pref_width(column) for
                                                       column in
                                                       columns) else self.get_pref_min_width(column)),
                                               linesize - self.spacing[column], self.maxwidth[column]))

                    tot_used_width = sum([self.width[pageindex][column] + self.spacing[column] for column in columns])
                    excess_width = tot_used_width - linesize

                if excess_width > 0:
                    cols1 = columns
                    cols2 = tuple()

                    while excess_width > 0:
                        cols2 = (cols1[-1],) + cols2
                        cols1 = cols1[:-1]
                        tot_used_width = sum([self.width[pageindex][column] + self.spacing[column] for column in cols1])
                        excess_width = tot_used_width - linesize

                    maxkey = max(self.pages.keys())
                    self.pages[maxkey] = cols1
                    self.pages[maxkey + 1] = self.idcols + cols2

                    self.width[maxkey + 1] = {}
                    for column in self.idcols + cols2:
                        self.width[maxkey + 1][column] = self.get_pref_width(column)
                    self.recurse([cols1, self.idcols + cols2], linesize=linesize, depth=depth + 1)
        return

    def calculate_width(self, linesize):
        self.recurse([self.colorder], linesize=linesize, depth=-1)
        return self

    # def get_rows(self, pageindex):
    #     rows = {}
    #     for column in self.pages[pageindex]:
    #         for cell in self.columns[column]:
    #             cell.print_width = self.width[pageindex][column]
    #             if column in rows:
    #                 rows[column][cell.rowindex] = rows[column].get(cell.rowindex, tuple()) + (cell,)
    #             else:
    #                 rows[column] = {}
    #                 rows[column][cell.rowindex] = rows[column].get(cell.rowindex, tuple()) + (cell,)
    #
    #     #return (Row(*row) for row in zip_longest(*(self.columns[column] for column in self.pages[pageindex])))
    #
    #     rowindices = sorted(tuple(set(cell.rowindex for cell in self.cells)))
    #
    #     prevlabel = tuple()
    #     for index in rowindices:
    #         row = tuple()
    #         for column in self.pages[pageindex]:
    #             row = row + rows[column].get(index, (Cell(None, print_width=self.width[pageindex][column]),))
    #
    #         rowlabel = tuple()
    #         for cell in row:
    #             if cell.label is not None:
    #                 for label in cell.label:
    #                     if label not in rowlabel:
    #                         rowlabel = rowlabel + (label,)
    #
    #         if prevlabel != rowlabel:
    #             j = 0
    #             for i in range(len(rowlabel)):
    #                 if i < len(prevlabel):
    #                     if rowlabel[i] != prevlabel[i]:
    #                         j = i
    #                         break
    #
    #             yield Row(Cell(' ', print_width=1))
    #             for i in range(j, len(rowlabel)):
    #                 yield Row(Cell(rowlabel[i], initial_indent=i*'  '))
    #
    #         yield Row(*row)
    #         prevlabel = rowlabel

    def get_header_row(self, pageindex):
        header = tuple()

        for column in self.pages[pageindex]:
            label = Cell(self.label[column], print_width=self.width[pageindex][column],
                         spacing=self.spacing[column], split=self.split, just=self.header_just[column])
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

    def write(self, file, align_bottom=False):
        for i in range(self.max_lines):
            for cell in self.cells:
                if align_bottom:
                    if self.max_lines == cell.max_lines:
                        cell.write_line(i, file)
                    else:
                        cell.write_line(i - cell.max_lines, file)
                else:
                    cell.write_line(i, file)

            file.write('\n')


class RowLabel():
    def __init__(self, *labels, print_index=0):
        self._labels = labels
        self.print_index = print_index

    def __repr__(self):
        self.labels.__repr__()

    @property
    def labels(self):
        return (Cell(label, print_width=90) for label in self._labels)

    @labels.setter
    def labels(self, value):
        self._labels = tuple(value)

    @property
    def max_lines(self):
        return sum(label.max_lines for i, label in enumerate(self.labels) if i >= self.print_index)

    def write(self, file):
        for i, label in enumerate(self.labels):
            if i >= self.print_index:
                label.initial_indent = i*'  '
                label.write(file)

            # file.write('\n')


class RowGroup:
    def __init__(self, *rows, rowlabel):
        self.rows = rows
        self.rowlabel = rowlabel

    @property
    def max_lines(self):
        return sum(row.max_lines for row in self.rows) + self.rowlabel.max_lines

# import lorem
# testcells = ()
# for column in ('a','b','c'):
#     for row in range(10):
#         testcells = testcells + (Cell(lorem.sentence(), colindex=column, rowindex=row),)
#
# testcolumn=Columns(*testcells, colorder=('a','b','c'), linesize=145, wrap=True, minwidth=40).calculate_width()
# print(testcolumn.pages)
