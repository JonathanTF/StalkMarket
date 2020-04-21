"""
A rough Python conversion of the js prediction algorithm at https://github.com/mikebryant/ac-nh-turnip-prices
TODO: cleanup and credit
"""

from enum import IntEnum
import numpy as np
import typing
from collections import namedtuple
from dataclasses import dataclass

import logging

#Range = namedtuple('Range', 'min max')

@dataclass
class Range:
    min: int
    max: int

    def __str__(self):
        if self.min == self.max:
            return f"{int(self.min)}"
        return f"[{int(self.min)}, {int(self.max)}]"

@dataclass
class Prediction:
    pattern_description: str
    pattern_number: int
    prices: typing.List
    probability: float
    weekGuaranteedMinimum: int = 0
    weekMax: int = 0
    category_total_probability: float = 0

#Prediction = namedtuple('Prediction', 'pattern_description pattern_number prices probability weekGuaranteedMinimum weekMax category_total_probability')

# The reverse-engineered code is not perfectly accurate, especially as it's not
# 32-bit ARM floating point. So, be tolerant of slightly unexpected inputs
FUDGE_FACTOR = 5


class PATTERN(IntEnum):
    FLUCTUATING = 0,
    LARGE_SPIKE = 1,
    DECREASING = 2,
    SMALL_SPIKE = 3


PROBABILITY_MATRIX = {
    PATTERN.FLUCTUATING: {
        PATTERN.FLUCTUATING: 0.20,
        PATTERN.LARGE_SPIKE: 0.30,
        PATTERN.DECREASING: 0.15,
        PATTERN.SMALL_SPIKE: 0.35,
    },
    PATTERN.LARGE_SPIKE: {
        PATTERN.FLUCTUATING: 0.50,
        PATTERN.LARGE_SPIKE: 0.05,
        PATTERN.DECREASING: 0.20,
        PATTERN.SMALL_SPIKE: 0.25,
    },
    PATTERN.DECREASING: {
        PATTERN.FLUCTUATING: 0.25,
        PATTERN.LARGE_SPIKE: 0.45,
        PATTERN.DECREASING: 0.05,
        PATTERN.SMALL_SPIKE: 0.25,
    },
    PATTERN.SMALL_SPIKE: {
        PATTERN.FLUCTUATING: 0.45,
        PATTERN.LARGE_SPIKE: 0.25,
        PATTERN.DECREASING: 0.15,
        PATTERN.SMALL_SPIKE: 0.15,
    },
}

RATE_MULTIPLIER = 10000


def intceil(val):
    return np.trunc(val + 0.99999) # todo does this do the thing as js.Math.trunc?


def minimum_rate_from_given_and_base(given_price, buy_price):
    return RATE_MULTIPLIER * (given_price - 0.99999) / buy_price


def maximum_rate_from_given_and_base(given_price, buy_price):
    return RATE_MULTIPLIER * (given_price + 0.00001) / buy_price


def rate_range_from_given_and_base(given_price, buy_price):
    return [
        minimum_rate_from_given_and_base(given_price, buy_price),
        maximum_rate_from_given_and_base(given_price, buy_price)
    ]


def get_price(rate, basePrice):
    return intceil(rate * basePrice / RATE_MULTIPLIER)

#function* multiply_generator_probability(generator, probability) {
#  for (const it of generator) {
#    yield {...it, probability: it.probability * probability};
#  }
#}


def multiply_generator_probability(generator, probability):
    for prediction in generator:
        prediction.probability *= probability
        yield prediction


def clamp(x, min_, max_):
    return min(max(x, min_), max_)


def range_length(range_):
    return range_[1] - range_[0]


def range_intersect(range1, range2):
    if (range1[0] > range2[1]) or (range1[1] < range2[0]):
        return None
    return [max(range1[0], range2[0]), min(range1[1], range2[1])]


def range_intersect_length(range1, range2):
    if (range1[0] > range2[1]) or (range1[1] < range2[0]):
        return 0
    return range_length(range_intersect(range1, range2))

"""
/*
 * This corresponds to the code:
 *   for (int i = start; i < start + length; i++)
 *   {
 *     sellPrices[work++] =
 *       intceil(randfloat(rate_min / RATE_MULTIPLIER, rate_max / RATE_MULTIPLIER) * basePrice);
 *   }
 *
 * Would return the conditional probability given the given_prices, and modify
 * the predicted_prices array.
 * If the given_prices won't match, returns 0.
 */
"""


