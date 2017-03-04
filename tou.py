import numpy as np
import pandas as pd
from datetime import datetime


def string_date(mnthDay, year):
    """Return a string date as 'mm/dd/yyyy'.

       Argument format:
       'mm/dd' string
       'yyyy'"""
    return(mnthDay + '/' + str(year))


class TouRate(object):
    """Object for Utility Time Of Use Tariff.

    Class for a utilty time of use tariff structure.  TouRate provides
    methods to slice a dataframe with an year long hourly datetime axis (8760)
    by the time periods defined by a time of use (TOU) utility rate.

    Instance Variables:
    year - integer year for the anlaysis; the year effects holidays
    cal - an instance of pandas holiday calendar
    deliveryPrice - float price for the base elec. price ($/kWh)
    periods - dictionary defining the time of use periods

    Periods dict format days dict can be empty
    SCE_TOU_GS_2 = {'holWkndsWinter': {'dates': ('10/01', '5/31'),
                                    'times': ('00:00', '23:00'),
                                    'days': {'dropHol': True, 'dropWknd': True, 'inverse': True},
                                    'price': 0.04064}
                   }

    Methods:
    spans_year - returns bool indicating if tou period spans calendar year
    filter_days - Returns dataframe without holidays or weekends or inverse
    get_period - Returns dataframe with only hours and days from the give tou period
    get_all_periods - Returns dataframe with a column for each tou period.
    get_rates - Returns dataframe with TOU period rates from TouRate object.

    """
    def __init__(self,
                 year,
                 cal,
                 deliveryPrice,
                 periods={}):

        self.year = year
        self.cal = cal
        self.deliveryPrice = deliveryPrice
        self.periods = periods

    def spans_year(self, key):
        """Returns bool indicating spanning calendar year end.

        Arguments:
        dict key (string) for the TOU period to check
        """
        startDate = string_date(self.periods[key]['dates'][0], self.year)
        endDate = string_date(self.periods[key]['dates'][1], self.year)
        startDay = pd.date_range(startDate, periods=1).dayofyear
        endDay = pd.date_range(endDate, periods=1).dayofyear
        return(endDay[0] - startDay[0] < 0)

    def filter_days(self, df, col=0, dropWknd=True, dropHol=True, inverse=False):
        """Returns dataframe without holidays or weekends or inverse.

        Arguments:
        df - dataframe of energy production (hourly)

        Keyword arguments:
        dropWknd=bool  default is True
        dropHol=bool, default is True
        inverse=bool, default is False
        """
        # create function to check this and return error?
        # if df.index.date[0].year == self.year:
        df_int = pd.DataFrame()
        if df_int.empty:
            if dropWknd & dropHol:
                df_int = df[df.columns[col]].loc[~np.in1d(df.index.date, df.index[df.index.weekday > 4].date)]
                df_int = df_int.to_frame()
                holExcp = self.cal.holidays(datetime(self.year, 1, 1), datetime(self.year, 12, 31), return_name=False)
                df_int = df_int.loc[~np.in1d(df_int.index.date, holExcp.date)]
            elif dropWknd:
                df_int = df.loc[~np.in1d(df.index.date, df.index[df.index.weekday > 4].date)]
            elif dropHol:
                holExcp = self.cal.holidays(datetime(self.year, 1, 1), datetime(self.year, 12, 31), return_name=False)
                df_int = df.loc[~np.in1d(df.index.date, holExcp.date)]
            else:
                df_int = df

        if inverse:
            return(df[df.columns[col]].loc[~np.in1d(df.index.date, df_int.index.date)])
        else:
            return(df_int)

    def get_period(self, df, key, col=0):
        """Returns dataframe with only hours and days from the give tou period.

        Arguments:
        df - dataframe of hourly energy production data
        key - dict key of TOU period defined in the
        """
        daysFiltered = self.filter_days(df, col=col, **self.periods[key]['days'])
        perStart = string_date(self.periods[key]['dates'][0], df.index[0].date().year)
        perEnd = string_date(self.periods[key]['dates'][1], df.index[0].date().year)
        if self.spans_year(key):
            # slice period for beginning of the year
            fall = daysFiltered.ix[perStart:string_date('12/31', df.index[0].date().year)]
            fall = fall.between_time(self.periods[key]['times'][0], self.periods[key]['times'][1])
            fall = fall.sort_index()
            # slice period for end of the year
            spring = fall.append(daysFiltered.ix[string_date('1/1', df.index[0].date().year):perEnd])
            spring = spring.between_time(self.periods[key]['times'][0], self.periods[key]['times'][1])
            spring = spring.sort_index()
            if isinstance(spring, pd.DataFrame):
                return(spring.rename_axis({spring.columns[0]: key}, axis=1))
            else:
                spring = spring.to_frame()
                return(spring.rename_axis({spring.columns[0]: key}, axis=1))
        else:
            df_temp = daysFiltered.ix[perStart:perEnd]
            df_temp = df_temp.between_time(self.periods[key]['times'][0], self.periods[key]['times'][1])
            if isinstance(df_temp, pd.DataFrame):
                return(df_temp.rename_axis({df_temp.columns[0]: key}, axis=1))
            else:
                df_temp = df_temp.to_frame()
                return(df_temp.rename_axis({df_temp.columns[0]: key}, axis=1))

    def get_all_periods(self, df, col=0):
        """Returns dataframe with a column for each tou period.

        Arguments:
        df - dataframe of hourly energy production data
        """
        df_append = pd.DataFrame()
        for index, element in enumerate(self.periods):
            df_temp = self.get_period(df, element, col)
            df_append = df_append.append(df_temp)
        return(df_append.sort_index())

    def get_rates(self):
        """Returns dataframe with TOU period rates from TouRate object."""
        rates = np.empty(len(self.periods))
        for index, element in enumerate(self.periods):
            rates[index] = self.periods[element]['price']
        return(pd.Series(rates, self.periods.keys()))

    def get_summary(self, df, col=0):
        """Returns datafame with summary TOU data of input dataframe.

        Arguments:
        df - dataframe of hourly energy production data
        col - column of dataframe to slice, default 0
        """
        results_df = pd.DataFrame({'Energy kWh': self.get_all_periods(df, col).sum()})
        results_df['Prices $/kWh'] = self.deliveryPrice + self.get_rates()
        results_df['Value $'] = results_df['Energy kWh'] * results_df['Prices $/kWh']
        return(results_df)

"""
    def check_times(self):
        ""Returns df with TOU period rates from TouRate object.
        No arguments required
        ""
        for index, element in enumerate(self.periods):
            if index == 0:
                season = self.periods[element]['date']
            elif season = self.periods[element]['date']
                start_times = pd.Series(index=np.arange(len(self.periods)))
                end_times = pd.Series(index=np.arange(len(self.periods)))
                for index, element in enumerate(self.periods):
                    start_times[index] = int(self.periods[element]['times'][0][0:2])
                    end_times[index] = int(self.periods[element]['times'][1][0:2])

        return(start_times, end_times)
        #return(pd.Series(rates, self.periods.keys()))
"""
