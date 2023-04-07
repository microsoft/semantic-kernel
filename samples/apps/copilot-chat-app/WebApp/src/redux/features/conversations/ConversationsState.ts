// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from "../../../libs/models/ChatMessage";
import { ChatState, initialChatName, initialState as initialChatState } from "../chat/ChatState";

export type Conversation = {
    [key:string]: ChatState
}

export interface ConversationsState {
    conversations: Conversation;
    selectedId: string;
}

export const initialState: ConversationsState = {
    conversations: {
        [initialChatName]: initialChatState
    },
    selectedId: initialChatName,
};

export type UpdateConversationPayload = {
    id: string,
    messages: ChatMessage[]
}

export interface ConversationTitleChange {
    id: string, 
    newId: string
}