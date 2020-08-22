import simplejson as json
from src.Table import *
from src.LoadStats import *
from decimal import Decimal
from operator import itemgetter
from src.LoadLabels import *


class LoadSummary:
    def __init__(self, jsonfile, statlabelconfig, statformatconfig, stattemplateconfig, statsectionindex, colindex,
                 sortindex, noprintindex, rowgrplevels, labelconfig, labelorderconfig=None, labelsectionindex=None, printanavar=True):
        self.jsonfile = jsonfile
        self.loadstats = LoadStats(labelconfig=statlabelconfig, formatconfig=statformatconfig,
                                   templateconfig=stattemplateconfig)
        self.statsectionindex = statsectionindex
        self.colindex = colindex
        self.sortindex = sortindex
        self.noprintindex = noprintindex
        self.labelsectionindex = labelsectionindex
        self.loadlabels = LoadLabels(labelconfig=labelconfig, labelorderconfig=labelorderconfig)
        self.rowgrplevels = rowgrplevels
        self.printanavar = printanavar

        with open(self.jsonfile, 'r') as fl:
            try:
                self.summary = json.load(fl, use_decimal=True).get('summary', [{}])
            except json.JSONDecodeError:
                print("invalid JSON")

    def _getindexlabel(self, index, indexvar, rowgrplevels, anavar, loadlabels):
        loadlabels.labelsection = anavar
        labels = tuple()
        if self.printanavar:
            labels = labels + (loadlabels.get_formatted_label(anavar),)
        for i in rowgrplevels:
            loadlabels.labelsection = indexvar[i]

            if i not in self.noprintindex:
                print(indexvar[i])
                labels = labels + (loadlabels.get_formatted_label(indexvar[i]),)

            labels = labels + (loadlabels.get_formatted_label(index[i]),)

        return labels

    def _getindexorder(self, index, indexvar, sortindex, anavar, loadlabels):
        loadlabels.labelordersection = anavar
        labelorder = (loadlabels.get_label_order(anavar),)
        for i in sortindex:
            loadlabels.labelordersection = indexvar[i]
            labelorder = labelorder + (loadlabels.get_label_order(index[i]),)

        return labelorder
        # return tuple(loadlabels.get_label_order(index[i]) for i in sortindex)

    # def _getrowweight(self, index, sortindex, row, loadlabels):
    #     return self._getindexorder(index, sortindex, loadlabels) + (loadlabels.get_label_order(row),)
    #
    # def _getallrows(self, summary):
    #     allrows = tuple()
    #     for record in summary:
    #         if record['type'] == 'categorical':
    #             allrows = allrows + tuple((tuple(
    #                 (index if i not in (self.colindex,) else None for i, index in enumerate(record['index']))),) + (
    #                                           key,) for key in record['rows'].keys())
    #         elif record['type'] == 'numeric':
    #             allrows = allrows + tuple((tuple(
    #                 (index if i not in (self.colindex,) else None for i, index in enumerate(record['index']))),) + (
    #                                           None,))
    #
    #     return tuple(set(allrows))
    #
    # def _sortkey(self, row):
    #     self.loadlabels.labelordersection = row[0][self.labelsectionindex]
    #     return self._getrowweight(row[0], self.sortindex, row[1], self.loadlabels)
    #
    # def _orderrows(self, rows):
    #     rowlookup = {}
    #     for i, row in enumerate(sorted(rows, key=self._sortkey)):
    #         rowlookup[row] = i
    #     return rowlookup

    # def _sortsummary(self, summary):
    #     getsortitems = itemgetter(*self.sortindex)
    #     key = lambda record: tuple(getsortitems(record['index'])) + tuple(
    #         record['index'][i] for i in range(len(record['index'])) if
    #         i not in self.sortindex and i != self.colindex) + (
    #                              record['index'][self.colindex],)
    #     return sorted(summary, key=key)

    def _loadcategoric(self):
        cells = tuple()
        # roworderlookup = self._orderrows(self._getallrows(self.summary))
        for record in self.summary:
            # self.loadstats.formatsection = record['index'][self.statsectionindex]
            # self.loadstats.templatesection = record['index'][self.statsectionindex]
            self.loadstats.labelsection = record['anavar']
            self.loadstats.formatsection = record['anavar']
            self.loadstats.templatesection = record['anavar']
            self.loadlabels.labelsection = record['indexvar']

            # roworder = 0
            # keys_wo_col = tuple(record['index'][:self.colindex] + record['index'][self.colindex + 1:])
            # keys_wo_col = tuple(record['index'][i] for i in range(len(record['index'])) if
            #                     i not in (self.colindex,) + self.noprintindex)
            #
            # if keys_wo_col != prevkeys_wo_col:
            #     keyorder += 1

            keylabels = self._getindexlabel(record['index'], record['indexvar'], self.rowgrplevels, record['anavar'], self.loadlabels)
            print(keylabels)

            for row, statdict in record['rows'].items():
                self.loadstats.stats = statdict
                stats = self.loadstats.getstats()
                for stat in stats:
                    # keylabels = tuple(self.loadlabels.get_formatted_label(key) for key in keys_wo_col)
                    self.loadlabels.labelsection = record['anavar']
                    rowlabel = self.loadlabels.get_formatted_label(row)

                    # rowindex = roworderlookup[(tuple(
                    #     (index if i not in (self.colindex,) else None for i, index in enumerate(record['index']))),) + (
                    #                               row,)]

                    indexorder = self._getindexorder(tuple(
                        (index if i not in (self.colindex,) else None for i, index in enumerate(record['index']))),
                        record['indexvar'], self.sortindex, record['anavar'], self.loadlabels)

                    self.loadlabels.labelordersection = record['anavar']
                    rowindex = indexorder + (self.loadlabels.get_label_order(row),)

                    if Cell(rowlabel, colindex="stats",
                            rowindex=rowindex,
                            label=keylabels) not in cells:
                        cells = cells + (
                            Cell(rowlabel, colindex="stats",
                                 rowindex=rowindex,
                                 label=keylabels, initial_indent=(len(keylabels) * '  ')),)
                    cells = cells + (Cell(stat[1], colindex=record['index'][self.colindex],
                                          rowindex=rowindex,
                                          label=keylabels),)

        return cells

    def _loadnumeric(self):
        cells = tuple()
        # roworderlookup = self._orderrows(self._getallrows(self.summary))
        for record in self.summary:
            self.loadstats.stats = record['statistics']
            self.loadstats.labelsection = record['anavar']
            self.loadstats.formatsection = record['anavar']
            self.loadstats.templatesection = record['anavar']

            stats = self.loadstats.getstats()

            keylabels = self._getindexlabel(record['index'], record['indexvar'], self.rowgrplevels, record['anavar'],
                                            self.loadlabels)
            print(keylabels)
            indexorder = self._getindexorder(tuple(
                (index if i not in (self.colindex,) else None for i, index in enumerate(record['index']))),
                record['indexvar'], self.sortindex, record['anavar'], self.loadlabels)

            for stat in stats:
                rowindex = indexorder + (f'{stat[2]:0>5}',)

                if Cell(stat[0], colindex="stats",
                        rowindex=rowindex,
                        label=keylabels) not in cells:
                    cells = cells + (
                        Cell(stat[0], colindex="stats",
                             rowindex=rowindex,
                             label=keylabels, initial_indent=(len(keylabels) * '  ')),)
                cells = cells + (Cell(stat[1], colindex=record['index'][self.colindex],
                                      rowindex=rowindex,
                                      label=keylabels),)

        return cells

    def getcells(self):
        keyorder = 0
        prevkeys_wo_col = tuple()
        cells = tuple()
        for record in self._sortsummary(self.summary):
            self.loadstats.stats = record['statistics']
            self.loadstats.labelsection = record['index'][self.statsectionindex]
            self.loadstats.formatsection = record['index'][self.statsectionindex]
            self.loadstats.templatesection = record['index'][self.statsectionindex]

            stats = self.loadstats.getstats()

            row = 0
            keys_wo_col = tuple(record['index'][:self.colindex] + record['index'][self.colindex + 1:])
            keys_wo_col = tuple(record['index'][i] for i in range(len(record['index'])) if
                                i not in (self.colindex,) + self.noprintindex)

            if keys_wo_col != prevkeys_wo_col:
                keyorder += 1

            for stat in stats:
                keylabels = (self.loadlabels.get_formatted_label(key) for key in keys_wo_col)
                if Cell(stat[0], colindex="stats", rowindex=(f'{keyorder:0>5}',) + keys_wo_col + (f'{row:0>5}',),
                        label=keylabels) not in cells:
                    cells = cells + (
                        Cell(stat[0], colindex="stats", rowindex=(f'{keyorder:0>5}',) + keys_wo_col + (f'{row:0>5}',),
                             label=keylabels, initial_indent=(len(keys_wo_col)) * '  '),)
                cells = cells + (Cell(stat[1], colindex=record['index'][self.colindex],
                                      rowindex=(f'{keyorder:0>5}',) + keys_wo_col + (f'{row:0>5}',),
                                      label=keylabels),)
                row += 1

            prevkeys_wo_col = keys_wo_col

        return cells