def generate_individual_random_price(given_prices, predicted_prices, start, length, rate_min, rate_max):
    rate_min *= RATE_MULTIPLIER
    rate_max *= RATE_MULTIPLIER

    buy_price = given_prices[0]
    rate_range = [rate_min, rate_max]
    prob = 1

    for i in range(start, start+length):
    #for (i = start; i < start + length; i++):
        min_pred = get_price(rate_min, buy_price)
        max_pred = get_price(rate_max, buy_price)
        if given_prices[i] is not None:
            if (given_prices[i] < (min_pred - FUDGE_FACTOR)) or (given_prices[i] > (max_pred + FUDGE_FACTOR)):
                # Given price is out of predicted range, so this is the wrong pattern
                return 0
            # TODO: How to deal with probability when there's fudge factor?
            # Clamp the value to be in range now so the probability won't be totally biased to fudged values.
            real_rate_range = rate_range_from_given_and_base(clamp(given_prices[i], min_pred, max_pred), buy_price)
            prob *= range_intersect_length(rate_range, real_rate_range) / range_length(rate_range)
            min_pred = given_prices[i]
            max_pred = given_prices[i]

        predicted_prices.append(Range(min_pred, max_pred))

        #predicted_prices.push({
        #    min: min_pred,
        #    max: max_pred,
        #})
    return prob

"""
/*
 * Probability Density Function of rates.
 * Since the PDF is continuous*, we approximate it by a discrete probability function:
 *   the value in range [(x - 0.5), (x + 0.5)) has a uniform probability
 *   prob[x - value_start];
 *
 * Note that we operate all rate on the (* RATE_MULTIPLIER) scale.
 *
 * (*): Well not really since it only takes values that "float" can represent in some form, but the
 * space is too large to compute directly in JS.
 */
 """


class PDF:
    """
    /*
     * Initialize a PDF in range [a, b], a and b can be non-integer.
     * if uniform is true, then initialize the probability to be uniform, else initialize to a
     * all-zero (invalid) PDF.
     */
    """
    def __init__(self, a, b, uniform = True):
        self.value_start = int(np.round(a))
        self.value_end = int(np.round(b))
        range_ = [a, b]
        total_length = range_length(range_)
        self.prob = []
        for i in range(self.value_end - self.value_start + 1):
            self.prob.append(0)
        if uniform:
            for i in range(len(self.prob)):#(let i = 0; i < this.prob.length; i++) {
                self.prob[i] = range_intersect_length(self.range_of(i), range_) / total_length

    def range_of(self, idx):
        #// TODO: consider doing the "exclusive end" properly.
        return [self.value_start + idx - 0.5, self.value_start + idx + 0.5 - 1e-9]

    def min_value(self):
        return self.value_start - 0.5

    def max_value(self):
        return self.value_end + 0.5 - 1e-9

    def normalize(self):
        total_probability = np.sum(self.prob)#this.prob.reduce((acc, it) => acc + it, 0);
        for i in range(len(self.prob)): #(let i = 0; i < this.prob.length; i++) {
            self.prob[i] /= total_probability

        """
    /*
     * Limit the values to be in the range, and return the probability that the value was in this
     * range.
     */
     """
    def range_limit(self, range_: typing.List):
        start = range_[0]
        end = range_[1]
        #let [start, end] = range;
        start = max(start, self.min_value())
        end = min(end, self.max_value())
        if (start >= end):
            # Set this to invalid values
            self.value_start = 0
            self.value_end = 0
            self.prob = []
            return 0

        prob = 0
        start_idx = int(np.round(start)) - self.value_start
        end_idx = int(np.round(end)) - self.value_start
        for i in range(start_idx, end_idx):
            bucket_prob = self.prob[i] * range_intersect_length(self.range_of(i), range_)
            self.prob[i] = bucket_prob
            prob += bucket_prob

        self.prob = self.prob[start_idx: end_idx+1]#self.prob.slice(start_idx, end_idx + 1)
        self.value_start = int(np.round(start))
        self.value_end = int(np.round(end))
        self.normalize()
        return prob

        # Subtract the PDF by a uniform distribution in [rate_decay_min, rate_decay_max]
        # For simplicity, we assume that rate_decay_min and rate_decay_max are both integers.
    def decay(self, rate_decay_min, rate_decay_max):
        rate_decay_min = int(rate_decay_min)
        rate_decay_max = int(rate_decay_max)
        ret = PDF(self.min_value() - rate_decay_max, self.max_value() - rate_decay_min, False)
        """
        // O(n^2) naive algorithm for reference, which would be too slow.
        for (let i = this.value_start; i <= this.value_end; i++) {
            const unit_prob = this.prob[i - this.value_start] / (rate_decay_max - rate_decay_min) / 2;
            for (let j = rate_decay_min; j < rate_decay_max; j++) {
                // ([i - 0.5, i + 0.5] uniform) - ([j, j + 1] uniform)
                // -> [i - j - 1.5, i + 0.5 - j] with a triangular PDF
                // -> approximate by
                //        [i - j - 1.5, i - j - 0.5] uniform &
                //        [i - j - 0.5, i - j + 0.5] uniform
                ret.prob[i - j - 1 - ret.value_start] += unit_prob; // Part A
                ret.prob[i - j - ret.value_start] += unit_prob; // Part B
            }
        }
        """
        #Transform to "CDF"
        for i in range(1, len(self.prob)):#(let i = 1; i < this.prob.length; i++) {
            self.prob[i] += self.prob[i - 1]
        #// Return this.prob[l - this.value_start] + ... + this.prob[r - 1 - this.value_start];
        #// This assume that this.prob is already transformed to "CDF".
        
        def sum_(l_, r_):
            l_ -= self.value_start
            r_ -= self.value_start
            if l_ < 0:
                l_ = 0
            if r_ > len(self.prob):
                r_ = len(self.prob)
            if l_ == 0:
                return self.prob[r_ - 1]
            else:
                return self.prob[r_ - 1] - self.prob[l_ - 1]

        for x in range(len(ret.prob)):#(let x = 0; x < ret.prob.length; x++) {
            #// i - j - 1 - ret.value_start == x    (Part A)
            #// -> i = x + j + 1 + ret.value_start, j in [rate_decay_min, rate_decay_max)
            ret.prob[x] = sum_(x + rate_decay_min + 1 + ret.value_start, x + rate_decay_max + 1 + ret.value_start)

            #// i - j - ret.value_start == x    (Part B)
            #// -> i = x + j + ret.value_start, j in [rate_decay_min, rate_decay_max)
            ret.prob[x] += sum_(x + rate_decay_min + ret.value_start, x + rate_decay_max + ret.value_start)

        self.prob = ret.prob
        self.value_start = ret.value_start
        self.value_end = ret.value_end
        self.normalize()

