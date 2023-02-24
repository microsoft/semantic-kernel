// Copyright (c) Microsoft. All rights reserved.

export interface IPage {
    num: number;
    content: string;
}

export interface IBookResult {
    outline: string;
    summary: string;
    pages: IPage[];
}
