// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState, initialChatName, initialState as initialChatState } from './ChatState';

export type Conversations = {
    [key: string]: ChatState;
};

export interface ConversationsState {
    conversations: Conversations;
    selectedId: string;
    botProfilePictureIndex: number;
}

export const initialState: ConversationsState = {
    conversations: {
        [initialChatName]: initialChatState,
    },
    selectedId: initialChatName,
    botProfilePictureIndex: 0,
};

export interface IEditConversationTitle {
    id: string;
    newTitle: string;
}

export interface IUpdateConversation {
    message: ChatMessage;
    chatId?: string;
}