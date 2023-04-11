// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatState } from './ChatState';
import {
    Conversations,
    ConversationsState,
    IEditConversationTitle,
    initialState,
    IUpdateConversation
} from './ConversationsState';

export const conversationsSlice = createSlice({
    name: 'hub',
    initialState,
    reducers: {
        incrementBotProfilePictureIndex: (state: ConversationsState) => {
            state.botProfilePictureIndex = ++state.botProfilePictureIndex % 5;
        },
        setConversations: (state: ConversationsState, action: PayloadAction<Conversations>) => {
            state.conversations = action.payload;
        },
        editConversationTitle: (state: ConversationsState, action: PayloadAction<IEditConversationTitle>) => {
            state.conversations[action.payload.id].title = action.payload.newTitle;
            frontloadChat(state, action.payload.id);
        },
        setSelectedConversation: (state: ConversationsState, action: PayloadAction<string>) => {
            state.selectedId = action.payload;
        },
        addConversation: (state: ConversationsState, action: PayloadAction<ChatState>) => {
            const newId = action.payload.id ?? '';
            state.conversations = { [newId]: action.payload, ...state.conversations };
        },
        updateConversation: (state: ConversationsState, action: PayloadAction<IUpdateConversation>) => {
            const { message, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages.push(message);
            frontloadChat(state, id);
        },
    },
});

export const {
    incrementBotProfilePictureIndex,
    setConversations,
    editConversationTitle,
    setSelectedConversation,
    addConversation,
    updateConversation,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;

const frontloadChat = (state: ConversationsState, id: string) => {
    const conversation = state.conversations[id];
    delete state.conversations[id];
    state.conversations = { [id]: conversation, ...state.conversations };
};