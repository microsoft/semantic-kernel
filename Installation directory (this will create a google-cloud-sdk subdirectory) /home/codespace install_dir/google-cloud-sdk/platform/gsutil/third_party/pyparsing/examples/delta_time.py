# deltaTime.py
#
# Parser to convert a conversational time reference such as "in a minute" or
# "noon tomorrow" and convert it to a Python datetime. The returned
# ParseResults object contains
#   - original - the original time expression string
#   - computed_dt - the Python datetime representing the computed time
#   - relative_to - the reference "now" time
#   - time_offset - the difference between the reference time and the computed time
#
# BNF:
#     time_and_day ::= time_reference [day_reference] | day_reference 'at' absolute_time_of_day
#     day_reference ::= absolute_day_reference | relative_day_reference
#     absolute_day_reference ::= 'today' | 'tomorrow' | 'yesterday' | ('next' | 'last') weekday_name
#     relative_day_reference ::= 'in' qty day_units
#                                | qty day_units 'ago'
#                                | 'qty day_units ('from' | 'before' | 'after') absolute_day_reference
#     day_units ::= 'days' | 'weeks'
#
#     time_reference ::= absolute_time_of_day | relative_time_reference
#     relative_time_reference ::= qty time_units ('from' | 'before' | 'after') absolute_time_of_day
#                                 | qty time_units 'ago'
#                                 | 'in' qty time_units
#     time_units ::= 'hours' | 'minutes' | 'seconds'
#     absolute_time_of_day ::= 'noon' | 'midnight' | 'now' | absolute_time
#     absolute_time ::=  24hour_time | hour ("o'clock" | ':' minute) ('AM'|'PM')
#
#     qty ::= integer | integer_words | 'a couple of' | 'a' | 'the'
#
# Copyright 2010, 2019 by Paul McGuire
#

from datetime import datetime, time, timedelta
import pyparsing as pp
import calendar

__all__ = ["time_expression"]

# basic grammar definitions
def make_integer_word_expr(int_name, int_value):
    return pp.CaselessKeyword(int_name).addParseAction(pp.replaceWith(int_value))
integer_word = pp.MatchFirst(make_integer_word_expr(int_str, int_value)
                     for int_value, int_str
                     in enumerate("one two three four five six seven eight nine ten"
                                  " eleven twelve thirteen fourteen fifteen sixteen"
                                  " seventeen eighteen nineteen twenty".split(), start=1))
integer = pp.pyparsing_common.integer | integer_word

CK = pp.CaselessKeyword
CL = pp.CaselessLiteral
today, tomorrow, yesterday, noon, midnight, now = map(CK, "today tomorrow yesterday noon midnight now".split())
def plural(s):
    return CK(s) | CK(s + 's').addParseAction(pp.replaceWith(s))
week, day, hour, minute, second = map(plural, "week day hour minute second".split())
time_units = hour | minute | second
any_time_units = week | day | time_units

am = CL("am")
pm = CL("pm")
COLON = pp.Suppress(':')

in_ = CK("in").setParseAction(pp.replaceWith(1))
from_ = CK("from").setParseAction(pp.replaceWith(1))
before = CK("before").setParseAction(pp.replaceWith(-1))
after = CK("after").setParseAction(pp.replaceWith(1))
ago = CK("ago").setParseAction(pp.replaceWith(-1))
next_ = CK("next").setParseAction(pp.replaceWith(1))
last_ = CK("last").setParseAction(pp.replaceWith(-1))
at_ = CK("at")
on_ = CK("on")

couple = (pp.Optional(CK("a")) + CK("couple") + pp.Optional(CK("of"))).setParseAction(pp.replaceWith(2))
a_qty = (CK("a") | CK("an")).setParseAction(pp.replaceWith(1))
the_qty = CK("the").setParseAction(pp.replaceWith(1))
qty = pp.ungroup(integer | couple | a_qty | the_qty).setName("qty")
time_ref_present = pp.Empty().addParseAction(pp.replaceWith(True))('time_ref_present')

