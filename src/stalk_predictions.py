import typing

import turnips
from turnips.meta import MetaModel
from turnips.ttime import TimePeriod
from turnips.model import ModelEnum
#import src.stalk_time as stlk_time
from stalk_time import DayOfTheWeek, TimeOfDay

_MIN_NUMBER_MODELS = 10


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
    
    def __init__(self, pattern = ""):#, monday_am = "", monday_pm = "", tuesday_am = "", tuesday_pm = "", wednesday_am = "", wednesday_pm = "", thursday_am = "", thursday_pm = "", friday_am = "", friday_pm = "", saturday_am = "", saturday_pm = ""):
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
        if len(pattern) > 10:
            pattern = pattern[:10] + ' '
        else:
            pattern = self.pattern + ' '*(11-len(pattern))



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
    yield f"`Pattern    |{add_spaces('Mon-AM')}{add_spaces('Mon-PM')}{add_spaces('Tues-AM')}{add_spaces('Tues-PM')}{add_spaces('Wed-AM')}{add_spaces('Wed-PM')}{add_spaces('Thurs-AM')}{add_spaces('Thurs-PM')}{add_spaces('Fri-AM')}{add_spaces('Fri-PM')}{add_spaces('Sat-AM')}{add_spaces('Sat-PM')}`\n"
    for prediction in predictions:
        yield f"`{str(prediction)}`\n"

#def get_human_readable_model_enum(model_enum:turnips.)


def get_valid_patterns() -> typing.List[str]:
    return ['bump', 'decay', 'spike', 'triple', 'unknown']


def get_short_prediction_string(predictions: typing.List[PredictionResult]) -> str:

    if len(predictions) <= 0:
        return "it looks like your Stalk Market is experiencing a Random Market! ...sorry!"

    pattern_dict = {'bump': 0,
                    'decay': 0,
                    'spike': 0,
                    'triple': 0,
                    'unknown': 0}

    for prediction in predictions:
        pattern_dict[prediction.pattern] += 1

    # check for number of winners
    valid_patterns = []
    for key in pattern_dict.keys():
        #if key == 'unknown':
        #    continue
        if pattern_dict[key] > 0:
            valid_patterns.append(key)

    if len(valid_patterns) == 0:
        return "your Stalk Market doesn't match any known pattern! ...sorry!"
    elif len(valid_patterns) == 1:
        return f"your Stalk Market will very likely follow the **{valid_patterns[0]}** pattern!\n" + get_pattern_info(valid_patterns[0])
    elif len(valid_patterns) == 2:
        return f"your Stalk Market could follow either the **{valid_patterns[0]}** pattern or the **{valid_patterns[1]}** pattern."
    elif len(valid_patterns) >= 3:
        return f"your Stalk Market could follow pretty much any pattern! ...sorry!"


def get_pattern_info(pattern: str) -> str:

    if pattern == 'bump':
        return "A bump market, or small spike, is identified by a period of decreasing prices, followed by a period of increasing prices, finally followed by another period of decreasing prices. Prices will increase 5 times, after which they will only go down."
    elif pattern == 'decay':
        return "A decay market, or decreasing, is identified by decreasing prices every single day. It is recommended to either find another Stalk Market or sell your Turnips at a loss."
    elif pattern == 'spike':
        return "A spike market, or large spike, is identified by a period of decreasing prices, followed by a sharp increase in prices. Prices will increase 3 times, where the third increase will yield the highest prices, between 2x to 6x of Daisy's prices. This is the best market to be in, please notify your friends if your market matches this pattern!"
    elif pattern == 'triple':
        return "A triple market, or triple peak, is identified by two phases of increasing then decreasing prices, finished with a final phase of increasing prices. It is possible to turn a profit on any of the 3 peaks, but they are generally not as reliable as other markets."
    elif pattern == 'unknown':
        return "An unknown market is a market that is either completely random, or is a new market the Nooks have introduced to keep the Stalk Index on its toes. If there is a definite pattern to your Market but it isn't classified, you may have discovered a new market pattern."
    else:
        return f"The Stalk Index doesn't have any information on the {pattern} market pattern."


async def predict(stalk_data: typing.Dict) -> (int, typing.List[PredictionResult]):

    day_strings = [str(x) for x in [DayOfTheWeek.MONDAY, DayOfTheWeek.TUESDAY, DayOfTheWeek.WEDNESDAY, DayOfTheWeek.THURSDAY, DayOfTheWeek.FRIDAY, DayOfTheWeek.SATURDAY]]
    turnips_day_strings = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    time_strings = [str(x) for x in [TimeOfDay.AM, TimeOfDay.PM]]

    turnips_model = MetaModel.blank()

    day_index = 0
    while day_index < 6:

        for time_of_day in time_strings:
            user_price = stalk_data[day_strings[day_index]][time_of_day]
            if user_price != 0:
                turnip_string = f"{turnips_day_strings[day_index]}_{time_of_day}"
                turnips_model.fix_price(turnip_string, user_price)

        day_index += 1

    #num_models = len(turnips_model)
    #if len(turnips_model) > _MIN_NUMBER_MODELS:
    #    return num_models, None
        #return f"your currently fits {len(turnips_model)} different models. Please provide more data to narrow the search."

    #report = f'your turnip data fits {num_models} models:\n'
    #report += "`Pattern\tM-am\tM-pm\tTu-am\tTu-pm\tW-am\tW-pm\tTh-am\tTh-pm\tF-am\tF-pm\tSa-am\tSa-pm\tDetails`\n"

    prediction_results = []
    for model in turnips_model.models:
        prediction_result = PredictionResult()
        prediction_result.pattern = str(model.model_name)

        #for time in [TimePeriod.Monday_AM, TimePeriod.Monday_PM, TimePeriod.Tuesday_AM, TimePeriod.Tuesday_PM,
        #             TimePeriod.Wednesday_AM, TimePeriod.Wednesday_PM, TimePeriod.Thursday_AM, TimePeriod.Thursday_PM,
        #             TimePeriod.Friday_AM, TimePeriod.Friday_PM, TimePeriod.Saturday_AM, TimePeriod.Saturday_PM]:
            
        prediction_result.prices[DayOfTheWeek.MONDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Monday_AM].price)
        prediction_result.prices[DayOfTheWeek.MONDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Monday_PM].price)
        prediction_result.prices[DayOfTheWeek.TUESDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Tuesday_AM].price)
        prediction_result.prices[DayOfTheWeek.TUESDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Tuesday_PM].price)
        prediction_result.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Wednesday_AM].price)
        prediction_result.prices[DayOfTheWeek.WEDNESDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Wednesday_PM].price)
        prediction_result.prices[DayOfTheWeek.THURSDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Thursday_AM].price)
        prediction_result.prices[DayOfTheWeek.THURSDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Thursday_PM].price)
        prediction_result.prices[DayOfTheWeek.FRIDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Friday_AM].price)
        prediction_result.prices[DayOfTheWeek.FRIDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Friday_PM].price)
        prediction_result.prices[DayOfTheWeek.SATURDAY][TimeOfDay.AM] = str(model.timeline[TimePeriod.Saturday_AM].price)
        prediction_result.prices[DayOfTheWeek.SATURDAY][TimeOfDay.PM] = str(model.timeline[TimePeriod.Saturday_PM].price)

        prediction_results.append(prediction_result)

    return prediction_results

    #print(f"Number of models available: {len(turnips_model)}\n\n")


    #print(turnips_model.report(show_summary=True))
    #print(turnips_model.summary())







