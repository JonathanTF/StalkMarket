import typing

import turnips
from turnips.meta import MetaModel
from turnips.ttime import TimePeriod
from turnips.model import ModelEnum
#import src.stalk_time as stlk_time
from stalk_time import DayOfTheWeek, TimeOfDay
from adapted_predictions import analyze_possibilities
#try:
#    from src.adapted_predicitions import analyze_possibilities
#except ModuleNotFoundError:


_MIN_NUMBER_MODELS = 10

PATTERN_STRING_TO_NUMBER = {
    "fluctuating": 0,
    "large spike": 1,
    "decreasing": 2,
    "small spike": 3,
    "all": 4
}

PATTERN_NUMBER_TO_STRING = {
    0: "fluctuating",
    1: "large spike",
    2: "decreasing",
    3: "small spike",
    4: "all"
}


def add_spaces(value: str) -> str:
    remaining_spots = 12 - len(value)
    if remaining_spots < 0:
        print("ERROR: encountered a value entry that was larger than 10 characters!")
    spaces_per_side = int(remaining_spots / 2)
    one_if_odd_zero_otherwise = (remaining_spots % 2)

    value = (' ' * spaces_per_side) + value + (' ' * spaces_per_side) + (' ' * one_if_odd_zero_otherwise)

    # if len(value) < 10:
    #    value += ' '*(10-len(value))
    # value += ' '
    return value


class PredictionResult:
    
    def __init__(self, pattern):#, monday_am = "", monday_pm = "", tuesday_am = "", tuesday_pm = "", wednesday_am = "", wednesday_pm = "", thursday_am = "", thursday_pm = "", friday_am = "", friday_pm = "", saturday_am = "", saturday_pm = ""):
        self.pattern = pattern

        self.prices = {DayOfTheWeek.MONDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""},
                       DayOfTheWeek.TUESDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""},
                       DayOfTheWeek.WEDNESDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""},
                       DayOfTheWeek.THURSDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""},
                       DayOfTheWeek.FRIDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""},
                       DayOfTheWeek.SATURDAY: {TimeOfDay.AM: "", TimeOfDay.PM: ""}}

        """
        self.monday_am = monday_am
        self.monday_pm = monday_pm
        self.tuesday_am = tuesday_am
        self.tuesday_pm = tuesday_pm
        self.wednesday_am = wednesday_am
        self.wednesday_pm = wednesday_pm
        self.thursday_am = thursday_am
        self.thursday_pm = thursday_pm
        self.friday_am = friday_am
        self.friday_pm = friday_pm
        self.saturday_am = saturday_am
        self.saturday_pm = saturday_pm
        """

    def __str__(self):
        pattern = self.pattern
        if len(pattern) > 11:
            pattern = pattern[:11] + ' '
        else:
            pattern = self.pattern + ' '*(12-len(pattern))



        return f"{pattern}|{add_spaces(self.prices[DayOfTheWeek.MONDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.MONDAY][TimeOfDay.PM])}" \
               f"{add_spaces(self.prices[DayOfTheWeek.TUESDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.TUESDAY][TimeOfDay.PM])}" \
               f"{add_spaces(self.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.PM])}" \
               f"{add_spaces(self.prices[DayOfTheWeek.THURSDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.THURSDAY][TimeOfDay.PM])}" \
               f"{add_spaces(self.prices[DayOfTheWeek.FRIDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.FRIDAY][TimeOfDay.PM])}" \
               f"{add_spaces(self.prices[DayOfTheWeek.SATURDAY][TimeOfDay.AM])}{add_spaces(self.prices[DayOfTheWeek.SATURDAY][TimeOfDay.PM])}"

        """
        return f"{self.pattern}\t\t{self.prices[DayOfTheWeek.MONDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.MONDAY][TimeOfDay.PM]}\t" \
               f"{self.prices[DayOfTheWeek.TUESDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.TUESDAY][TimeOfDay.PM]}\t" \
               f"{self.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.PM]}\t" \
               f"{self.prices[DayOfTheWeek.THURSDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.THURSDAY][TimeOfDay.PM]}\t" \
               f"{self.prices[DayOfTheWeek.FRIDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.FRIDAY][TimeOfDay.PM]}\t" \
               f"{self.prices[DayOfTheWeek.SATURDAY][TimeOfDay.AM]}\t{self.prices[DayOfTheWeek.SATURDAY][TimeOfDay.PM]}"
        """

def predictions_list_generator(predictions: typing.List[PredictionResult]):
    yield f"`Pattern     |{add_spaces('Mon-AM')}{add_spaces('Mon-PM')}{add_spaces('Tues-AM')}{add_spaces('Tues-PM')}{add_spaces('Wed-AM')}{add_spaces('Wed-PM')}{add_spaces('Thurs-AM')}{add_spaces('Thurs-PM')}{add_spaces('Fri-AM')}{add_spaces('Fri-PM')}{add_spaces('Sat-AM')}{add_spaces('Sat-PM')}`\n"
    for prediction in predictions:
        yield f"`{str(prediction)}`\n"

#def get_human_readable_model_enum(model_enum:turnips.)


def get_valid_patterns() -> typing.List[str]:
    return ['large spike', 'small spike', 'decreasing', 'fluctuating', 'unknown']


