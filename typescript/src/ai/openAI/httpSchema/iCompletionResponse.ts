// Copyright (c) Microsoft Corporation. All rights reserved.

export interface IChoice {
    text: string;
    index: number;
}

export interface ICompletionResponse {
    choices: IChoice[];
}
