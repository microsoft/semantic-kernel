// Copyright (c) Microsoft. All rights reserved.

export interface ChatMemorySource {
    id: string;
    chatId: string;
    sourceType: string;
    name: string;
    hyperlink?: string;
    sharedBy: string;
    createdOn: number;
}