"""
/*
 * This corresponds to the code:
 *   rate = randfloat(start_rate_min, start_rate_max);
 *   for (int i = start; i < start + length; i++)
 *   {
 *     sellPrices[work++] = intceil(rate * basePrice);
 *     rate -= randfloat(rate_decay_min, rate_decay_max);
 *   }
 *
 * Would return the conditional probability given the given_prices, and modify
 * the predicted_prices array.
 * If the given_prices won't match, returns 0.
 */
"""


def generate_decreasing_random_price(given_prices, predicted_prices, start, length, start_rate_min, start_rate_max, rate_decay_min, rate_decay_max):
    start_rate_min *= RATE_MULTIPLIER
    start_rate_max *= RATE_MULTIPLIER
    rate_decay_min *= RATE_MULTIPLIER
    rate_decay_max *= RATE_MULTIPLIER

    buy_price = given_prices[0]
    rate_pdf = PDF(start_rate_min, start_rate_max)#rate_pdf = new PDF(start_rate_min, start_rate_max)
    prob = 1

    for i in range(start, start+length):
        min_pred = get_price(rate_pdf.min_value(), buy_price)
        max_pred = get_price(rate_pdf.max_value(), buy_price)
        if (given_prices[i] is not None):
            if (given_prices[i] < min_pred - FUDGE_FACTOR or given_prices[i] > max_pred + FUDGE_FACTOR):
                # Given price is out of predicted range, so this is the wrong pattern
                return 0
            # TODO: How to deal with probability when there's fudge factor?
            # Clamp the value to be in range now so the probability won't be totally biased to fudged values.
            real_rate_range = rate_range_from_given_and_base(clamp(given_prices[i], min_pred, max_pred), buy_price)
            prob *= rate_pdf.range_limit(real_rate_range)
            if prob == 0:
                return 0
            min_pred = given_prices[i]
            max_pred = given_prices[i]

        predicted_prices.append(Range(min_pred, max_pred))
        #predicted_prices.push({
        #    min: min_pred,
        #    max: max_pred,
        #})

        rate_pdf.decay(rate_decay_min, rate_decay_max)
    return prob


"""
/*
 * This corresponds to the code:
 *   rate = randfloat(rate_min, rate_max);
 *   sellPrices[work++] = intceil(randfloat(rate_min, rate) * basePrice) - 1;
 *   sellPrices[work++] = intceil(rate * basePrice);
 *   sellPrices[work++] = intceil(randfloat(rate_min, rate) * basePrice) - 1;
 *
 * Would return the conditional probability given the given_prices, and modify
 * the predicted_prices array.
 * If the given_prices won't match, returns 0.
 */
 """


