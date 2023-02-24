// Copyright (c) Microsoft. All rights reserved.

export interface IAsk {
    value: string;
    skills?: string[];
    inputs?: IAskInput[];
}

export interface IAskInput {
    key: string;
    value: string;
}
