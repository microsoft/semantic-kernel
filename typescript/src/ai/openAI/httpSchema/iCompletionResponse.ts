/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export interface IChoice {
    text: string;
    index: number;
}

export interface ICompletionResponse {
    choices: IChoice[];
}