def generate_peak_price(given_prices: typing.List, predicted_prices, start, rate_min, rate_max):
    rate_min *= RATE_MULTIPLIER
    rate_max *= RATE_MULTIPLIER

    buy_price = given_prices[0]
    prob = 1
    rate_range = [rate_min, rate_max]

    #Calculate the probability first.
    #Prob(middle_price)
    middle_price = given_prices[start + 1]
    if (middle_price is not None):
        min_pred = get_price(rate_min, buy_price)
        max_pred = get_price(rate_max, buy_price)
        if (middle_price < min_pred - FUDGE_FACTOR) or (middle_price > max_pred + FUDGE_FACTOR):
            # Given price is out of predicted range, so this is the wrong pattern
            return 0
        # TODO: How to deal with probability when there's fudge factor?
        # Clamp the value to be in range now so the probability won't be totally biased to fudged values.
        real_rate_range = rate_range_from_given_and_base(clamp(middle_price, min_pred, max_pred), buy_price)
        prob *= range_intersect_length(rate_range, real_rate_range) / range_length(rate_range)
        if prob == 0:
            return 0

        rate_range = range_intersect(rate_range, real_rate_range)

    left_price = given_prices[start]
    right_price = given_prices[start + 2]
    # Prob(left_price | middle_price), Prob(right_price | middle_price)
    #
    # A = rate_range[0], B = rate_range[1], C = rate_min, X = rate, Y = randfloat(rate_min, rate)
    # rate = randfloat(A, B); sellPrices[work++] = intceil(randfloat(C, rate) * basePrice) - 1;
    #
    # => X->U(A,B), Y->U(C,X), Y-C->U(0,X-C), Y-C->U(0,1)*(X-C), Y-C->U(0,1)*U(A-C,B-C),
    # let Z=Y-C,    Z1=A-C, Z2=B-C, Z->U(0,1)*U(Z1,Z2)
    # Prob(Z<=t) = integral_{x=0}^{1} [min(t/x,Z2)-min(t/x,Z1)]/ (Z2-Z1)
    # let F(t, ZZ) = integral_{x=0}^{1} min(t/x, ZZ)
    #        1. if ZZ < t, then min(t/x, ZZ) = ZZ -> F(t, ZZ) = ZZ
    #        2. if ZZ >= t, then F(t, ZZ) = integral_{x=0}^{t/ZZ} ZZ + integral_{x=t/ZZ}^{1} t/x
    #                                                                 = t - t log(t/ZZ)
    # Prob(Z<=t) = (F(t, Z2) - F(t, Z1)) / (Z2 - Z1)
    # Prob(Y<=t) = Prob(Z>=t-C)
    for price in [left_price, right_price]:
        if price is None:
            continue
        min_pred = get_price(rate_min, buy_price) - 1
        max_pred = get_price(rate_range[1], buy_price) - 1
        if (price < min_pred - FUDGE_FACTOR) or (price > max_pred + FUDGE_FACTOR):
            # Given price is out of predicted range, so this is the wrong pattern
            return 0
        # TODO: How to deal with probability when there's fudge factor?
        # Clamp the value to be in range now so the probability won't be totally biased to fudged values.
        rate2_range = rate_range_from_given_and_base(clamp(price, min_pred, max_pred)+ 1, buy_price)

        def F(t, ZZ):
            if t <= 0:
                return 0
            if ZZ < t:
                return ZZ
            else:
                return t - t * (np.log(t) - np.log(ZZ))
        """
        F = (t, ZZ) => {
            if (t <= 0) {
                return 0;
            }
            return ZZ < t ? ZZ : t - t * (Math.log(t) - Math.log(ZZ));
        };
        """

        A = rate_range[0]
        B = rate_range[1]
        C = rate_min
        Z1 = A - C
        Z2 = B - C

        def PY(t):
            return (F(t - C, Z2) - F(t - C, Z1)) / (Z2 - Z1)
        #const PY = (t) => (F(t - C, Z2) - F(t - C, Z1)) / (Z2 - Z1);
    
        prob *= PY(rate2_range[1]) - PY(rate2_range[0])
        if prob == 0:
            return 0

    # * Then generate the real predicted range.
    # We're doing things in different order then how we calculate probability,
    # since forward prediction is more useful here.
    #
    # Main spike 1
    min_pred = get_price(rate_min, buy_price) - 1
    max_pred = get_price(rate_max, buy_price) - 1
    if given_prices[start] is not None:
        min_pred = given_prices[start]
        max_pred = given_prices[start]

    predicted_prices.append(Range(min_pred, max_pred))
    #predicted_prices.push({
    #    min: min_pred,
    #    max: max_pred,
    #})

    #// Main spike 2
    min_pred = predicted_prices[start].min
    max_pred = get_price(rate_max, buy_price)
    if given_prices[start + 1] is not None:
        min_pred = given_prices[start + 1]
        max_pred = given_prices[start + 1]
    predicted_prices.append(Range(min_pred, max_pred))
    #predicted_prices.push({
    #    min: min_pred,
    #    max: max_pred,
    #})

    #// Main spike 3
    min_pred = get_price(rate_min, buy_price) - 1
    max_pred = predicted_prices[start + 1].max - 1
    if given_prices[start + 2] is not None:
        min_pred = given_prices[start + 2]
        max_pred = given_prices[start + 2]
    predicted_prices.append(Range(min_pred, max_pred))
    #predicted_prices.push({
    #    min: min_pred,
    #    max: max_pred,
    #})

    return prob


