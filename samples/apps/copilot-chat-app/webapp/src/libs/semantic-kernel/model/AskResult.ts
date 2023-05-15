// Copyright (c) Microsoft. All rights reserved.

export interface IAskResult {
    value: string;
    variables: Variable[];
}

export type Variable = {
    key: string;
    value: string;
};
