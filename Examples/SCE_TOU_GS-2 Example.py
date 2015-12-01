import os.path
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.holiday import Holiday, USPresidentsDay, USMemorialDay, USLaborDay, USThanksgivingDay, AbstractHolidayCalendar, sunday_to_monday

import tou
#reload(tou)

dirName = os.path.normpath("./rooftop.csv")  # path to PVsyst hourly output normpath converts to correct backslashes for OS
df = pd.read_csv(dirName)  # path to PVsyst hourly output
year = 2015

rng = pd.date_range('1/1/' + str(2016), periods=8760, freq='h')
df.index = rng


class SCE_Holidays(AbstractHolidayCalendar):

    """
    Southern California Edison Holidays from the tariff- TOU-GS-2
    """

    rules = [
        Holiday('New Years Day', month=1, day=1, observance=sunday_to_monday),
        USPresidentsDay,
        USMemorialDay,
        Holiday('July 4th', month=7, day=4, observance=sunday_to_monday),
        USLaborDay,
        Holiday('Veterans Day', month=11, day=11, observance=sunday_to_monday),
        USThanksgivingDay,
        Holiday('Christmas', month=12, day=25, observance=sunday_to_monday)
    ]

cal = SCE_Holidays()

SCE_TOU_GS_2 = {'offPeak1': {'dates': ('06/01', '9/30'),
                             'times': ('00:00', '08:00'),
                             'days': {},
                             'price': 0.03855},
                'midPeak1': {'dates': ('06/01', '9/30'),
                             'times': ('09:00', '12:00'),
                             'days': {},
                             'price': 0.06143},
                'onPeak': {'dates': ('06/01', '9/30'),
                           'times': ('13:00', '18:00'),
                           'days': {},
                           'price': 0.31971},
                'midPeak2': {'dates': ('06/01', '9/30'),
                             'times': ('19:00', '23:00'),
                             'days': {},
                             'price': 0.06143},
                'midPeak3': {'dates': ('10/01', '5/31'),
                             'times': ('09:00', '21:00'),
                             'days': {},
                             'price': 0.06073},
                'offPeak2': {'dates': ('10/01', '5/31'),
                             'times': ('22:00', '08:00'),
                             'days': {},
                             'price': 0.04064},
                'holWkndsSummer': {'dates': ('06/01', '09/30'),
                                   'times': ('00:00', '23:00'),
                                   'days': {'dropHol': True, 'dropWknd': True, 'inverse': True},
                                   'price': 0.03584},
                'holWkndsWinter': {'dates': ('10/01', '5/31'),
                                   'times': ('00:00', '23:00'),
                                   'days': {'dropHol': True, 'dropWknd': True, 'inverse': True},
                                   'price': 0.04064}
                }

sce_GS2 = tou.TouRate(year, cal, 0.04482, SCE_TOU_GS_2)

if __name__ == '__main__':
    print(sce_GS2.get_summary(df))