def fill_24hr_time_fields(t):
    t['HH'] = t[0]
    t['MM'] = t[1]
    t['SS'] = 0
    t['ampm'] = ('am','pm')[t.HH >= 12]

def fill_default_time_fields(t):
    for fld in 'HH MM SS'.split():
        if fld not in t:
            t[fld] = 0

weekday_name_list = list(calendar.day_name)
weekday_name = pp.oneOf(weekday_name_list)

_24hour_time = (~(integer + any_time_units)
                + pp.Word(pp.nums, exact=4).addParseAction(lambda t: [int(t[0][:2]),int(t[0][2:])],
                                                           fill_24hr_time_fields)
                )
_24hour_time.setName("0000 time")
ampm = am | pm
timespec = (integer("HH")
                    + pp.Optional(CK("o'clock")
                       |
                       COLON + integer("MM")
                       + pp.Optional(COLON + integer("SS"))
                       )
                   + (am | pm)("ampm")
                 ).addParseAction(fill_default_time_fields)
absolute_time = _24hour_time | timespec

absolute_time_of_day = noon | midnight | now | absolute_time

def add_computed_time(t):
    if t[0] in 'now noon midnight'.split():
        t['computed_time'] = {'now': datetime.now().time().replace(microsecond=0),
                              'noon': time(hour=12),
                              'midnight': time()}[t[0]]
    else:
        t['HH'] = {'am': int(t['HH']) % 12,
                   'pm': int(t['HH']) % 12 + 12}[t.ampm]
        t['computed_time'] = time(hour=t.HH, minute=t.MM, second=t.SS)

absolute_time_of_day.addParseAction(add_computed_time)


#     relative_time_reference ::= qty time_units ('from' | 'before' | 'after') absolute_time_of_day
#                                 | qty time_units 'ago'
#                                 | 'in' qty time_units
time_units = hour | minute | second
relative_time_reference = (qty('qty') + time_units('units') + ago('dir')
                           | qty('qty') + time_units('units')
                             + (from_ | before | after)('dir')
                             + pp.Group(absolute_time_of_day)('ref_time')
                           | in_('dir') + qty('qty') + time_units('units')
                           )

def compute_relative_time(t):
    if 'ref_time' not in t:
        t['ref_time'] = datetime.now().time().replace(microsecond=0)
    else:
        t['ref_time'] = t.ref_time.computed_time
    delta_seconds = {'hour': 3600,
                     'minute': 60,
                     'second': 1}[t.units] * t.qty
    t['time_delta'] = timedelta(seconds=t.dir * delta_seconds)

relative_time_reference.addParseAction(compute_relative_time)

time_reference = absolute_time_of_day | relative_time_reference
def add_default_time_ref_fields(t):
    if 'time_delta' not in t:
        t['time_delta'] = timedelta()
time_reference.addParseAction(add_default_time_ref_fields)

#     absolute_day_reference ::= 'today' | 'tomorrow' | 'yesterday' | ('next' | 'last') weekday_name
#     day_units ::= 'days' | 'weeks'

day_units = day | week
weekday_reference = pp.Optional(next_ | last_, 1)('dir') + weekday_name('day_name')

def convert_abs_day_reference_to_date(t):
    now = datetime.now().replace(microsecond=0)

    # handle day reference by weekday name
    if 'day_name' in t:
        todaynum = now.weekday()
        daynames = [n.lower() for n in weekday_name_list]
        nameddaynum = daynames.index(t.day_name.lower())
        # compute difference in days - if current weekday name is referenced, then
        # computed 0 offset is changed to 7
        if t.dir > 0:
            daydiff = (nameddaynum + 7 - todaynum) % 7 or 7
        else:
            daydiff = -((todaynum + 7 - nameddaynum) % 7 or 7)
        t["abs_date"] = datetime(now.year, now.month, now.day) + timedelta(daydiff)
    else:
        name = t[0]
        t["abs_date"] = {
            "now"       : now,
            "today"     : datetime(now.year, now.month, now.day),
            "yesterday" : datetime(now.year, now.month, now.day) + timedelta(days=-1),
            "tomorrow"  : datetime(now.year, now.month, now.day) + timedelta(days=+1),
            }[name]

