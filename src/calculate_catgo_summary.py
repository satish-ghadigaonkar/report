import pandas as pd
import numpy as np
import simplejson as json
from statistics import mode
from decimal import Decimal

# adsldf = pd.read_excel(r"C:\Users\sasg\PycharmProjects\test\src\assets\adsl.xlsx", 'adsl')
adsldf = pd.read_sas(r"P:\nn7415\nn7415-4255\ctr_20190130_er\stats\data\adam\xprt\adsl.xpt", encoding='UTF-8')


class CatgoSummary:
    def __init__(self, df, anavars, byvars, idvars, stats, totalover=None):
        self.df = df
        self.anavars = self._assign_prop(anavars)
        self.byvars = self._assign_prop(byvars)
        self.idvars = self._assign_prop(idvars)
        self.stats = self._assign_prop(stats)
        self.totalover = self._assign_prop(totalover)

    def _assign_prop(self, prop):
        if isinstance(prop, (list, tuple)):
            return prop
        elif prop is not None:
            return (prop,)
        else:
            return tuple()

    def _dedup(self, df, *vars):
        return df.drop_duplicates(subset=vars)

    def _count(self, df, anavar, byvars, rename, compute_nonmiss, totalover):

        if len(byvars):
            if len(totalover):
                for totvar in totalover:
                    totaldf = df.copy()
                    totaldf[totvar] = 'TOTAL'
                    df = pd.concat([df, totaldf])

                summdf = df.groupby([*byvars])[anavar].value_counts(dropna=True).unstack(
                    level=-1).replace(np.nan, 0)
            else:
                summdf = df.groupby([*byvars])[anavar].value_counts(dropna=True).unstack(
                    level=-1).replace(np.nan, 0)
        else:
            summdf = df.groupby(['__by__' for i in range(len(df))])[anavar].value_counts(dropna=True).unstack(
                level=-1).replace(np.nan, 0)

        summdf.columns = pd.MultiIndex.from_product([summdf.columns, [rename]])

        if compute_nonmiss:
            summdf.loc[:, ('NONMISS', rename)] = summdf.sum(axis=1, numeric_only=True)
        return summdf

    def _percent(self, df, anavar, byvars, rename, compute_nonmiss, totalover, denominator=None):
        if isinstance(denominator, (np.number,)):
            pass
        else:
            if len(byvars):
                if len(totalover):
                    for totvar in totalover:
                        totaldf = df.copy()
                        totaldf[totvar] = 'TOTAL'
                        df = pd.concat([df, totaldf])

                    summdf = df.groupby([*byvars])[anavar].value_counts(normalize=True,
                                                                        dropna=True).multiply(
                        100).unstack(level=-1).replace(np.nan, 0)
                else:
                    summdf = df.groupby([*byvars])[anavar].value_counts(normalize=True, dropna=True).unstack(
                        level=-1).replace(np.nan,
                                          0)
            else:
                summdf = df.groupby(['__by__' for i in range(len(df))])[anavar].value_counts(normalize=True,
                                                                                             dropna=True).multiply(
                    100).unstack(level=-1).replace(np.nan, 0)

            summdf.columns = pd.MultiIndex.from_product([summdf.columns, [rename]])

            if compute_nonmiss:
                summdf.loc[:, ('NONMISS', rename)] = 100

            return summdf

    def _getstat(self, anavar, compute_nonmiss, totalover, stat):
        if stat == 'count':
            return self._count(self._dedup(self.df, anavar, *self.byvars, *self.idvars), anavar, self.byvars, 'count',
                               compute_nonmiss, totalover)
        elif stat == 'pct':
            return self._percent(self._dedup(self.df, anavar, *self.byvars, *self.idvars), anavar, self.byvars, 'pct',
                                 compute_nonmiss, totalover)
        elif stat == 'evnt':
            return self._count(self.df, anavar, self.byvars, 'evnt', compute_nonmiss, totalover)

    def _getstats(self, anavar, compute_nonmiss, totalover, *stats):
        return pd.concat((self._getstat(anavar, compute_nonmiss, totalover, stat) for stat in stats), axis=1,
                         join='outer')

    def _convert_to_dict(self, df, anavar):
        result = []
        for multindx in df.index:

            vardict = {'type': 'categorical', 'anavar': anavar, 'indexvar': df.index.names,'index': []}

            if isinstance(multindx, str):
                vardict['index'] = [*vardict['index'], multindx]
            else:
                vardict['index'] = [*vardict['index'], *multindx]

            for var in df.columns.unique(level=anavar):
                vardict['rows'] = vardict.get('rows', {})
                vardict['rows'][var] = df.loc[multindx, var].to_dict()

                for key, value in vardict['rows'][var].items():
                    vardict['rows'][var][key] = Decimal(str(value)) if not np.isnan(value) else None

            result.append(vardict)

        return result

    def catgosummary(self, compute_nonmiss=True):
        dict = {'summary': []}
        for anavar in self.anavars:
            dict['summary'] = [*dict['summary'],
                               *self._convert_to_dict(
                                   self._getstats(anavar, compute_nonmiss, self.totalover, *self.stats),
                                   anavar)]
        return dict


catgo = CatgoSummary(adsldf, ['RACE','ETHNIC'], ['TRTLST','SEX'], 'SUBJID', ['count', 'pct'], ['TRTLST'])


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


with open(r'./output/json/test.json', 'w') as file:
    json.dump(catgo.catgosummary(compute_nonmiss=True), file, cls=NpEncoder, use_decimal=True)
