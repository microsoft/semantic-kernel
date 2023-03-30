// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatUser } from '../../../libs/models/ChatUser';
import { ChatState, initialState } from './ChatState';

export const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        setAudience: (state: ChatState, action: PayloadAction<ChatUser[]>) => {
            state.audience = action.payload;
        },
        setChatUserTyping: (state: ChatState, action: PayloadAction<{ id: string; timestamp: number }>) => {
            const user = state.audience.find((u) => u.id === action.payload.id);
            if (user) {
                user.lastTypingTimestamp = action.payload.timestamp;
            }
        },
        setBotTyping: (state: ChatState, action: PayloadAction<boolean>) => {
            state.botTypingTimestamp = action.payload ? Date.now() : 0;
        },
        setChatMessages: (state: ChatState, action: PayloadAction<ChatMessage[]>) => {
            state.messages = action.payload;
        },
        addMessage: (state: ChatState, action: PayloadAction<ChatMessage>) => {
            state.messages = [...state.messages, action.payload];
        },
        setChat: (state: ChatState, action: PayloadAction<ChatState>) => {
            const newState = action.payload;
            state.messages = newState.messages;
            state.audience = newState.audience;
            state.botTypingTimestamp = newState.botTypingTimestamp;
            state.id = newState.id;
        },
    },
});

export const {
    setAudience,
    setChatUserTyping,
    setBotTyping,
    setChatMessages,
    addMessage,
    setChat
} = chatSlice.actions;

export default chatSlice.reducer;