absolute_day_reference = today | tomorrow | yesterday | now + time_ref_present | weekday_reference
absolute_day_reference.addParseAction(convert_abs_day_reference_to_date)


#     relative_day_reference ::=  'in' qty day_units
#                                   | qty day_units 'ago'
#                                   | 'qty day_units ('from' | 'before' | 'after') absolute_day_reference
relative_day_reference = (in_('dir') + qty('qty') + day_units('units')
                          | qty('qty') + day_units('units') + ago('dir')
                          | qty('qty') + day_units('units') + (from_ | before | after)('dir')
                            + absolute_day_reference('ref_day')
                          )

def compute_relative_date(t):
    now = datetime.now().replace(microsecond=0)
    if 'ref_day' in t:
        t['computed_date'] = t.ref_day
    else:
        t['computed_date'] = now.date()
    day_diff = t.dir * t.qty * {'week': 7, 'day': 1}[t.units]
    t['date_delta'] = timedelta(days=day_diff)
relative_day_reference.addParseAction(compute_relative_date)

# combine expressions for absolute and relative day references
day_reference = relative_day_reference | absolute_day_reference
def add_default_date_fields(t):
    if 'date_delta' not in t:
        t['date_delta'] = timedelta()
day_reference.addParseAction(add_default_date_fields)

# combine date and time expressions into single overall parser
time_and_day = (time_reference + time_ref_present + pp.Optional(pp.Optional(on_) + day_reference)
               | day_reference + pp.Optional(at_ + absolute_time_of_day + time_ref_present))

# parse actions for total time_and_day expression
def save_original_string(s, l, t):
    # save original input string and reference time
    t['original'] = ' '.join(s.strip().split())
    t['relative_to'] = datetime.now().replace(microsecond=0)

def compute_timestamp(t):
    # accumulate values from parsed time and day subexpressions - fill in defaults for omitted parts
    now = datetime.now().replace(microsecond=0)
    if 'computed_time' not in t:
        t['computed_time'] = t.ref_time or now.time()
    if 'abs_date' not in t:
        t['abs_date'] = now

    # roll up all fields and apply any time or day deltas
    t['computed_dt'] = (
        t.abs_date.replace(hour=t.computed_time.hour, minute=t.computed_time.minute, second=t.computed_time.second)
        + (t.time_delta or timedelta(0))
        + (t.date_delta or timedelta(0))
    )

    # if time just given in terms of day expressions, zero out time fields
    if not t.time_ref_present:
        t['computed_dt'] = t.computed_dt.replace(hour=0, minute=0, second=0)

    # add results name compatible with previous version
    t['calculatedTime'] = t.computed_dt

    # add time_offset fields
    t['time_offset'] = t.computed_dt - t.relative_to

def remove_temp_keys(t):
    # strip out keys that are just used internally
    all_keys = list(t.keys())
    for k in all_keys:
        if k not in ('computed_dt', 'original', 'relative_to', 'time_offset', 'calculatedTime'):
            del t[k]

time_and_day.addParseAction(save_original_string, compute_timestamp, remove_temp_keys)


time_expression = time_and_day


