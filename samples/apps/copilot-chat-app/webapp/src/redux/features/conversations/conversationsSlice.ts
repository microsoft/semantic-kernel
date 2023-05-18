// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatMessageState, IChatMessage } from '../../../libs/models/ChatMessage';
import { IChatUser } from '../../../libs/models/ChatUser';
import { ChatState, FileUploadedAlert } from './ChatState';
import { Conversations, ConversationsState, ConversationTitleChange, initialState } from './ConversationsState';

export const conversationsSlice = createSlice({
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
            frontLoadChat(state, id);
        },
        setSelectedConversation: (state: ConversationsState, action: PayloadAction<string>) => {
            state.selectedId = action.payload;
        },
        addConversation: (state: ConversationsState, action: PayloadAction<ChatState>) => {
            const newId = action.payload.id ?? '';
            state.conversations = { [newId]: action.payload, ...state.conversations };
            state.selectedId = newId;
        },
        addUserToConversation: (state: ConversationsState, action: PayloadAction<{ user: IChatUser, chatId: string }>) => {
            const { user, chatId } = action.payload;
            state.conversations[chatId].users.push(user);
        },
        /*
        * updateConversationFromUser() and updateConversationFromServer() both update the conversations state.
        * However they are for different purposes. The former action is for updating the conversation from the
        * user and will be captured by the SignalR middleware and the payload will be broadcasted to all clients
        * in the same group.
        * The updateConversationFromUser() action is triggered by the SignalR middleware when a response is received.
        */
        updateConversationFromUser: (
            state: ConversationsState,
            action: PayloadAction<{ message: IChatMessage; chatId?: string }>,
        ) => {
            const { message, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages.push(message);
            frontLoadChat(state, id);
        },
        updateConversationFromServer: (
            state: ConversationsState,
            action: PayloadAction<{ message: IChatMessage; chatId: string }>,
        ) => {
            const { message, chatId } = action.payload;
            state.conversations[chatId].messages.push(message);
            frontLoadChat(state, chatId);
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
        updateUserIsTyping: (state: ConversationsState, action: PayloadAction<{ userId: string; chatId: string; isTyping: boolean }>) => {
            const { userId, chatId, isTyping } = action.payload;
            const conversation = state.conversations[chatId];
            const user = conversation.users.find(u => u.id === userId);
            if (user) {
                user.isTyping = isTyping;
            }
        },
        updateUserIsTypingFromServer: (state: ConversationsState, action: PayloadAction<{ userId: string; chatId: string; isTyping: boolean }>) => {
            const { userId, chatId, isTyping } = action.payload;
            const conversation = state.conversations[chatId];
            const user = conversation.users.find(u => u.id === userId);
            if (user) {
                user.isTyping = isTyping;
            }
        },
        updateBotIsTypingFromServer: (state: ConversationsState, action: PayloadAction<{ chatId: string; isTyping: boolean }>) => {
            const { chatId, isTyping } = action.payload;
            const conversation = state.conversations[chatId];
            conversation.isBotTyping = isTyping;
        },
        updateFileUploadedFromUser: (
            state: ConversationsState,
            action: PayloadAction<FileUploadedAlert>,
        ) => {
            const alert = action.payload;
            const id = action.payload.id;
            state.alerts[id] = alert;
            frontLoadChat(state, id);
        },
    },
});

export const {
    setConversations,
    editConversationTitle,
    setSelectedConversation,
    addConversation,
    updateConversationFromUser,
    updateConversationFromServer,
    updateMessageState,
    updateUserIsTyping,
    updateUserIsTypingFromServer,
    updateFileUploadedFromUser,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;

const frontLoadChat = (state: ConversationsState, id: string) => {
    const conversation = state.conversations[id];
    delete state.conversations[id];
    state.conversations = { [id]: conversation, ...state.conversations };
};
