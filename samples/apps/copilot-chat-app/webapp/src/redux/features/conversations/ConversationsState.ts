// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState, FileUploadedAlert } from './ChatState';

export type Conversations = {
    [key: string]: ChatState;
};

export type Alerts = {
    [key: string]: FileUploadedAlert;
};

export interface ConversationsState {
    conversations: Conversations;
    alerts: Alerts;
    selectedId: string;
}

export const initialState: ConversationsState = {
    conversations: {},
    alerts: {},
    selectedId: '',
};

export type UpdateConversationPayload = {
    id: string;
    messages: IChatMessage[];
};

export interface ConversationTitleChange {
    id: string;
    newTitle: string;
}
