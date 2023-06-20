// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState } from './ChatState';

export type Conversations = {
    [key: string]: ChatState;
};

export interface ConversationsState {
    conversations: Conversations;
    selectedId: string;
    loggedInUserInfo?: LoggedInUserInfo;
}

export interface LoggedInUserInfo {
    id: string;
    email: string;
    fullName: string;
}

export const initialState: ConversationsState = {
    conversations: {},
    selectedId: '',
    loggedInUserInfo: undefined,
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
