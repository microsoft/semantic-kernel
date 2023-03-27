// Copyright (c) Microsoft. All rights reserved.

import { mockConversations } from "../../../mock-data";
import { ChatState } from "../chat/ChatState";

export type Conversation = {
    [key:string]: ChatState
}

export interface ConversationsState {
    conversations: Conversation;
    selectedId: string;
}

// TODO: revert
export const initialState: ConversationsState = {
    ...mockConversations,
    selectedId: '',
};

export interface ConversationTitleChange {
    id: string, 
    newId: string
}