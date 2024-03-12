# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from antlr3 import *
from antlr3.compat import set, frozenset


# for convenience in actions
HIDDEN = BaseRecognizer.HIDDEN

# token types
MONTH=27
THURSDAY=23
FOURTH_OR_FIFTH=16
THIRD=13
DECEMBER=39
FROM=41
EVERY=6
WEDNESDAY=22
QUARTER=40
SATURDAY=25
SYNCHRONIZED=9
JANUARY=28
SUNDAY=26
TUESDAY=21
SEPTEMBER=36
UNKNOWN_TOKEN=45
AUGUST=35
JULY=34
MAY=32
FRIDAY=24
DIGITS=8
FEBRUARY=29
TWO_DIGIT_HOUR_TIME=43
OF=4
WS=44
EOF=-1
APRIL=31
COMMA=10
JUNE=33
OCTOBER=37
TIME=5
FIFTH=15
NOVEMBER=38
FIRST=11
DIGIT=7
FOURTH=14
MONDAY=20
HOURS=17
MARCH=30
SECOND=12
MINUTES=18
TO=42
DAY=19


class GrocLexer(Lexer):

    grammarFileName = "borg/borgcron/py/Groc.g"
    antlr_version = version_str_to_tuple("3.1.1")
    antlr_version_str = "3.1.1"

    def __init__(self, input=None, state=None):
        if state is None:
            state = RecognizerSharedState()
        Lexer.__init__(self, input, state)

        self.dfa26 = self.DFA26(
            self, 26,
            eot = self.DFA26_eot,
            eof = self.DFA26_eof,
            min = self.DFA26_min,
            max = self.DFA26_max,
            accept = self.DFA26_accept,
            special = self.DFA26_special,
            transition = self.DFA26_transition
            )






    # $ANTLR start "TIME"
    def mTIME(self, ):

        try:
            _type = TIME
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:228:11: ( ( DIGIT ':' '0' .. '5' DIGIT ) )
            # borg/borgcron/py/Groc.g:228:13: ( DIGIT ':' '0' .. '5' DIGIT )
            pass 
            # borg/borgcron/py/Groc.g:228:13: ( DIGIT ':' '0' .. '5' DIGIT )
            # borg/borgcron/py/Groc.g:228:15: DIGIT ':' '0' .. '5' DIGIT
            pass 
            self.mDIGIT()
            self.match(58)
            self.matchRange(48, 53)
            self.mDIGIT()






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "TIME"



    # $ANTLR start "TWO_DIGIT_HOUR_TIME"
    def mTWO_DIGIT_HOUR_TIME(self, ):

        try:
            _type = TWO_DIGIT_HOUR_TIME
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:230:11: ( ( ( ( '0' DIGIT ) | ( '1' DIGIT ) | ( '2' '0' .. '3' ) ) ':' ( '0' .. '5' DIGIT ) ) )
            # borg/borgcron/py/Groc.g:230:13: ( ( ( '0' DIGIT ) | ( '1' DIGIT ) | ( '2' '0' .. '3' ) ) ':' ( '0' .. '5' DIGIT ) )
            pass 
            # borg/borgcron/py/Groc.g:230:13: ( ( ( '0' DIGIT ) | ( '1' DIGIT ) | ( '2' '0' .. '3' ) ) ':' ( '0' .. '5' DIGIT ) )
            # borg/borgcron/py/Groc.g:230:15: ( ( '0' DIGIT ) | ( '1' DIGIT ) | ( '2' '0' .. '3' ) ) ':' ( '0' .. '5' DIGIT )
            pass 
            # borg/borgcron/py/Groc.g:230:15: ( ( '0' DIGIT ) | ( '1' DIGIT ) | ( '2' '0' .. '3' ) )
            alt1 = 3
            LA1 = self.input.LA(1)
            if LA1 == 48:
                alt1 = 1
            elif LA1 == 49:
                alt1 = 2
            elif LA1 == 50:
                alt1 = 3
            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 1, 0, self.input)

                raise nvae

            if alt1 == 1:
                # borg/borgcron/py/Groc.g:230:17: ( '0' DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:230:17: ( '0' DIGIT )
                # borg/borgcron/py/Groc.g:230:19: '0' DIGIT
                pass 
                self.match(48)
                self.mDIGIT()





            elif alt1 == 2:
                # borg/borgcron/py/Groc.g:230:33: ( '1' DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:230:33: ( '1' DIGIT )
                # borg/borgcron/py/Groc.g:230:34: '1' DIGIT
                pass 
                self.match(49)
                self.mDIGIT()





            elif alt1 == 3:
                # borg/borgcron/py/Groc.g:230:47: ( '2' '0' .. '3' )
                pass 
                # borg/borgcron/py/Groc.g:230:47: ( '2' '0' .. '3' )
                # borg/borgcron/py/Groc.g:230:48: '2' '0' .. '3'
                pass 
                self.match(50)
                self.matchRange(48, 51)






            self.match(58)
            # borg/borgcron/py/Groc.g:232:15: ( '0' .. '5' DIGIT )
            # borg/borgcron/py/Groc.g:232:17: '0' .. '5' DIGIT
            pass 
            self.matchRange(48, 53)
            self.mDIGIT()



            if self._state.backtracking == 0:
                _type = TIME; 







            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "TWO_DIGIT_HOUR_TIME"



    # $ANTLR start "SYNCHRONIZED"
    def mSYNCHRONIZED(self, ):

        try:
            _type = SYNCHRONIZED
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:234:14: ( 'synchronized' )
            # borg/borgcron/py/Groc.g:234:16: 'synchronized'
            pass 
            self.match("synchronized")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "SYNCHRONIZED"



    # $ANTLR start "FIRST"
    def mFIRST(self, ):

        try:
            _type = FIRST
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:237:11: ( ( '1st' | 'first' ) )
            # borg/borgcron/py/Groc.g:237:13: ( '1st' | 'first' )
            pass 
            # borg/borgcron/py/Groc.g:237:13: ( '1st' | 'first' )
            alt2 = 2
            LA2_0 = self.input.LA(1)

            if (LA2_0 == 49) :
                alt2 = 1
            elif (LA2_0 == 102) :
                alt2 = 2
            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 2, 0, self.input)

                raise nvae

            if alt2 == 1:
                # borg/borgcron/py/Groc.g:237:15: '1st'
                pass 
                self.match("1st")


            elif alt2 == 2:
                # borg/borgcron/py/Groc.g:237:23: 'first'
                pass 
                self.match("first")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FIRST"



    # $ANTLR start "SECOND"
    def mSECOND(self, ):

        try:
            _type = SECOND
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:238:11: ( ( '2nd' | 'second' ) )
            # borg/borgcron/py/Groc.g:238:13: ( '2nd' | 'second' )
            pass 
            # borg/borgcron/py/Groc.g:238:13: ( '2nd' | 'second' )
            alt3 = 2
            LA3_0 = self.input.LA(1)

            if (LA3_0 == 50) :
                alt3 = 1
            elif (LA3_0 == 115) :
                alt3 = 2
            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 3, 0, self.input)

                raise nvae

            if alt3 == 1:
                # borg/borgcron/py/Groc.g:238:15: '2nd'
                pass 
                self.match("2nd")


            elif alt3 == 2:
                # borg/borgcron/py/Groc.g:238:23: 'second'
                pass 
                self.match("second")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "SECOND"



    # $ANTLR start "THIRD"
    def mTHIRD(self, ):

        try:
            _type = THIRD
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:239:11: ( ( '3rd' | 'third' ) )
            # borg/borgcron/py/Groc.g:239:13: ( '3rd' | 'third' )
            pass 
            # borg/borgcron/py/Groc.g:239:13: ( '3rd' | 'third' )
            alt4 = 2
            LA4_0 = self.input.LA(1)

            if (LA4_0 == 51) :
                alt4 = 1
            elif (LA4_0 == 116) :
                alt4 = 2
            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 4, 0, self.input)

                raise nvae

            if alt4 == 1:
                # borg/borgcron/py/Groc.g:239:15: '3rd'
                pass 
                self.match("3rd")


            elif alt4 == 2:
                # borg/borgcron/py/Groc.g:239:23: 'third'
                pass 
                self.match("third")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "THIRD"



    # $ANTLR start "FOURTH"
    def mFOURTH(self, ):

        try:
            _type = FOURTH
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:240:11: ( ( '4th' ) )
            # borg/borgcron/py/Groc.g:240:13: ( '4th' )
            pass 
            # borg/borgcron/py/Groc.g:240:13: ( '4th' )
            # borg/borgcron/py/Groc.g:240:15: '4th'
            pass 
            self.match("4th")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FOURTH"



    # $ANTLR start "FIFTH"
    def mFIFTH(self, ):

        try:
            _type = FIFTH
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:241:11: ( ( '5th' ) )
            # borg/borgcron/py/Groc.g:241:13: ( '5th' )
            pass 
            # borg/borgcron/py/Groc.g:241:13: ( '5th' )
            # borg/borgcron/py/Groc.g:241:15: '5th'
            pass 
            self.match("5th")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FIFTH"



    # $ANTLR start "FOURTH_OR_FIFTH"
    def mFOURTH_OR_FIFTH(self, ):

        try:
            _type = FOURTH_OR_FIFTH
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:248:11: ( ( ( 'fourth' ) | ( 'fifth' ) ) )
            # borg/borgcron/py/Groc.g:248:13: ( ( 'fourth' ) | ( 'fifth' ) )
            pass 
            # borg/borgcron/py/Groc.g:248:13: ( ( 'fourth' ) | ( 'fifth' ) )
            alt5 = 2
            LA5_0 = self.input.LA(1)

            if (LA5_0 == 102) :
                LA5_1 = self.input.LA(2)

                if (LA5_1 == 111) :
                    alt5 = 1
                elif (LA5_1 == 105) :
                    alt5 = 2
                else:
                    if self._state.backtracking > 0:
                        raise BacktrackingFailed

                    nvae = NoViableAltException("", 5, 1, self.input)

                    raise nvae

            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 5, 0, self.input)

                raise nvae

            if alt5 == 1:
                # borg/borgcron/py/Groc.g:248:15: ( 'fourth' )
                pass 
                # borg/borgcron/py/Groc.g:248:15: ( 'fourth' )
                # borg/borgcron/py/Groc.g:248:16: 'fourth'
                pass 
                self.match("fourth")
                if self._state.backtracking == 0:
                    _type = FOURTH; 






            elif alt5 == 2:
                # borg/borgcron/py/Groc.g:249:15: ( 'fifth' )
                pass 
                # borg/borgcron/py/Groc.g:249:15: ( 'fifth' )
                # borg/borgcron/py/Groc.g:249:16: 'fifth'
                pass 
                self.match("fifth")
                if self._state.backtracking == 0:
                    _type = FIFTH; 










            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FOURTH_OR_FIFTH"



    # $ANTLR start "DAY"
    def mDAY(self, ):

        try:
            _type = DAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:252:8: ( 'day' )
            # borg/borgcron/py/Groc.g:252:10: 'day'
            pass 
            self.match("day")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "DAY"



    # $ANTLR start "MONDAY"
    def mMONDAY(self, ):

        try:
            _type = MONDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:254:11: ( 'mon' ( 'day' )? )
            # borg/borgcron/py/Groc.g:254:13: 'mon' ( 'day' )?
            pass 
            self.match("mon")
            # borg/borgcron/py/Groc.g:254:19: ( 'day' )?
            alt6 = 2
            LA6_0 = self.input.LA(1)

            if (LA6_0 == 100) :
                alt6 = 1
            if alt6 == 1:
                # borg/borgcron/py/Groc.g:254:20: 'day'
                pass 
                self.match("day")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "MONDAY"



    # $ANTLR start "TUESDAY"
    def mTUESDAY(self, ):

        try:
            _type = TUESDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:255:11: ( 'tue' ( 'sday' )? )
            # borg/borgcron/py/Groc.g:255:13: 'tue' ( 'sday' )?
            pass 
            self.match("tue")
            # borg/borgcron/py/Groc.g:255:19: ( 'sday' )?
            alt7 = 2
            LA7_0 = self.input.LA(1)

            if (LA7_0 == 115) :
                alt7 = 1
            if alt7 == 1:
                # borg/borgcron/py/Groc.g:255:20: 'sday'
                pass 
                self.match("sday")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "TUESDAY"



    # $ANTLR start "WEDNESDAY"
    def mWEDNESDAY(self, ):

        try:
            _type = WEDNESDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:256:11: ( 'wed' ( 'nesday' )? )
            # borg/borgcron/py/Groc.g:256:13: 'wed' ( 'nesday' )?
            pass 
            self.match("wed")
            # borg/borgcron/py/Groc.g:256:19: ( 'nesday' )?
            alt8 = 2
            LA8_0 = self.input.LA(1)

            if (LA8_0 == 110) :
                alt8 = 1
            if alt8 == 1:
                # borg/borgcron/py/Groc.g:256:20: 'nesday'
                pass 
                self.match("nesday")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "WEDNESDAY"



    # $ANTLR start "THURSDAY"
    def mTHURSDAY(self, ):

        try:
            _type = THURSDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:257:11: ( 'thu' ( 'rsday' )? )
            # borg/borgcron/py/Groc.g:257:13: 'thu' ( 'rsday' )?
            pass 
            self.match("thu")
            # borg/borgcron/py/Groc.g:257:19: ( 'rsday' )?
            alt9 = 2
            LA9_0 = self.input.LA(1)

            if (LA9_0 == 114) :
                alt9 = 1
            if alt9 == 1:
                # borg/borgcron/py/Groc.g:257:20: 'rsday'
                pass 
                self.match("rsday")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "THURSDAY"



    # $ANTLR start "FRIDAY"
    def mFRIDAY(self, ):

        try:
            _type = FRIDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:258:11: ( 'fri' ( 'day' )? )
            # borg/borgcron/py/Groc.g:258:13: 'fri' ( 'day' )?
            pass 
            self.match("fri")
            # borg/borgcron/py/Groc.g:258:19: ( 'day' )?
            alt10 = 2
            LA10_0 = self.input.LA(1)

            if (LA10_0 == 100) :
                alt10 = 1
            if alt10 == 1:
                # borg/borgcron/py/Groc.g:258:20: 'day'
                pass 
                self.match("day")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FRIDAY"



    # $ANTLR start "SATURDAY"
    def mSATURDAY(self, ):

        try:
            _type = SATURDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:259:11: ( 'sat' ( 'urday' )? )
            # borg/borgcron/py/Groc.g:259:13: 'sat' ( 'urday' )?
            pass 
            self.match("sat")
            # borg/borgcron/py/Groc.g:259:19: ( 'urday' )?
            alt11 = 2
            LA11_0 = self.input.LA(1)

            if (LA11_0 == 117) :
                alt11 = 1
            if alt11 == 1:
                # borg/borgcron/py/Groc.g:259:20: 'urday'
                pass 
                self.match("urday")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "SATURDAY"



    # $ANTLR start "SUNDAY"
    def mSUNDAY(self, ):

        try:
            _type = SUNDAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:260:11: ( 'sun' ( 'day' )? )
            # borg/borgcron/py/Groc.g:260:13: 'sun' ( 'day' )?
            pass 
            self.match("sun")
            # borg/borgcron/py/Groc.g:260:19: ( 'day' )?
            alt12 = 2
            LA12_0 = self.input.LA(1)

            if (LA12_0 == 100) :
                alt12 = 1
            if alt12 == 1:
                # borg/borgcron/py/Groc.g:260:20: 'day'
                pass 
                self.match("day")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "SUNDAY"



    # $ANTLR start "JANUARY"
    def mJANUARY(self, ):

        try:
            _type = JANUARY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:263:11: ( 'jan' ( 'uary' )? )
            # borg/borgcron/py/Groc.g:263:13: 'jan' ( 'uary' )?
            pass 
            self.match("jan")
            # borg/borgcron/py/Groc.g:263:19: ( 'uary' )?
            alt13 = 2
            LA13_0 = self.input.LA(1)

            if (LA13_0 == 117) :
                alt13 = 1
            if alt13 == 1:
                # borg/borgcron/py/Groc.g:263:20: 'uary'
                pass 
                self.match("uary")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "JANUARY"



    # $ANTLR start "FEBRUARY"
    def mFEBRUARY(self, ):

        try:
            _type = FEBRUARY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:264:11: ( 'feb' ( 'ruary' )? )
            # borg/borgcron/py/Groc.g:264:13: 'feb' ( 'ruary' )?
            pass 
            self.match("feb")
            # borg/borgcron/py/Groc.g:264:19: ( 'ruary' )?
            alt14 = 2
            LA14_0 = self.input.LA(1)

            if (LA14_0 == 114) :
                alt14 = 1
            if alt14 == 1:
                # borg/borgcron/py/Groc.g:264:20: 'ruary'
                pass 
                self.match("ruary")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FEBRUARY"



    # $ANTLR start "MARCH"
    def mMARCH(self, ):

        try:
            _type = MARCH
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:265:11: ( 'mar' ( 'ch' )? )
            # borg/borgcron/py/Groc.g:265:13: 'mar' ( 'ch' )?
            pass 
            self.match("mar")
            # borg/borgcron/py/Groc.g:265:19: ( 'ch' )?
            alt15 = 2
            LA15_0 = self.input.LA(1)

            if (LA15_0 == 99) :
                alt15 = 1
            if alt15 == 1:
                # borg/borgcron/py/Groc.g:265:20: 'ch'
                pass 
                self.match("ch")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "MARCH"



    # $ANTLR start "APRIL"
    def mAPRIL(self, ):

        try:
            _type = APRIL
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:266:11: ( 'apr' ( 'il' )? )
            # borg/borgcron/py/Groc.g:266:13: 'apr' ( 'il' )?
            pass 
            self.match("apr")
            # borg/borgcron/py/Groc.g:266:19: ( 'il' )?
            alt16 = 2
            LA16_0 = self.input.LA(1)

            if (LA16_0 == 105) :
                alt16 = 1
            if alt16 == 1:
                # borg/borgcron/py/Groc.g:266:20: 'il'
                pass 
                self.match("il")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "APRIL"



    # $ANTLR start "MAY"
    def mMAY(self, ):

        try:
            _type = MAY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:267:11: ( 'may' )
            # borg/borgcron/py/Groc.g:267:13: 'may'
            pass 
            self.match("may")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "MAY"



    # $ANTLR start "JUNE"
    def mJUNE(self, ):

        try:
            _type = JUNE
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:268:11: ( 'jun' ( 'e' )? )
            # borg/borgcron/py/Groc.g:268:13: 'jun' ( 'e' )?
            pass 
            self.match("jun")
            # borg/borgcron/py/Groc.g:268:19: ( 'e' )?
            alt17 = 2
            LA17_0 = self.input.LA(1)

            if (LA17_0 == 101) :
                alt17 = 1
            if alt17 == 1:
                # borg/borgcron/py/Groc.g:268:20: 'e'
                pass 
                self.match(101)






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "JUNE"



    # $ANTLR start "JULY"
    def mJULY(self, ):

        try:
            _type = JULY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:269:11: ( 'jul' ( 'y' )? )
            # borg/borgcron/py/Groc.g:269:13: 'jul' ( 'y' )?
            pass 
            self.match("jul")
            # borg/borgcron/py/Groc.g:269:19: ( 'y' )?
            alt18 = 2
            LA18_0 = self.input.LA(1)

            if (LA18_0 == 121) :
                alt18 = 1
            if alt18 == 1:
                # borg/borgcron/py/Groc.g:269:20: 'y'
                pass 
                self.match(121)






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "JULY"



    # $ANTLR start "AUGUST"
    def mAUGUST(self, ):

        try:
            _type = AUGUST
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:270:11: ( 'aug' ( 'ust' )? )
            # borg/borgcron/py/Groc.g:270:13: 'aug' ( 'ust' )?
            pass 
            self.match("aug")
            # borg/borgcron/py/Groc.g:270:19: ( 'ust' )?
            alt19 = 2
            LA19_0 = self.input.LA(1)

            if (LA19_0 == 117) :
                alt19 = 1
            if alt19 == 1:
                # borg/borgcron/py/Groc.g:270:20: 'ust'
                pass 
                self.match("ust")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "AUGUST"



    # $ANTLR start "SEPTEMBER"
    def mSEPTEMBER(self, ):

        try:
            _type = SEPTEMBER
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:271:11: ( 'sep' ( 'tember' )? )
            # borg/borgcron/py/Groc.g:271:13: 'sep' ( 'tember' )?
            pass 
            self.match("sep")
            # borg/borgcron/py/Groc.g:271:19: ( 'tember' )?
            alt20 = 2
            LA20_0 = self.input.LA(1)

            if (LA20_0 == 116) :
                alt20 = 1
            if alt20 == 1:
                # borg/borgcron/py/Groc.g:271:20: 'tember'
                pass 
                self.match("tember")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "SEPTEMBER"



    # $ANTLR start "OCTOBER"
    def mOCTOBER(self, ):

        try:
            _type = OCTOBER
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:272:11: ( 'oct' ( 'ober' )? )
            # borg/borgcron/py/Groc.g:272:13: 'oct' ( 'ober' )?
            pass 
            self.match("oct")
            # borg/borgcron/py/Groc.g:272:19: ( 'ober' )?
            alt21 = 2
            LA21_0 = self.input.LA(1)

            if (LA21_0 == 111) :
                alt21 = 1
            if alt21 == 1:
                # borg/borgcron/py/Groc.g:272:20: 'ober'
                pass 
                self.match("ober")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "OCTOBER"



    # $ANTLR start "NOVEMBER"
    def mNOVEMBER(self, ):

        try:
            _type = NOVEMBER
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:273:11: ( 'nov' ( 'ember' )? )
            # borg/borgcron/py/Groc.g:273:13: 'nov' ( 'ember' )?
            pass 
            self.match("nov")
            # borg/borgcron/py/Groc.g:273:19: ( 'ember' )?
            alt22 = 2
            LA22_0 = self.input.LA(1)

            if (LA22_0 == 101) :
                alt22 = 1
            if alt22 == 1:
                # borg/borgcron/py/Groc.g:273:20: 'ember'
                pass 
                self.match("ember")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "NOVEMBER"



    # $ANTLR start "DECEMBER"
    def mDECEMBER(self, ):

        try:
            _type = DECEMBER
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:274:11: ( 'dec' ( 'ember' )? )
            # borg/borgcron/py/Groc.g:274:13: 'dec' ( 'ember' )?
            pass 
            self.match("dec")
            # borg/borgcron/py/Groc.g:274:19: ( 'ember' )?
            alt23 = 2
            LA23_0 = self.input.LA(1)

            if (LA23_0 == 101) :
                alt23 = 1
            if alt23 == 1:
                # borg/borgcron/py/Groc.g:274:20: 'ember'
                pass 
                self.match("ember")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "DECEMBER"



    # $ANTLR start "MONTH"
    def mMONTH(self, ):

        try:
            _type = MONTH
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:276:11: ( ( 'month' ) )
            # borg/borgcron/py/Groc.g:276:13: ( 'month' )
            pass 
            # borg/borgcron/py/Groc.g:276:13: ( 'month' )
            # borg/borgcron/py/Groc.g:276:15: 'month'
            pass 
            self.match("month")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "MONTH"



    # $ANTLR start "QUARTER"
    def mQUARTER(self, ):

        try:
            _type = QUARTER
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:277:11: ( ( 'quarter' ) )
            # borg/borgcron/py/Groc.g:277:13: ( 'quarter' )
            pass 
            # borg/borgcron/py/Groc.g:277:13: ( 'quarter' )
            # borg/borgcron/py/Groc.g:277:15: 'quarter'
            pass 
            self.match("quarter")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "QUARTER"



    # $ANTLR start "EVERY"
    def mEVERY(self, ):

        try:
            _type = EVERY
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:278:11: ( ( 'every' ) )
            # borg/borgcron/py/Groc.g:278:13: ( 'every' )
            pass 
            # borg/borgcron/py/Groc.g:278:13: ( 'every' )
            # borg/borgcron/py/Groc.g:278:15: 'every'
            pass 
            self.match("every")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "EVERY"



    # $ANTLR start "HOURS"
    def mHOURS(self, ):

        try:
            _type = HOURS
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:280:11: ( ( 'hours' ) )
            # borg/borgcron/py/Groc.g:280:13: ( 'hours' )
            pass 
            # borg/borgcron/py/Groc.g:280:13: ( 'hours' )
            # borg/borgcron/py/Groc.g:280:15: 'hours'
            pass 
            self.match("hours")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "HOURS"



    # $ANTLR start "MINUTES"
    def mMINUTES(self, ):

        try:
            _type = MINUTES
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:281:11: ( ( 'mins' | 'minutes' ) )
            # borg/borgcron/py/Groc.g:281:13: ( 'mins' | 'minutes' )
            pass 
            # borg/borgcron/py/Groc.g:281:13: ( 'mins' | 'minutes' )
            alt24 = 2
            LA24_0 = self.input.LA(1)

            if (LA24_0 == 109) :
                LA24_1 = self.input.LA(2)

                if (LA24_1 == 105) :
                    LA24_2 = self.input.LA(3)

                    if (LA24_2 == 110) :
                        LA24_3 = self.input.LA(4)

                        if (LA24_3 == 115) :
                            alt24 = 1
                        elif (LA24_3 == 117) :
                            alt24 = 2
                        else:
                            if self._state.backtracking > 0:
                                raise BacktrackingFailed

                            nvae = NoViableAltException("", 24, 3, self.input)

                            raise nvae

                    else:
                        if self._state.backtracking > 0:
                            raise BacktrackingFailed

                        nvae = NoViableAltException("", 24, 2, self.input)

                        raise nvae

                else:
                    if self._state.backtracking > 0:
                        raise BacktrackingFailed

                    nvae = NoViableAltException("", 24, 1, self.input)

                    raise nvae

            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 24, 0, self.input)

                raise nvae

            if alt24 == 1:
                # borg/borgcron/py/Groc.g:281:15: 'mins'
                pass 
                self.match("mins")


            elif alt24 == 2:
                # borg/borgcron/py/Groc.g:281:24: 'minutes'
                pass 
                self.match("minutes")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "MINUTES"



    # $ANTLR start "COMMA"
    def mCOMMA(self, ):

        try:
            _type = COMMA
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:284:11: ( ( ',' ) )
            # borg/borgcron/py/Groc.g:284:13: ( ',' )
            pass 
            # borg/borgcron/py/Groc.g:284:13: ( ',' )
            # borg/borgcron/py/Groc.g:284:15: ','
            pass 
            self.match(44)






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "COMMA"



    # $ANTLR start "OF"
    def mOF(self, ):

        try:
            _type = OF
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:285:11: ( ( 'of' ) )
            # borg/borgcron/py/Groc.g:285:13: ( 'of' )
            pass 
            # borg/borgcron/py/Groc.g:285:13: ( 'of' )
            # borg/borgcron/py/Groc.g:285:15: 'of'
            pass 
            self.match("of")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "OF"



    # $ANTLR start "FROM"
    def mFROM(self, ):

        try:
            _type = FROM
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:286:11: ( ( 'from' ) )
            # borg/borgcron/py/Groc.g:286:13: ( 'from' )
            pass 
            # borg/borgcron/py/Groc.g:286:13: ( 'from' )
            # borg/borgcron/py/Groc.g:286:15: 'from'
            pass 
            self.match("from")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "FROM"



    # $ANTLR start "TO"
    def mTO(self, ):

        try:
            _type = TO
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:287:11: ( ( 'to' ) )
            # borg/borgcron/py/Groc.g:287:13: ( 'to' )
            pass 
            # borg/borgcron/py/Groc.g:287:13: ( 'to' )
            # borg/borgcron/py/Groc.g:287:15: 'to'
            pass 
            self.match("to")






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "TO"



    # $ANTLR start "WS"
    def mWS(self, ):

        try:
            _type = WS
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:288:11: ( ( ' ' | '\\t' | '\\n' | '\\r' ) )
            # borg/borgcron/py/Groc.g:288:13: ( ' ' | '\\t' | '\\n' | '\\r' )
            pass 
            if (9 <= self.input.LA(1) <= 10) or self.input.LA(1) == 13 or self.input.LA(1) == 32:
                self.input.consume()
            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse

            if self._state.backtracking == 0:
                _channel=HIDDEN; 




            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "WS"



    # $ANTLR start "DIGIT"
    def mDIGIT(self, ):

        try:
            _type = DIGIT
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:290:11: ( ( '0' .. '9' ) )
            # borg/borgcron/py/Groc.g:290:13: ( '0' .. '9' )
            pass 
            # borg/borgcron/py/Groc.g:290:13: ( '0' .. '9' )
            # borg/borgcron/py/Groc.g:290:15: '0' .. '9'
            pass 
            self.matchRange(48, 57)






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "DIGIT"



    # $ANTLR start "DIGITS"
    def mDIGITS(self, ):

        try:
            _type = DIGITS
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:291:11: ( ( ( DIGIT DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT ) ) )
            # borg/borgcron/py/Groc.g:291:13: ( ( DIGIT DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT ) )
            pass 
            # borg/borgcron/py/Groc.g:291:13: ( ( DIGIT DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT DIGIT ) | ( DIGIT DIGIT ) )
            alt25 = 4
            LA25_0 = self.input.LA(1)

            if ((48 <= LA25_0 <= 57)) :
                LA25_1 = self.input.LA(2)

                if ((48 <= LA25_1 <= 57)) :
                    LA25_2 = self.input.LA(3)

                    if ((48 <= LA25_2 <= 57)) :
                        LA25_4 = self.input.LA(4)

                        if ((48 <= LA25_4 <= 57)) :
                            LA25_6 = self.input.LA(5)

                            if ((48 <= LA25_6 <= 57)) and (self.synpred1_Groc()):
                                alt25 = 1
                            else:
                                alt25 = 2
                        else:
                            alt25 = 3
                    else:
                        alt25 = 4
                else:
                    if self._state.backtracking > 0:
                        raise BacktrackingFailed

                    nvae = NoViableAltException("", 25, 1, self.input)

                    raise nvae

            else:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                nvae = NoViableAltException("", 25, 0, self.input)

                raise nvae

            if alt25 == 1:
                # borg/borgcron/py/Groc.g:291:15: ( DIGIT DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:291:52: ( DIGIT DIGIT DIGIT DIGIT DIGIT )
                # borg/borgcron/py/Groc.g:291:54: DIGIT DIGIT DIGIT DIGIT DIGIT
                pass 
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()





            elif alt25 == 2:
                # borg/borgcron/py/Groc.g:292:15: ( DIGIT DIGIT DIGIT DIGIT )=> ( DIGIT DIGIT DIGIT DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:292:46: ( DIGIT DIGIT DIGIT DIGIT )
                # borg/borgcron/py/Groc.g:292:48: DIGIT DIGIT DIGIT DIGIT
                pass 
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()





            elif alt25 == 3:
                # borg/borgcron/py/Groc.g:293:15: ( DIGIT DIGIT DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:293:15: ( DIGIT DIGIT DIGIT )
                # borg/borgcron/py/Groc.g:293:17: DIGIT DIGIT DIGIT
                pass 
                self.mDIGIT()
                self.mDIGIT()
                self.mDIGIT()





            elif alt25 == 4:
                # borg/borgcron/py/Groc.g:294:15: ( DIGIT DIGIT )
                pass 
                # borg/borgcron/py/Groc.g:294:15: ( DIGIT DIGIT )
                # borg/borgcron/py/Groc.g:294:17: DIGIT DIGIT
                pass 
                self.mDIGIT()
                self.mDIGIT()









            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "DIGITS"



    # $ANTLR start "UNKNOWN_TOKEN"
    def mUNKNOWN_TOKEN(self, ):

        try:
            _type = UNKNOWN_TOKEN
            _channel = DEFAULT_CHANNEL

            # borg/borgcron/py/Groc.g:299:15: ( ( . ) )
            # borg/borgcron/py/Groc.g:299:17: ( . )
            pass 
            # borg/borgcron/py/Groc.g:299:17: ( . )
            # borg/borgcron/py/Groc.g:299:19: .
            pass 
            self.matchAny()






            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass

    # $ANTLR end "UNKNOWN_TOKEN"



    def mTokens(self):
        # borg/borgcron/py/Groc.g:1:8: ( TIME | TWO_DIGIT_HOUR_TIME | SYNCHRONIZED | FIRST | SECOND | THIRD | FOURTH | FIFTH | FOURTH_OR_FIFTH | DAY | MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY | SATURDAY | SUNDAY | JANUARY | FEBRUARY | MARCH | APRIL | MAY | JUNE | JULY | AUGUST | SEPTEMBER | OCTOBER | NOVEMBER | DECEMBER | MONTH | QUARTER | EVERY | HOURS | MINUTES | COMMA | OF | FROM | TO | WS | DIGIT | DIGITS | UNKNOWN_TOKEN )
        alt26 = 42
        alt26 = self.dfa26.predict(self.input)
        if alt26 == 1:
            # borg/borgcron/py/Groc.g:1:10: TIME
            pass 
            self.mTIME()


        elif alt26 == 2:
            # borg/borgcron/py/Groc.g:1:15: TWO_DIGIT_HOUR_TIME
            pass 
            self.mTWO_DIGIT_HOUR_TIME()


        elif alt26 == 3:
            # borg/borgcron/py/Groc.g:1:35: SYNCHRONIZED
            pass 
            self.mSYNCHRONIZED()


        elif alt26 == 4:
            # borg/borgcron/py/Groc.g:1:48: FIRST
            pass 
            self.mFIRST()


        elif alt26 == 5:
            # borg/borgcron/py/Groc.g:1:54: SECOND
            pass 
            self.mSECOND()


        elif alt26 == 6:
            # borg/borgcron/py/Groc.g:1:61: THIRD
            pass 
            self.mTHIRD()


        elif alt26 == 7:
            # borg/borgcron/py/Groc.g:1:67: FOURTH
            pass 
            self.mFOURTH()


        elif alt26 == 8:
            # borg/borgcron/py/Groc.g:1:74: FIFTH
            pass 
            self.mFIFTH()


        elif alt26 == 9:
            # borg/borgcron/py/Groc.g:1:80: FOURTH_OR_FIFTH
            pass 
            self.mFOURTH_OR_FIFTH()


        elif alt26 == 10:
            # borg/borgcron/py/Groc.g:1:96: DAY
            pass 
            self.mDAY()


        elif alt26 == 11:
            # borg/borgcron/py/Groc.g:1:100: MONDAY
            pass 
            self.mMONDAY()


        elif alt26 == 12:
            # borg/borgcron/py/Groc.g:1:107: TUESDAY
            pass 
            self.mTUESDAY()


        elif alt26 == 13:
            # borg/borgcron/py/Groc.g:1:115: WEDNESDAY
            pass 
            self.mWEDNESDAY()


        elif alt26 == 14:
            # borg/borgcron/py/Groc.g:1:125: THURSDAY
            pass 
            self.mTHURSDAY()


        elif alt26 == 15:
            # borg/borgcron/py/Groc.g:1:134: FRIDAY
            pass 
            self.mFRIDAY()


        elif alt26 == 16:
            # borg/borgcron/py/Groc.g:1:141: SATURDAY
            pass 
            self.mSATURDAY()


        elif alt26 == 17:
            # borg/borgcron/py/Groc.g:1:150: SUNDAY
            pass 
            self.mSUNDAY()


        elif alt26 == 18:
            # borg/borgcron/py/Groc.g:1:157: JANUARY
            pass 
            self.mJANUARY()


        elif alt26 == 19:
            # borg/borgcron/py/Groc.g:1:165: FEBRUARY
            pass 
            self.mFEBRUARY()


        elif alt26 == 20:
            # borg/borgcron/py/Groc.g:1:174: MARCH
            pass 
            self.mMARCH()


        elif alt26 == 21:
            # borg/borgcron/py/Groc.g:1:180: APRIL
            pass 
            self.mAPRIL()


        elif alt26 == 22:
            # borg/borgcron/py/Groc.g:1:186: MAY
            pass 
            self.mMAY()


        elif alt26 == 23:
            # borg/borgcron/py/Groc.g:1:190: JUNE
            pass 
            self.mJUNE()


        elif alt26 == 24:
            # borg/borgcron/py/Groc.g:1:195: JULY
            pass 
            self.mJULY()


        elif alt26 == 25:
            # borg/borgcron/py/Groc.g:1:200: AUGUST
            pass 
            self.mAUGUST()


        elif alt26 == 26:
            # borg/borgcron/py/Groc.g:1:207: SEPTEMBER
            pass 
            self.mSEPTEMBER()


        elif alt26 == 27:
            # borg/borgcron/py/Groc.g:1:217: OCTOBER
            pass 
            self.mOCTOBER()


        elif alt26 == 28:
            # borg/borgcron/py/Groc.g:1:225: NOVEMBER
            pass 
            self.mNOVEMBER()


        elif alt26 == 29:
            # borg/borgcron/py/Groc.g:1:234: DECEMBER
            pass 
            self.mDECEMBER()


        elif alt26 == 30:
            # borg/borgcron/py/Groc.g:1:243: MONTH
            pass 
            self.mMONTH()


        elif alt26 == 31:
            # borg/borgcron/py/Groc.g:1:249: QUARTER
            pass 
            self.mQUARTER()


        elif alt26 == 32:
            # borg/borgcron/py/Groc.g:1:257: EVERY
            pass 
            self.mEVERY()


        elif alt26 == 33:
            # borg/borgcron/py/Groc.g:1:263: HOURS
            pass 
            self.mHOURS()


        elif alt26 == 34:
            # borg/borgcron/py/Groc.g:1:269: MINUTES
            pass 
            self.mMINUTES()


        elif alt26 == 35:
            # borg/borgcron/py/Groc.g:1:277: COMMA
            pass 
            self.mCOMMA()


        elif alt26 == 36:
            # borg/borgcron/py/Groc.g:1:283: OF
            pass 
            self.mOF()


        elif alt26 == 37:
            # borg/borgcron/py/Groc.g:1:286: FROM
            pass 
            self.mFROM()


        elif alt26 == 38:
            # borg/borgcron/py/Groc.g:1:291: TO
            pass 
            self.mTO()


        elif alt26 == 39:
            # borg/borgcron/py/Groc.g:1:294: WS
            pass 
            self.mWS()


        elif alt26 == 40:
            # borg/borgcron/py/Groc.g:1:297: DIGIT
            pass 
            self.mDIGIT()


        elif alt26 == 41:
            # borg/borgcron/py/Groc.g:1:303: DIGITS
            pass 
            self.mDIGITS()


        elif alt26 == 42:
            # borg/borgcron/py/Groc.g:1:310: UNKNOWN_TOKEN
            pass 
            self.mUNKNOWN_TOKEN()






    # $ANTLR start "synpred1_Groc"
    def synpred1_Groc_fragment(self, ):
        # borg/borgcron/py/Groc.g:291:15: ( DIGIT DIGIT DIGIT DIGIT DIGIT )
        # borg/borgcron/py/Groc.g:291:17: DIGIT DIGIT DIGIT DIGIT DIGIT
        pass 
        self.mDIGIT()
        self.mDIGIT()
        self.mDIGIT()
        self.mDIGIT()
        self.mDIGIT()


    # $ANTLR end "synpred1_Groc"



    # $ANTLR start "synpred2_Groc"
    def synpred2_Groc_fragment(self, ):
        # borg/borgcron/py/Groc.g:292:15: ( DIGIT DIGIT DIGIT DIGIT )
        # borg/borgcron/py/Groc.g:292:17: DIGIT DIGIT DIGIT DIGIT
        pass 
        self.mDIGIT()
        self.mDIGIT()
        self.mDIGIT()
        self.mDIGIT()


    # $ANTLR end "synpred2_Groc"



    def synpred2_Groc(self):
        self._state.backtracking += 1
        start = self.input.mark()
        try:
            self.synpred2_Groc_fragment()
        except BacktrackingFailed:
            success = False
        else:
            success = True
        self.input.rewind(start)
        self._state.backtracking -= 1
        return success

    def synpred1_Groc(self):
        self._state.backtracking += 1
        start = self.input.mark()
        try:
            self.synpred1_Groc_fragment()
        except BacktrackingFailed:
            success = False
        else:
            success = True
        self.input.rewind(start)
        self._state.backtracking -= 1
        return success



    # lookup tables for DFA #26

    DFA26_eot = DFA.unpack(
        u"\1\uffff\4\30\2\27\1\30\1\27\2\30\12\27\4\uffff\1\37\2\uffff\2"
        u"\37\47\uffff\1\113\6\uffff"
        )

    DFA26_eof = DFA.unpack(
        u"\114\uffff"
        )

    DFA26_min = DFA.unpack(
        u"\1\0\4\60\1\141\1\145\1\60\1\150\2\60\2\141\1\145\1\141\1\160\1"
        u"\143\1\157\1\165\1\166\1\157\4\uffff\1\72\2\uffff\2\72\4\uffff"
        u"\1\143\2\uffff\1\146\1\uffff\1\151\2\uffff\1\151\5\uffff\1\156"
        u"\1\162\3\uffff\1\154\17\uffff\1\164\6\uffff"
        )

    DFA26_max = DFA.unpack(
        u"\1\uffff\1\72\1\163\1\156\1\162\1\171\1\162\1\164\1\165\1\164\1"
        u"\72\1\145\1\157\1\145\2\165\1\146\1\157\1\165\1\166\1\157\4\uffff"
        u"\1\72\2\uffff\2\72\4\uffff\1\160\2\uffff\1\162\1\uffff\1\157\2"
        u"\uffff\1\165\5\uffff\1\156\1\171\3\uffff\1\156\17\uffff\1\164\6"
        u"\uffff"
        )

    DFA26_accept = DFA.unpack(
        u"\25\uffff\1\43\1\47\1\52\1\50\1\uffff\1\1\1\4\2\uffff\1\5\1\51"
        u"\1\6\1\3\1\uffff\1\20\1\21\1\uffff\1\11\1\uffff\1\23\1\7\1\uffff"
        u"\1\14\1\46\1\10\1\12\1\35\2\uffff\1\42\1\15\1\22\1\uffff\1\25\1"
        u"\31\1\33\1\44\1\34\1\37\1\40\1\41\1\43\1\47\1\2\1\32\1\17\1\45"
        u"\1\16\1\uffff\1\24\1\26\1\27\1\30\1\36\1\13"
        )

    DFA26_special = DFA.unpack(
        u"\1\0\113\uffff"
        )

            
    DFA26_transition = [
        DFA.unpack(u"\11\27\2\26\2\27\1\26\22\27\1\26\13\27\1\25\3\27\1\1"
        u"\1\2\1\3\1\4\1\7\1\11\4\12\47\27\1\17\2\27\1\13\1\23\1\6\1\27\1"
        u"\24\1\27\1\16\2\27\1\14\1\21\1\20\1\27\1\22\1\27\1\5\1\10\2\27"
        u"\1\15\uff88\27"),
        DFA.unpack(u"\12\31\1\32"),
        DFA.unpack(u"\12\34\1\32\70\uffff\1\33"),
        DFA.unpack(u"\4\35\6\37\1\32\63\uffff\1\36"),
        DFA.unpack(u"\12\37\1\32\67\uffff\1\40"),
        DFA.unpack(u"\1\43\3\uffff\1\42\17\uffff\1\44\3\uffff\1\41"),
        DFA.unpack(u"\1\50\3\uffff\1\45\5\uffff\1\46\2\uffff\1\47"),
        DFA.unpack(u"\12\37\1\32\71\uffff\1\51"),
        DFA.unpack(u"\1\52\6\uffff\1\54\5\uffff\1\53"),
        DFA.unpack(u"\12\37\1\32\71\uffff\1\55"),
        DFA.unpack(u"\12\37\1\32"),
        DFA.unpack(u"\1\56\3\uffff\1\57"),
        DFA.unpack(u"\1\61\7\uffff\1\62\5\uffff\1\60"),
        DFA.unpack(u"\1\63"),
        DFA.unpack(u"\1\64\23\uffff\1\65"),
        DFA.unpack(u"\1\66\4\uffff\1\67"),
        DFA.unpack(u"\1\70\2\uffff\1\71"),
        DFA.unpack(u"\1\72"),
        DFA.unpack(u"\1\73"),
        DFA.unpack(u"\1\74"),
        DFA.unpack(u"\1\75"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\100"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\100"),
        DFA.unpack(u"\1\100"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\36\14\uffff\1\101"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\46\13\uffff\1\33"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\102\5\uffff\1\103"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\40\13\uffff\1\104"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\105"),
        DFA.unpack(u"\1\106\6\uffff\1\107"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\111\1\uffff\1\110"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\112"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]

    # class definition for DFA #26

    class DFA26(DFA):
        def specialStateTransition(self_, s, input):
            # convince pylint that my self_ magic is ok ;)
            # pylint: disable-msg=E0213

            # pretend we are a member of the recognizer
            # thus semantic predicates can be evaluated
            self = self_.recognizer

            _s = s

            if s == 0: 
                LA26_0 = input.LA(1)

                s = -1
                if (LA26_0 == 48):
                    s = 1

                elif (LA26_0 == 49):
                    s = 2

                elif (LA26_0 == 50):
                    s = 3

                elif (LA26_0 == 51):
                    s = 4

                elif (LA26_0 == 115):
                    s = 5

                elif (LA26_0 == 102):
                    s = 6

                elif (LA26_0 == 52):
                    s = 7

                elif (LA26_0 == 116):
                    s = 8

                elif (LA26_0 == 53):
                    s = 9

                elif ((54 <= LA26_0 <= 57)):
                    s = 10

                elif (LA26_0 == 100):
                    s = 11

                elif (LA26_0 == 109):
                    s = 12

                elif (LA26_0 == 119):
                    s = 13

                elif (LA26_0 == 106):
                    s = 14

                elif (LA26_0 == 97):
                    s = 15

                elif (LA26_0 == 111):
                    s = 16

                elif (LA26_0 == 110):
                    s = 17

                elif (LA26_0 == 113):
                    s = 18

                elif (LA26_0 == 101):
                    s = 19

                elif (LA26_0 == 104):
                    s = 20

                elif (LA26_0 == 44):
                    s = 21

                elif ((9 <= LA26_0 <= 10) or LA26_0 == 13 or LA26_0 == 32):
                    s = 22

                elif ((0 <= LA26_0 <= 8) or (11 <= LA26_0 <= 12) or (14 <= LA26_0 <= 31) or (33 <= LA26_0 <= 43) or (45 <= LA26_0 <= 47) or (58 <= LA26_0 <= 96) or (98 <= LA26_0 <= 99) or LA26_0 == 103 or LA26_0 == 105 or (107 <= LA26_0 <= 108) or LA26_0 == 112 or LA26_0 == 114 or (117 <= LA26_0 <= 118) or (120 <= LA26_0 <= 65535)):
                    s = 23

                if s >= 0:
                    return s

            if self._state.backtracking >0:
                raise BacktrackingFailed
            nvae = NoViableAltException(self_.getDescription(), 26, _s, input)
            self_.error(nvae)
            raise nvae
 



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import LexerMain
    main = LexerMain(GrocLexer)
    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)


if __name__ == '__main__':
    main(sys.argv)