def generate_pattern_0_with_lengths(given_prices, high_phase_1_len, dec_phase_1_len, high_phase_2_len, dec_phase_2_len, high_phase_3_len):  # function*
    """
    /*
            // PATTERN 0: high, decreasing, high, decreasing, high
            work = 2;
            // high phase 1
            for (int i = 0; i < hiPhaseLen1; i++)
            {
                sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
            }
            // decreasing phase 1
            rate = randfloat(0.8, 0.6);
            for (int i = 0; i < decPhaseLen1; i++)
            {
                sellPrices[work++] = intceil(rate * basePrice);
                rate -= 0.04;
                rate -= randfloat(0, 0.06);
            }
            // high phase 2
            for (int i = 0; i < (hiPhaseLen2and3 - hiPhaseLen3); i++)
            {
                sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
            }
            // decreasing phase 2
            rate = randfloat(0.8, 0.6);
            for (int i = 0; i < decPhaseLen2; i++)
            {
                sellPrices[work++] = intceil(rate * basePrice);
                rate -= 0.04;
                rate -= randfloat(0, 0.06);
            }
            // high phase 3
            for (int i = 0; i < hiPhaseLen3; i++)
            {
                sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
            }
    */
    """
    buy_price = given_prices[0]

    predicted_prices = [Range(buy_price, buy_price), Range(buy_price, buy_price)]

    #predicted_prices = [
    #    {
    #        min: buy_price,
    #        max: buy_price,
    #    },
    #    {
    #        min: buy_price,
    #        max: buy_price,
    #    },
    #]
    probability = 1

    #// High Phase 1
    probability *= generate_individual_random_price(given_prices, predicted_prices, 2, high_phase_1_len, 0.9, 1.4)
    if probability == 0:
        return

    #// Dec Phase 1
    probability *= generate_decreasing_random_price(given_prices, predicted_prices, 2 + high_phase_1_len, dec_phase_1_len,0.6, 0.8, 0.04, 0.1)
    if probability == 0:
        return

    #// High Phase 2
    probability *= generate_individual_random_price(given_prices, predicted_prices, 2 + high_phase_1_len + dec_phase_1_len, high_phase_2_len, 0.9, 1.4)
    if probability == 0:
        return

    #// Dec Phase 2
    probability *= generate_decreasing_random_price(given_prices, predicted_prices, 2 + high_phase_1_len + dec_phase_1_len + high_phase_2_len, dec_phase_2_len, 0.6, 0.8, 0.04, 0.1)
    if probability == 0:
        return

    #// High Phase 3
    if (2 + high_phase_1_len + dec_phase_1_len + high_phase_2_len + dec_phase_2_len + high_phase_3_len) != 14:
        raise RuntimeError("Phase lengths don't add up")

    prev_length = 2 + high_phase_1_len + dec_phase_1_len + high_phase_2_len + dec_phase_2_len
    probability *= generate_individual_random_price(given_prices, predicted_prices, prev_length, 14 - prev_length, 0.9, 1.4)
    if probability == 0:
        return

    yield Prediction('fluctuating', 0, predicted_prices, probability, 0, 0, 0)

    #yield {
    #    pattern_description: "patterns.fluctuating",
    #    pattern_number: 0,
    #    prices: predicted_prices,
    #    probability,
    #};


