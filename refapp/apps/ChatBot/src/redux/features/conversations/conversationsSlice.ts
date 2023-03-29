// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState } from '../chat/ChatState';
import { Conversation, ConversationsState, ConversationTitleChange, initialState } from './ConversationsState';

export const conversationsSlice = createSlice({
    name: 'hub',
    initialState,
    reducers: {
        setConversations: (state: ConversationsState, action: PayloadAction<Conversation>) => {
            state.conversations = action.payload;
        },
        editConversationTitle: (state: ConversationsState, action: PayloadAction<ConversationTitleChange>) => {
            const newId = action.payload.newId;
            state.conversations[action.payload.id].id = newId;
            const updatedChat = state.conversations[action.payload.id];
            delete state.conversations[action.payload.id];
            state.conversations = { [newId]: updatedChat , ...state.conversations}
            state.selectedId = action.payload.newId;
        },
        setSelectedConversation: (state: ConversationsState, action: PayloadAction<string>) => {
            state.selectedId = action.payload;
        },
        addConversation: (state: ConversationsState, action: PayloadAction<ChatState>) => {
            const newId = action.payload.id ?? '';
            state.conversations = { [newId]: action.payload, ...state.conversations };
        },
        updateConversation: (state: ConversationsState, action: PayloadAction<{ message: ChatMessage, chatId?: string}>) => {
            state.conversations[action.payload.chatId ?? state.selectedId].messages.push(action.payload.message);
        },
    },
});

export const { setConversations, editConversationTitle, setSelectedConversation, addConversation, updateConversation } = conversationsSlice.actions;

export default conversationsSlice.reducer;
