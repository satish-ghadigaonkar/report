import pandas as pd
from src.Table import *

shoes = pd.read_excel(r"C:\Users\sasg\PycharmProjects\test\src\assets\SHOES.xlsx", 'SHOES')
shoes.sort_values(by=['Region', 'Product', 'Subsidiary'], axis=0, inplace=True, ascending=True)

page = Page(95, 50)
table = Table(Columns(
    *(Cell(shoes.loc[row, column], colindex=column, rowindex=row) for column in shoes.columns for row in shoes.index),
    colorder=tuple(shoes.columns), idcols=('Region', 'Product', 'Subsidiary'), label=tuple(shoes.columns), wrap=False, wrap_header=False,
    spacing=(0, 1, 1, 1, 1, 1, 1), minwidth=10, just='<'), page=page,
              title='This is a title',
              footnotes=["This is a footnote", (datetime.now().strftime("%d%b%Y:%H:%M:%S").upper(), '>')], double_spaced=False)
#table.columns.calculate_width(table.page.linesize)

with open(r'C:\Users\sasg\PycharmProjects\report\src\output\test.txt', 'w') as fl:
    table.print_table(fl)

