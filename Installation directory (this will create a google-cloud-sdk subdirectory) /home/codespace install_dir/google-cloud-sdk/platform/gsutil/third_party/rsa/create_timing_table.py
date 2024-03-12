#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import time
import rsa

poolsize = 8
accurate = True


def run_speed_test(bitsize):
    iterations = 0
    start = end = time.time()

    # At least a number of iterations, and at least 2 seconds
    while iterations < 10 or end - start < 2:
        iterations += 1
        rsa.newkeys(bitsize, accurate=accurate, poolsize=poolsize)
        end = time.time()

    duration = end - start
    dur_per_call = duration / iterations

    print('%5i bit: %9.3f sec. (%i iterations over %.1f seconds)' %
          (bitsize, dur_per_call, iterations, duration))


if __name__ == '__main__':
    for bitsize in (128, 256, 384, 512, 1024, 2048, 3072, 4096):
        run_speed_test(bitsize)
