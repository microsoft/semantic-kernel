/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
export enum ChatUser {
    USER = "USER",
    ASSISTANT = "ASSISTANT",
}

export interface ChatMessageContent {
    sender: ChatUser;
    content?: unknown;
    action?: string;
    timestamp?: string;
}