mydata = LoadSummary(jsonfile=r'.\output\json\test.json',
                     statlabelconfig=r'./output/stat-label-config.txt',
                     statformatconfig=r'./output/stat-format-config.txt',
                     stattemplateconfig=r'./output/stat-template-config.txt',
                     statsectionindex=0,
                     colindex=0,
                     sortindex=(1,),
                     noprintindex=tuple(),
                     rowgrplevels=(1,),
                     labelconfig=r'./output/label-config.txt',
                     labelorderconfig=r'./output/label-order-config.txt',
                     labelsectionindex=0,
                     printanavar=True)

page = Page(89, 45)
table = Table(Columns(
    *mydata._loadnumeric(),
    colorder=('stats', '0.15 mg/kg', '0.20 mg/kg', '0.25 mg/kg'), wrap=False, wrap_header=False,
    just=('<', '^', '^', '>', '^'), label=(None, '0.15 mg/kg', '0.20 mg/kg', '0.25 mg/kg'), idcols=('stats',),
    spacing=(0, 1, 1, 1, 1)), page=page,
    title='This is a title~Another title',
    footnotes=["This is a footnote", (datetime.now().strftime("%d%b%Y:%H:%M:%S").upper(), '>')], double_spaced=False)
# table.columns.calculate_width(table.page.linesize)
# print(table.columns.width)

with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.txt', 'w') as fl:
    table.print_table(fl)
#
# width = {'stats': 10, "0.15 mg/kg": 10, "0.20 mg/kg": 10, "0.25 mg/kg": 10}
# test = Cells(*mydata.getcells())
# test.set_cell_width(width)
#
# for group in test.getrowgroup('stats', "0.15 mg/kg", "0.20 mg/kg", "0.25 mg/kg", width=width):
#     for cell in group.rowlabel.labels:
#         print(cell)
#     for row in group.rows:
#         print(row)
