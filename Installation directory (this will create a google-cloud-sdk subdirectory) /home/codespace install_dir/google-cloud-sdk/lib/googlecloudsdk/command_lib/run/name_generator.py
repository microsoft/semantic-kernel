# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Generate random names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random
import string

# The strings below contain bad words, swear words, and otherwise offensive
# words as well as strings phonetically similar to offensive words and
# misspellings of offensive words.
# This list is used as a blocklist to prevent potentially offensive words
# from being generated and shown to users. While offensive words may
# still be generated from combining multiple 3-letter words, this blocklist is
# a best effort to limit any potential offensiveness. Words may be added or
# removed from this list as deemed appropriate.
#
# Only 3-letter words matching the consonant-vowel-consonant pattern are
# included.
# TODO(b/183436507) Sync the list
_INVALID_THREE_LETTER_WORDS = frozenset({
    'bah',
    'baj',
    'bal',
    'bam',
    'bar',
    'beh',
    'bew',
    'bez',
    'bic',
    'bin',
    'bod',
    'bok',
    'bol',
    'bon',
    'bow',
    'box',
    'bun',
    'bur',
    'bus',
    'cac',
    'cak',
    'caq',
    'cin',
    'coc',
    'cok',
    'con',
    'coq',
    'coz',
    'cuk',
    'cul',
    'cum',
    'cun',
    'cur',
    'dan',
    'daw',
    'day',
    'dem',
    'dev',
    'dic',
    'dik',
    'diq',
    'dix',
    'dom',
    'dot',
    'dud',
    'fag',
    'fak',
    'fan',
    'fap',
    'fas',
    'fek',
    'fel',
    'fez',
    'fis',
    'fob',
    'fok',
    'fot',
    'fuc',
    'fuk',
    'fuq',
    'fut',
    'fux',
    'gad',
    'gal',
    'gan',
    'gar',
    'gat',
    'gay',
    'gec',
    'gey',
    'gid',
    'gil',
    'giz',
    'gog',
    'gop',
    'got',
    'goy',
    'guc',
    'gud',
    'guk',
    'guq',
    'hag',
    'hah',
    'heh',
    'hen',
    'het',
    'hon',
    'hor',
    'huj',
    'hul',
    'hur',
    'hus',
    'jap',
    'jav',
    'jeb',
    'jew',
    'jit',
    'jiz',
    'job',
    'kac',
    'kak',
    'kan',
    'kaq',
    'kar',
    'kaw',
    'kef',
    'kel',
    'ken',
    'kep',
    'kik',
    'kir',
    'koc',
    'kok',
    'koq',
    'kor',
    'kox',
    'kuk',
    'kum',
    'kun',
    'kus',
    'kut',
    'kuz',
    'lam',
    'lan',
    'las',
    'lem',
    'let',
    'lic',
    'lid',
    'lik',
    'lil',
    'liq',
    'lol',
    'lop',
    'lox',
    'lud',
    'lul',
    'lun',
    'lus',
    'luz',
    'maj',
    'mal',
    'meg',
    'meh',
    'mes',
    'mic',
    'mik',
    'min',
    'miq',
    'mor',
    'muf',
    'mul',
    'mun',
    'mut',
    'nad',
    'nas',
    'nib',
    'nig',
    'nim',
    'noq',
    'nun',
    'nut',
    'pad',
    'pah',
    'pap',
    'par',
    'pat',
    'paz',
    'pek',
    'pel',
    'pes',
    'pik',
    'pis',
    'pix',
    'pod',
    'pom',
    'pot',
    'pug',
    'puk',
    'pum',
    'pus',
    'qab',
    'qij',
    'quz',
    'rac',
    'rak',
    'ral',
    'ran',
    'raq',
    'rev',
    'ris',
    'rit',
    'rot',
    'ruc',
    'sac',
    'sak',
    'saq',
    'sat',
    'sek',
    'ser',
    'set',
    'sex',
    'sey',
    'sik',
    'sob',
    'sod',
    'sol',
    'sot',
    'soy',
    'suc',
    'sud',
    'suk',
    'suq',
    'sut',
    'tal',
    'tay',
    'tem',
    'tin',
    'tit',
    'toc',
    'tog',
    'tok',
    'toq',
    'tos',
    'tun',
    'tup',
    'vag',
    'vaj',
    'wac',
    'wah',
    'wak',
    'waq',
    'war',
    'was',
    'wat',
    'wen',
    'wog',
    'wop',
    'xuy',
    'yal',
    'yid',
    'yor',
    'yuk',
    'zak',
    'zeb',
    'zig',
    'zov',
    'zut',
})

_VOWELS = 'aeiou'

_CONSONANTS = ''.join(l for l in string.ascii_lowercase if l not in _VOWELS)


def IsValidWord(word):
  return word not in _INVALID_THREE_LETTER_WORDS


def _ThreeLetterGenerator(validate):
  """Generate random 3-letter words.

  Words are generated in a consonant-vowel-consonant order to be pronounceable.
  A specific word matching this pattern has a 1/21*1/5*1/21 = 1/2205 chance
  of being generated.

  Args:
    validate: bool, True to validate words against the invalid set.

  Returns:
    str, 3-letter word
  """
  while True:
    word = (
        random.choice(_CONSONANTS) + random.choice(_VOWELS) +
        random.choice(_CONSONANTS))
    if not validate or IsValidWord(word):
      return word


def GenerateName(sections=1, separator='-', prefix=None, validate=True):
  """Generate a random string of 3-letter sections.

  Each word has a 1/2205 chance of being generated (see _GenerateThreeLetter).
  Therefore a specific name has a (1/2205)^(sections) chance of being generated.
  For 3 sections, the denominator is over 10.7 billion.

  Args:
    sections: int, number of 3-letter generated sections to include
    separator: str, separator between sections
    prefix: str, prefix of the generated name. This acts like an additional
      section at the start of the name and will be separated from the
      generated sections by the seperator argument, however it does not count
      towards the number of sections specified by the sections argument.
    validate: bool, True to validate sections against invalid word list

  Returns:
    str, generated name
  """
  assert sections > 0
  names = [_ThreeLetterGenerator(validate) for _ in range(sections)]
  if prefix is not None:
    names.insert(0, prefix)
  return separator.join(names)
