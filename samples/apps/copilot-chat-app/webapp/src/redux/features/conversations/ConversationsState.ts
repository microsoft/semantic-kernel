// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState } from './ChatState';

export type Conversations = {
    [key: string]: ChatState;
};

export interface ConversationsState {
    conversations: Conversations;
    selectedId: string;
    loggedInUserId: string;
}

export const initialState: ConversationsState = {
    conversations: {},
    selectedId: '',
    loggedInUserId: '',
};

export type UpdateConversationPayload = {
    id: string;
    messages: IChatMessage[];
};

export interface ConversationTitleChange {
    id: string;
    newTitle: string;
}

export interface ConversationInputChange {
    id: string;
    newInput: string;
}