#function*
def generate_pattern_0(given_prices):
    """
    /*
            decPhaseLen1 = randbool() ? 3 : 2;
            decPhaseLen2 = 5 - decPhaseLen1;
            hiPhaseLen1 = randint(0, 6);
            hiPhaseLen2and3 = 7 - hiPhaseLen1;
            hiPhaseLen3 = randint(0, hiPhaseLen2and3 - 1);
    */
    """
    for dec_phase_1_len in range(2, 4):
        for high_phase_1_len in range(7):
            for high_phase_3_len in range(7 - high_phase_1_len - 1 + 1):
                pattern_0_with_lengths = generate_pattern_0_with_lengths(given_prices, high_phase_1_len, dec_phase_1_len, (7 - high_phase_1_len - high_phase_3_len), (5 - dec_phase_1_len), high_phase_3_len)
                p = 1 / (4 - 2) / 7 / (7 - high_phase_1_len)
                yield from multiply_generator_probability(pattern_0_with_lengths, p)
                #generate_pattern_0_with_lengths(given_prices, high_phase_1_len, dec_phase_1_len, 7 - high_phase_1_len - high_phase_3_len, 5 - dec_phase_1_len, high_phase_3_len), 1 / (4 - 2) / 7 / (7 - high_phase_1_len))
                #yield pattern_0_with_lengths


  #for (var dec_phase_1_len = 2; dec_phase_1_len < 4; dec_phase_1_len++) {
  #  for (var high_phase_1_len = 0; high_phase_1_len < 7; high_phase_1_len++) {
  #    for (var high_phase_3_len = 0; high_phase_3_len < (7 - high_phase_1_len - 1 + 1); high_phase_3_len++) {
  #      yield* multiply_generator_probability(
  #        generate_pattern_0_with_lengths(given_prices, high_phase_1_len, dec_phase_1_len, 7 - high_phase_1_len - high_phase_3_len, 5 - dec_phase_1_len, high_phase_3_len),
  #        1 / (4 - 2) / 7 / (7 - high_phase_1_len));

