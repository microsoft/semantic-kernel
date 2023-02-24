// Copyright (c) Microsoft. All rights reserved.

import { IAskInput } from './Ask';

export interface IAskResult {
    value: string;

    state: IAskInput[];
}