def get_pattern_info(pattern: str) -> str:

    if pattern == 'small spike':
        return "A bump market, or small spike, is identified by a period of decreasing prices, followed by a period of increasing prices, finally followed by another period of decreasing prices. Prices will increase 5 times, after which they will only go down."
    elif pattern == 'decreasing':
        return "A decay market, or decreasing, is identified by decreasing prices every single day. It is recommended to either find another Stalk Market or sell your Turnips at a loss."
    elif pattern == 'large spike':
        return "A spike market, or large spike, is identified by a period of decreasing prices, followed by a sharp increase in prices. Prices will increase 3 times, where the third increase will yield the highest prices, between 2x to 6x of Daisy's prices. This is the best market to be in, please notify your friends if your market matches this pattern!"
    elif pattern == 'fluctuating':
        return "A triple market, or triple peak, is identified by two phases of increasing then decreasing prices, finished with a final phase of increasing prices. It is possible to turn a profit on any of the 3 peaks, but they are generally not as reliable as other markets."
    elif pattern == 'unknown':
        return "An unknown market is a market that is either completely random, or is a new market the Nooks have introduced to keep the Stalk Index on its toes. If there is a definite pattern to your Market but it isn't classified, you may have discovered a new market pattern."
    else:
        return f"The Stalk Index doesn't have any information on the {pattern} market pattern."


async def predict(stalk_data: typing.Dict, previous_week: str) -> (typing.Dict[str, float], typing.List[PredictionResult]):

    previous_week_number = None
    try:
        previous_week_number = PATTERN_STRING_TO_NUMBER[previous_week]
    except KeyError:
        pass

    #prices = [97, 97, 84, 81, 77, 73, 69, 66, None, None, None, None, None, None]

    prices = [None, None, None, None, None, None, None, None, None, None, None, None, None, None]
    # convert dictionary to list of prices
    if stalk_data['SUNDAY']['AM'] > 0:
        prices[0] = stalk_data['SUNDAY']['AM']
        prices[1] = stalk_data['SUNDAY']['AM']
    if stalk_data['MONDAY']['AM'] > 0:
        prices[2] = stalk_data['MONDAY']['AM']
    if stalk_data['MONDAY']['PM'] > 0:
        prices[3] = stalk_data['MONDAY']['PM']
    if stalk_data['TUESDAY']['AM'] > 0:
        prices[4] = stalk_data['TUESDAY']['AM']
    if stalk_data['TUESDAY']['PM'] > 0:
        prices[5] = stalk_data['TUESDAY']['PM']
    if stalk_data['WEDNESDAY']['AM'] > 0:
        prices[6] = stalk_data['WEDNESDAY']['AM']
    if stalk_data['WEDNESDAY']['PM'] > 0:
        prices[7] = stalk_data['WEDNESDAY']['PM']
    if stalk_data['THURSDAY']['AM'] > 0:
        prices[8] = stalk_data['THURSDAY']['AM']
    if stalk_data['THURSDAY']['PM'] > 0:
        prices[9] = stalk_data['THURSDAY']['PM']
    if stalk_data['FRIDAY']['AM'] > 0:
        prices[10] = stalk_data['FRIDAY']['AM']
    if stalk_data['FRIDAY']['PM'] > 0:
        prices[11] = stalk_data['FRIDAY']['PM']
    if stalk_data['SATURDAY']['AM'] > 0:
        prices[12] = stalk_data['SATURDAY']['AM']
    if stalk_data['SATURDAY']['PM'] > 0:
        prices[13] = stalk_data['SATURDAY']['PM']

    first_buy = False
    prophet_results = analyze_possibilities(prices, first_buy, previous_week_number)

    probabilities = []
    probabilities = {'fluctuating': 0.0,
                     'large spike': 0.0,
                     'small spike': 0.0,
                     'decreasing': 0.0}
    remaining_patterns = [PATTERN_NUMBER_TO_STRING[x] for x in [0, 1, 2, 3]]

    for result in prophet_results:
        pattern = PATTERN_NUMBER_TO_STRING[result.pattern_number]
        if pattern in probabilities:
            probabilities[pattern] += result.probability
    for pattern in probabilities.keys():
        probabilities[pattern] = round(probabilities[pattern] * 100, 2)

    prediction_results = []

    for result in prophet_results:
        if result.pattern_number > 3:
            continue

        prediction_result = PredictionResult(result.pattern_description)

        prices = result.prices

        prediction_result.prices[DayOfTheWeek.MONDAY][TimeOfDay.AM] = str(prices[2])
        prediction_result.prices[DayOfTheWeek.MONDAY][TimeOfDay.PM] = str(prices[3])
        prediction_result.prices[DayOfTheWeek.TUESDAY][TimeOfDay.AM] = str(prices[4])
        prediction_result.prices[DayOfTheWeek.TUESDAY][TimeOfDay.PM] = str(prices[5])
        prediction_result.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.AM] = str(prices[6])
        prediction_result.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.PM] = str(prices[7])
        prediction_result.prices[DayOfTheWeek.THURSDAY][TimeOfDay.AM] = str(prices[8])
        prediction_result.prices[DayOfTheWeek.THURSDAY][TimeOfDay.PM] = str(prices[9])
        prediction_result.prices[DayOfTheWeek.FRIDAY][TimeOfDay.AM] = str(prices[10])
        prediction_result.prices[DayOfTheWeek.FRIDAY][TimeOfDay.PM] = str(prices[11])
        prediction_result.prices[DayOfTheWeek.SATURDAY][TimeOfDay.AM] = str(prices[12])
        prediction_result.prices[DayOfTheWeek.SATURDAY][TimeOfDay.PM] = str(prices[13])

        prediction_results.append(prediction_result)

    return probabilities, prediction_results



