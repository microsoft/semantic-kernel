// Copyright (c) Microsoft. All rights reserved.

export interface ChatMessage {
    timestamp: number;
    senderName: 'bot' | string;
    senderId: string;
    content: string;
    id?: string;
    debug?: string;
}