// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction, Slice } from '@reduxjs/toolkit';
import { IChatMessage } from '../../../libs/models/ChatMessage';
import { PlanState } from '../../../libs/models/Plan';
import { ChatState } from './ChatState';
import {
    ConversationInputChange,
    Conversations,
    ConversationsState,
    ConversationTitleChange,
    initialState,
} from './ConversationsState';

export const conversationsSlice: Slice<ConversationsState> = createSlice({
    name: 'conversations',
    initialState,
    reducers: {
        setConversations: (state: ConversationsState, action: PayloadAction<Conversations>) => {
            state.conversations = action.payload;
        },
        editConversationTitle: (state: ConversationsState, action: PayloadAction<ConversationTitleChange>) => {
            const id = action.payload.id;
            const newTitle = action.payload.newTitle;
            state.conversations[id].title = newTitle;
            state.conversations[id].lastUpdatedTimestamp = new Date().getTime();
            frontLoadChat(state, id);
        },
        editConversationInput: (state: ConversationsState, action: PayloadAction<ConversationInputChange>) => {
            const id = action.payload.id;
            const newInput = action.payload.newInput;
            state.conversations[id].input = newInput;
        },
        setSelectedConversation: (state: ConversationsState, action: PayloadAction<string>) => {
            state.selectedId = action.payload;
        },
        addConversation: (state: ConversationsState, action: PayloadAction<ChatState>) => {
            const newId = action.payload.id ?? '';
            state.conversations = { [newId]: action.payload, ...state.conversations };
            state.selectedId = newId;
        },
        updateConversation: (
            state: ConversationsState,
            action: PayloadAction<{ message: IChatMessage; chatId?: string }>,
        ) => {
            const { message, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages.push(message);
            state.conversations[id].lastUpdatedTimestamp = new Date().getTime();
            frontLoadChat(state, id);
        },
        updateMessage: (
            state: ConversationsState,
            action: PayloadAction<{
                content: string;
                messageIndex: number;
                chatId?: string;
                planState?: PlanState;
            }>,
        ) => {
            const { content, messageIndex, chatId, planState } = action.payload;
            const id = chatId ?? state.selectedId;
            if (planState) state.conversations[id].messages[messageIndex].state = planState;
            state.conversations[id].messages[messageIndex].content = content;
            frontLoadChat(state, id);
        },
    },
});

export const {
    setConversations,
    editConversationTitle,
    editConversationInput,
    setSelectedConversation,
    addConversation,
    updateConversation,
    updateMessage,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;

const frontLoadChat = (state: ConversationsState, id: string) => {
    const conversation = state.conversations[id];
    delete state.conversations[id];
    state.conversations = { [id]: conversation, ...state.conversations };
};