#function*
def generate_pattern_1_with_peak(given_prices, peak_start):
    """
    /*
        // PATTERN 1: decreasing middle, high spike, random low
        peakStart = randint(3, 9);
        rate = randfloat(0.9, 0.85);
        for (work = 2; work < peakStart; work++)
        {
            sellPrices[work] = intceil(rate * basePrice);
            rate -= 0.03;
            rate -= randfloat(0, 0.02);
        }
        sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
        sellPrices[work++] = intceil(randfloat(1.4, 2.0) * basePrice);
        sellPrices[work++] = intceil(randfloat(2.0, 6.0) * basePrice);
        sellPrices[work++] = intceil(randfloat(1.4, 2.0) * basePrice);
        sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
        for (; work < 14; work++)
        {
            sellPrices[work] = intceil(randfloat(0.4, 0.9) * basePrice);
        }
    */
    """
    buy_price = given_prices[0]
    predicted_prices = [Range(buy_price, buy_price), Range(buy_price, buy_price)]
    probability = 1

    probability *= generate_decreasing_random_price(given_prices, predicted_prices, 2, peak_start - 2, 0.85, 0.9, 0.03, 0.05)
    if probability == 0:
        return

    #// Now each day is independent of next
    min_randoms = [0.9, 1.4, 2.0, 1.4, 0.9, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]
    max_randoms = [1.4, 2.0, 6.0, 2.0, 1.4, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
    for i in range(peak_start, 14):#for (let i = peak_start; i < 14; i++) {
        probability *= generate_individual_random_price(given_prices, predicted_prices, i, 1, min_randoms[i - peak_start], max_randoms[i - peak_start])
        if probability == 0:
            return

    yield Prediction('large spike', 1, predicted_prices, probability, 0, 0, 0)
    #yield {
    #    pattern_description: i18next.t("patterns.large-spike"),
    #    pattern_number: 1,
    #    prices: predicted_prices,
    #    probability,
    #};

#function*
def generate_pattern_1(given_prices):
    for peak_start in range(3, 10):#for (var peak_start = 3; peak_start < 10; peak_start++) {
        yield from multiply_generator_probability(generate_pattern_1_with_peak(given_prices, peak_start), 1 / (10 - 3))

#function*
def generate_pattern_2(given_prices):
    """
    /*
            // PATTERN 2: consistently decreasing
            rate = 0.9;
            rate -= randfloat(0, 0.05);
            for (work = 2; work < 14; work++)
            {
                sellPrices[work] = intceil(rate * basePrice);
                rate -= 0.03;
                rate -= randfloat(0, 0.02);
            }
            break;
    */
    """
    buy_price = given_prices[0]
    predicted_prices = [ Range(buy_price, buy_price), Range(buy_price, buy_price)]

    probability = 1

    probability *= generate_decreasing_random_price(given_prices, predicted_prices, 2, 14 - 2, 0.85, 0.9, 0.03, 0.05)
    if probability == 0:
        return

    yield Prediction('decreasing', 2, predicted_prices, probability, 0, 0, 0)
    #yield {
    #    pattern_description: i18next.t("patterns.decreasing"),
    #    pattern_number: 2,
    #    prices: predicted_prices,
    #    probability,
    #};


#function*
def generate_pattern_3_with_peak(given_prices, peak_start):
    """
    /*
        // PATTERN 3: decreasing, spike, decreasing
        peakStart = randint(2, 9);
        // decreasing phase before the peak
        rate = randfloat(0.9, 0.4);
        for (work = 2; work < peakStart; work++)
        {
            sellPrices[work] = intceil(rate * basePrice);
            rate -= 0.03;
            rate -= randfloat(0, 0.02);
        }
        sellPrices[work++] = intceil(randfloat(0.9, 1.4) * (float)basePrice);
        sellPrices[work++] = intceil(randfloat(0.9, 1.4) * basePrice);
        rate = randfloat(1.4, 2.0);
        sellPrices[work++] = intceil(randfloat(1.4, rate) * basePrice) - 1;
        sellPrices[work++] = intceil(rate * basePrice);
        sellPrices[work++] = intceil(randfloat(1.4, rate) * basePrice) - 1;
        // decreasing phase after the peak
        if (work < 14)
        {
            rate = randfloat(0.9, 0.4);
            for (; work < 14; work++)
            {
                sellPrices[work] = intceil(rate * basePrice);
                rate -= 0.03;
                rate -= randfloat(0, 0.02);
            }
        }
    */
    """
    buy_price = given_prices[0]
    predicted_prices = [Range(buy_price, buy_price), Range(buy_price, buy_price)]

    probability = 1

    probability *= generate_decreasing_random_price(given_prices, predicted_prices, 2, peak_start - 2, 0.4, 0.9, 0.03, 0.05)
    if probability == 0:
        return

    #// The peak
    probability *= generate_individual_random_price(given_prices, predicted_prices, peak_start, 2, 0.9, 1.4)
    if probability == 0:
        return

    probability *= generate_peak_price(given_prices, predicted_prices, peak_start + 2, 1.4, 2.0)
    if probability == 0:
        return

    if (peak_start + 5) < 14:
        probability *= generate_decreasing_random_price(given_prices, predicted_prices, peak_start + 5, 14 - (peak_start + 5), 0.4, 0.9, 0.03, 0.05)
        if probability == 0:
            return

    yield Prediction('small spike', 3, predicted_prices, probability, 0, 0, 0)

    #yield {
    #    pattern_description: i18next.t("patterns.small-spike"),
    #    pattern_number: 3,
    #    prices: predicted_prices,
    #    probability,
    #};

#function*
def generate_pattern_3(given_prices):
    for peak_start in range(2, 10):#for (let peak_start = 2; peak_start < 10; peak_start++) {
        #yield* multiply_generator_probability(generate_pattern_3_with_peak(given_prices, peak_start), 1 / (10 - 2))
        p = 1 / (10 - 2)
        yield from multiply_generator_probability(generate_pattern_3_with_peak(given_prices, peak_start), p)

def get_transition_probability(previous_pattern: typing.Optional[int]):
    #if (typeof previous_pattern === 'undefined' || Number.isNaN(previous_pattern) || previous_pattern === null || previous_pattern < 0 || previous_pattern > 3) {
    if (previous_pattern is None) or (previous_pattern < 0) or (previous_pattern > 3):
        #// TODO: Fill the steady state pattern (https://github.com/mikebryant/ac-nh-turnip-prices/pull/90) here.
        return [0.346278, 0.247363, 0.147607, 0.258752]

    return PROBABILITY_MATRIX[previous_pattern]

#function*
def generate_all_patterns(sell_prices, previous_pattern):
    generate_pattern_fns = [generate_pattern_0, generate_pattern_1, generate_pattern_2, generate_pattern_3]
    transition_probability = get_transition_probability(previous_pattern)

    for i in range(4):
        yield from multiply_generator_probability(generate_pattern_fns[i](sell_prices), transition_probability[i])

    #for (let i = 0; i < 4; i++) {
    #    yield* multiply_generator_probability(generate_pattern_fns[i](sell_prices), transition_probability[i]);
    #}

#function*
def generate_possibilities(sell_prices, first_buy: bool, previous_pattern: typing.Optional[int]):
    if first_buy or (sell_prices[0] is None):
        for buy_price in range(90, 111):#for (var buy_price = 90; buy_price <= 110; buy_price++) {
            sell_prices[0] = sell_prices[1] = buy_price
            if first_buy:
                yield from generate_pattern_3(sell_prices)
            else:
                #// All buy prices are equal probability and we're at the outmost layer,
                #// so don't need to multiply_generator_probability here.
                yield from generate_all_patterns(sell_prices, previous_pattern)
    else:
        yield from generate_all_patterns(sell_prices, previous_pattern)


def analyze_possibilities(sell_prices, first_buy, previous_pattern):
    generated_p = generate_possibilities(sell_prices, first_buy, previous_pattern)
    generated_possibilities = []
    for prediction in generated_p:
        generated_possibilities.append(prediction)
    #generated_possibilities = Array.from(generate_possibilities(sell_prices, first_buy, previous_pattern));
    #console.log(generated_possibilities);

    total_probability = 0
    for prediction in generated_possibilities:
        total_probability += prediction.probability

    #const total_probability = generated_possibilities.reduce((acc, it) => acc + it.probability, 0);

    for idx in range(len(generated_possibilities)):
        generated_possibilities[idx].probability /= total_probability

    #for (const it of generated_possibilities) {
    #    it.probability /= total_probability;
    #}

    for idx in range(len(generated_possibilities)):
        poss = generated_possibilities[idx]
        weekMins = []
        weekMaxes = []
        for day in poss.prices[2:]:
            if day.min != day.max:
                weekMins.append(day.min)
                weekMaxes.append(day.max)
            else:
                weekMins = []
                weekMaxes = []
        if (len(weekMins) == 0) and (len(weekMaxes) == 0):
            weekMins.append(poss.prices[len(poss.prices) - 1].min)
            weekMaxes.append(poss.prices[len(poss.prices) - 1].max)
    
        generated_possibilities[idx].weekGuaranteedMinimum = max(weekMins)
        generated_possibilities[idx].weekMax = max(weekMaxes)

    #for (let poss of generated_possibilities) {
    #    var weekMins = [];
    #    var weekMaxes = [];
    #    for (let day of poss.prices.slice(2)) {
    #        // Check for a future date by checking for a range of prices
    #        if(day.min !== day.max){
    #            weekMins.push(day.min);
    #            weekMaxes.push(day.max);
    #        } else {
    #            // If we find a set price after one or more ranged prices, the user has missed a day. Discard that data and start again.
    #            weekMins = [];
    #            weekMaxes = [];
    #        }
    #    }
    #    if (!weekMins.length && !weekMaxes.length) {
    #        weekMins.push(poss.prices[poss.prices.length -1].min);
    #        weekMaxes.push(poss.prices[poss.prices.length -1].max);
    #    }
    #    poss.weekGuaranteedMinimum = Math.max(...weekMins);
    #    poss.weekMax = Math.max(...weekMaxes);
    #}

    category_totals = {}
    for i in [0, 1, 2, 3]:
        category_totals[i] = 0
        for poss in generated_possibilities:
            if poss.pattern_number == i:
                category_totals[i] += poss.probability


    #category_totals = {}
    #for (let i of [0, 1, 2, 3]) {
    #    category_totals[i] = generated_possibilities
    #        .filter(value => value.pattern_number == i)
    #        .map(value => value.probability)
    #        .reduce((previous, current) => previous + current, 0);
    #}

    for idx in range(len(generated_possibilities)):
        generated_possibilities[idx].category_total_probability = category_totals[generated_possibilities[idx].pattern_number]

    #for (let pos of generated_possibilities) {
    #    pos.category_total_probability = category_totals[pos.pattern_number];
    #}

    #def sorter(a, b):
    #    return (b.category_total_probability - a.category_total_probability) or (b.probability - a.probability)
    def sorter(a):
        return a.probability
    generated_possibilities.sort(key=sorter)


    #generated_possibilities.sort((a, b) => {
    #  return b.category_total_probability - a.category_total_probability || b.probability - a.probability;
    #});

    global_min_max = []
    for day in range(14):
        prices = Range(999, 0)
        for poss in generated_possibilities:
            if poss.prices[day].min < prices.min:
                prices.min = poss.prices[day].min
            if poss.prices[day].max > prices.max:
                prices.max = poss.prices[day].max
        global_min_max.append(prices)



    #global_min_max = [];
    #for (var day = 0; day < 14; day++) {
    #    prices = {
    #        min: 999,
    #        max: 0,
    #    }
    #    for (let poss of generated_possibilities) {
    #        if (poss.prices[day].min < prices.min) {
    #            prices.min = poss.prices[day].min;
    #        }
    #        if (poss.prices[day].max > prices.max) {
    #            prices.max = poss.prices[day].max;
    #        }
    #    }
    #    global_min_max.push(prices);
    #}

    weekGarunteedMin = 999
    weekMax = 0
    for poss in generated_possibilities:
        if poss.weekGuaranteedMinimum < weekGarunteedMin:
            weekGarunteedMin = poss.weekGuaranteedMinimum
        if poss.weekMax > weekMax:
            weekMax = poss.weekMax

    generated_possibilities.insert(0, Prediction('all', 4, global_min_max, 0, weekGarunteedMin, weekMax, 0))

    #generated_possibilities.unshift({
    #    pattern_description: i18next.t("patterns.all"),
    #    pattern_number: 4,
    #    prices: global_min_max,
    #    weekGuaranteedMinimum: Math.min(...generated_possibilities.map(poss => poss.weekGuaranteedMinimum)),
    #    weekMax: Math.max(...generated_possibilities.map(poss => poss.weekMax))
    #});

    return generated_possibilities

