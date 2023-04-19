// Copyright (c) Microsoft. All rights reserved.

export enum AuthorRoles {
    User = 0,
    Bot,
    Participant
}

export interface ChatMessage {
    timestamp: number;
    userName: 'bot' | string;
    userId: string;
    content: string;
    id?: string;
    authorRole: AuthorRoles;
    debug?: string;
}

