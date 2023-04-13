// Copyright (c) Microsoft. All rights reserved.

export interface ChatMessage {
    timestamp: number;
    userName: 'bot' | string;
    userId: string;
    content: string;
    id?: string;
    fromUser: boolean;
    debug?: string;
}
