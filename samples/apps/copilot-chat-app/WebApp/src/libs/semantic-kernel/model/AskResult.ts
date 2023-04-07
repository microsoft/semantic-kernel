// Copyright (c) Microsoft. All rights reserved.

export interface IAskResult {
    value: string;
    variables: Variables;
}

export type Variables = { [key: string]: string }[];