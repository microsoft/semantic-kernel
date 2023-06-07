// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction, Slice } from '@reduxjs/toolkit';
import { ChatMessageState, IChatMessage } from '../../../libs/models/ChatMessage';
import { ChatState } from './ChatState';
import { ConversationInputChange, Conversations, ConversationsState, ConversationTitleChange, initialState } from './ConversationsState';

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
        updateMessageState: (
            state: ConversationsState,
            action: PayloadAction<{ newMessageState: ChatMessageState; messageIndex: number; chatId?: string }>,
        ) => {
            const { newMessageState, messageIndex, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages[messageIndex].state = newMessageState;
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
    updateMessageState,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;

const frontLoadChat = (state: ConversationsState, id: string) => {
    const conversation = state.conversations[id];
    delete state.conversations[id];
    state.conversations = { [id]: conversation, ...state.conversations };
};