if __name__ == "__main__":
    current_time = datetime.now()
    # test grammar
    tests = """\
        today
        tomorrow
        yesterday
        the day before yesterday
        the day after tomorrow
        2 weeks after today
        in a couple of days
        a couple of days from now
        a couple of days from today
        in a day
        3 days ago
        3 days from now
        a day ago
        an hour ago
        in 2 weeks
        in 3 days at 5pm
        now
        10 minutes ago
        10 minutes from now
        in 10 minutes
        in a minute
        in a couple of minutes
        20 seconds ago
        in 30 seconds
        in an hour
        in a couple hours
        in a couple days
        20 seconds before noon
        ten seconds before noon tomorrow
        noon
        midnight
        noon tomorrow
        6am tomorrow
        0800 yesterday
        1700 tomorrow
        12:15 AM today
        3pm 2 days from today
        a week from today
        a week from now
        three weeks ago
        noon next Sunday
        noon Sunday
        noon last Sunday
        2pm next Sunday
        next Sunday at 2pm
        last Sunday at 2pm
        10 seconds ago
        100 seconds ago
        1000 seconds ago
        10000 seconds ago
    """

    time_of_day = timedelta(hours=current_time.hour,
                            minutes=current_time.minute,
                            seconds=current_time.second)
    expected = {
        'now' : timedelta(0),
        "10 seconds ago": timedelta(seconds=-10),
        "100 seconds ago": timedelta(seconds=-100),
        "1000 seconds ago": timedelta(seconds=-1000),
        "10000 seconds ago": timedelta(seconds=-10000),
        '10 minutes ago': timedelta(minutes=-10),
        '10 minutes from now': timedelta(minutes=10),
        'in 10 minutes': timedelta(minutes=10),
        'in a minute': timedelta(minutes=1),
        'in a couple of minutes': timedelta(minutes=2),
        '20 seconds ago': timedelta(seconds=-20),
        'in 30 seconds': timedelta(seconds=30),
        'in an hour': timedelta(hours=1),
        'in a couple hours': timedelta(hours=2),
        'a week from now': timedelta(days=7),
        '3 days from now': timedelta(days=3),
        'a couple of days from now': timedelta(days=2),
        'an hour ago': timedelta(hours=-1),
        'in a couple days': timedelta(days=2) - time_of_day,
        'a week from today': timedelta(days=7) - time_of_day,
        'three weeks ago': timedelta(days=-21) - time_of_day,
        'a day ago': timedelta(days=-1) - time_of_day,
        'in a couple of days': timedelta(days=2) - time_of_day,
        'a couple of days from today': timedelta(days=2) - time_of_day,
        '2 weeks after today': timedelta(days=14) - time_of_day,
        'in 2 weeks': timedelta(days=14) - time_of_day,
        'the day after tomorrow': timedelta(days=2) - time_of_day,
        'tomorrow': timedelta(days=1) - time_of_day,
        'the day before yesterday': timedelta(days=-2) - time_of_day,
        'yesterday': timedelta(days=-1) - time_of_day,
        'today': -time_of_day,
        'midnight': -time_of_day,
        'in a day': timedelta(days=1) - time_of_day,
        '3 days ago': timedelta(days=-3) - time_of_day,
        'noon tomorrow': timedelta(days=1) - time_of_day + timedelta(hours=12),
        '6am tomorrow': timedelta(days=1) - time_of_day + timedelta(hours=6),
        '0800 yesterday': timedelta(days=-1) - time_of_day + timedelta(hours=8),
        '1700 tomorrow':  timedelta(days=1) - time_of_day + timedelta(hours=17),
        '12:15 AM today': -time_of_day + timedelta(minutes=15),
        '3pm 2 days from today': timedelta(days=2) - time_of_day + timedelta(hours=15),
        'ten seconds before noon tomorrow': timedelta(days=1) - time_of_day
                                            + timedelta(hours=12) + timedelta(seconds=-10),
        '20 seconds before noon': -time_of_day + timedelta(hours=12) + timedelta(seconds=-20),
        'in 3 days at 5pm': timedelta(days=3) - time_of_day + timedelta(hours=17),
    }

    def verify_offset(instring, parsed):
        time_epsilon = timedelta(seconds=1)
        if instring in expected:
            # allow up to a second time discrepancy due to test processing time
            if (parsed.time_offset - expected[instring]) <= time_epsilon:
                parsed['verify_offset'] = 'PASS'
            else:
                parsed['verify_offset'] = 'FAIL'

    print("(relative to %s)" % datetime.now())
    time_expression.runTests(tests, postParse=verify_offset)
