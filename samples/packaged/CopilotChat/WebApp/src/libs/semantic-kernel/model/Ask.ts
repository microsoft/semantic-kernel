// Copyright (c) Microsoft. All rights reserved.

export interface IAsk {
    value: string;
    inputs?: IAskInput[];
}

export interface IAskInput {
    key: string;
    value: string;
}
