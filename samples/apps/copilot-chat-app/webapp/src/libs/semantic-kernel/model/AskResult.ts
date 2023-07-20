// Copyright (c) Microsoft. All rights reserved.

export interface IAskResult {
    value: string;
    variables: Variable[];
}

export interface Variable {
    key: string;
    value: string;
}
