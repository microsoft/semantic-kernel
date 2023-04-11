// Copyright (c) Microsoft. All rights reserved.

export interface IAskResult {
    value: string;
    variables: Variables;
}

type Variables = {
    [key: string]: string;
};