import pandas as pd
import numpy as np
import simplejson as json
from statistics import mode
from decimal import Decimal

shoesDf = pd.read_excel(r"C:\Users\sasg\PycharmProjects\test\src\assets\adsl.xlsx", 'adsl')


def _rename(newname):
    def decorator(f):
        f.__name__ = newname
        return f

    return decorator


def q_at(y):
    @_rename(f'{y * 100:.0f}%')
    def q(x):
        return x.quantile(y)

    return q


class NestedDict(dict):
    """
    Nested dictionary of arbitrary depth with autovivification.

    Allows data access via extended slice notation.
    """

    def __getitem__(self, keys):
        # Let's assume *keys* is a list or tuple.
        if not isinstance(keys, str):
            try:
                node = self
                for key in keys:
                    node = dict.__getitem__(node, key)
                return node
            except TypeError:
                # *keys* is not a list or tuple.
                pass
        try:
            return dict.__getitem__(self, keys)
        except KeyError:
            raise KeyError(keys)

    def __contains__(self, keys):
        # Let's assume *keys* is a list or tuple.
        if not isinstance(keys, str):
            try:
                node = self
                for key in keys:
                    if dict.__contains__(node, key):
                        node = dict.__getitem__(node, key)
                    else:
                        return False
                return node
            except TypeError:
                # *keys* is not a list or tuple.
                pass

        return dict.__contains__(self, keys)

    def __setitem__(self, keys, value):
        # Let's assume *keys* is a list or tuple.
        if not isinstance(keys, str):
            try:
                node = self
                for key in keys[:-1]:
                    try:
                        node = dict.__getitem__(node, key)
                    except KeyError:
                        node[key] = type(self)()
                        node = node[key]
                return dict.__setitem__(node, keys[-1], value)
            except TypeError:
                # *keys* is not a list or tuple.
                pass
        dict.__setitem__(self, keys, value)


class NumericSummary():
    def __init__(self, df, anavar, byvars=None, stats=['mean'], totalover=None):
        self.df = df
        self.anavar = anavar
        self.stats = stats if type(stats) is list else [stats]
        self.byvars = byvars if type(byvars) is list else [byvars]

    def _calculate_stats(self, compute_total=False):
        # for stat in self.stats:
        if compute_total:
            df1 = self.df.loc[:, self.anavar + self.byvars]
            # df1.insert(0, self.columns[0], ['TOTAL' for i in range(self.df.shape[0])], False)

            return pd.concat([
                self.df.loc[:, self.anavar + self.byvars].groupby(self.byvars).agg(
                    self.stats),
                df1.groupby(self.byvars).agg(
                    self.stats)])
        else:
            return self.df.loc[:, self.anavar + self.byvars].groupby(self.byvars).agg(
                self.stats)
        # return self.df.pivot_table(values=self.anavar, index=self.by, aggfunc=self.stats)

    def _calculate_catgo_stats(self, compute_total=False):
        return self.df.loc[:, self.anavar + self.byvars + self.columns].groupby(
            self.byvars + self.columns).value_counts()
        # return pd.concat( (pd.crosstab([self.df[var] for var in self.byvars + self.columns], self.df[analysisvar]) for analysisvar in self.anavar), axis=1, join='outer', keys=self.anavar)

    def _convert_to_dict(self, summarydf):
        final = {'summary': []}
        for var in summarydf.columns.unique(level=0):
            for multindx in summarydf.index:
                vardict = {'type': 'numeric', 'anavar': var, 'indexvar': summarydf.index.names,'index': []}
                # cnt = 0

                # for i in range(len(self.byvars)):
                #     vardict['index'].append(multindx[i])
                #     cnt += 1

                # for i in range(len(multindx)):
                #     vardict['index'].append(multindx[i])

                if isinstance(multindx, str):
                    vardict['index'] = [*vardict['index'], multindx]
                else:
                    vardict['index'] = [*vardict['index'], *multindx]

                vardict['statistics'] = summarydf.loc[multindx, var].to_dict()

                for key, value in vardict['statistics'].items():
                    vardict['statistics'][key] = value if not np.isnan(value) else None

                final['summary'].append(vardict)

        return final


def _schema(self):
    schema = {'anavar': self.anavar, 'column': self.columns, 'byvar': self.byvars}
    return schema


numsum = NumericSummary(shoesDf, ['AGE','WGTBL','HGTBL'], ['TRTLST','RACE'],
                        ['count', 'mean', 'std', 'median', 'min', 'max', mode, q_at(0.05), q_at(0.95)])


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


# print(numsum._calculate_catgo_stats(compute_total=False))
with open(r'./output/json/test.json', 'w') as file:
    json.dump(numsum._convert_to_dict(numsum._calculate_stats(compute_total=False)), file, cls=NpEncoder,
              use_decimal=True)
