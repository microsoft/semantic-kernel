// Copyright (c) Microsoft. All rights reserved.

export interface ChatMessage {
    timestamp: number;
    sender: 'bot' | string;
    content: string;
    id?: string;
    debug?: string;
}