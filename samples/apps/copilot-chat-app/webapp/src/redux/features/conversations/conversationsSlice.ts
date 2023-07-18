// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction, Slice } from '@reduxjs/toolkit';
import { ChatMessageType, IChatMessage, UserFeedback } from '../../../libs/models/ChatMessage';
import { IChatUser } from '../../../libs/models/ChatUser';
import { PlanState } from '../../../libs/models/Plan';
import { ChatState } from './ChatState';
import {
    ConversationInputChange,
    Conversations,
    ConversationsState,
    ConversationSystemDescriptionChange,
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
            frontLoadChat(state, id);
        },
        editConversationInput: (state: ConversationsState, action: PayloadAction<ConversationInputChange>) => {
            const id = action.payload.id;
            const newInput = action.payload.newInput;
            state.conversations[id].input = newInput;
        },
        editConversationSystemDescription: (
            state: ConversationsState,
            action: PayloadAction<ConversationSystemDescriptionChange>,
        ) => {
            const id = action.payload.id;
            const newSystemDescription = action.payload.newSystemDescription;
            state.conversations[id].systemDescription = newSystemDescription;
        },
        editConversationMemoryBalance: (
            state: ConversationsState,
            action: PayloadAction<{id: string, memoryBalance: number}>,
        ) => {
            const id = action.payload.id;
            const newMemoryBalance = action.payload.memoryBalance;
            state.conversations[id].memoryBalance = newMemoryBalance;
        },
        setSelectedConversation: (state: ConversationsState, action: PayloadAction<string>) => {
            state.selectedId = action.payload;
        },
        addConversation: (state: ConversationsState, action: PayloadAction<ChatState>) => {
            const newId = action.payload.id;
            state.conversations = { [newId]: action.payload, ...state.conversations };
            state.selectedId = newId;
        },
        addUserToConversation: (
            state: ConversationsState,
            action: PayloadAction<{ user: IChatUser; chatId: string }>,
        ) => {
            const { user, chatId } = action.payload;
            state.conversations[chatId].users.push(user);
            state.conversations[chatId].userDataLoaded = false;
        },
        setUsersLoaded: (state: ConversationsState, action: PayloadAction<string>) => {
            state.conversations[action.payload].userDataLoaded = true;
        },
        /*
         * updateConversationFromUser() and updateConversationFromServer() both update the conversations state.
         * However they are for different purposes. The former action is for updating the conversation from the
         * webapp and will be captured by the SignalR middleware and the payload will be broadcasted to all clients
         * in the same group.
         * The updateConversationFromServer() action is triggered by the SignalR middleware when a response is received
         * from the webapi.
         */
        updateConversationFromUser: (
            state: ConversationsState,
            action: PayloadAction<{ message: IChatMessage; chatId?: string }>,
        ) => {
            const { message, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            updateConversation(state, id, message);
        },
        updateConversationFromServer: (
            state: ConversationsState,
            action: PayloadAction<{ message: IChatMessage; chatId: string }>,
        ) => {
            const { message, chatId } = action.payload;
            updateConversation(state, chatId, message);
        },
        updateMessageState: (
            state: ConversationsState,
            action: PayloadAction<{ newMessageState: PlanState; messageIndex: number; chatId?: string }>,
        ) => {
            const { newMessageState, messageIndex, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages[messageIndex].state = newMessageState;
            frontLoadChat(state, id);
        },
        /*
         * updateUserIsTyping() and updateUserIsTypingFromServer() both update a user's typing state.
         * However they are for different purposes. The former action is for updating an user's typing state from
         * the webapp and will be captured by the SignalR middleware and the payload will be broadcasted to all clients
         * in the same group.
         * The updateUserIsTypingFromServer() action is triggered by the SignalR middleware when a state is received
         * from the webapi.
         */
        updateUserIsTyping: (
            state: ConversationsState,
            action: PayloadAction<{ userId: string; chatId: string; isTyping: boolean }>,
        ) => {
            const { userId, chatId, isTyping } = action.payload;
            updateUserTypingState(state, userId, chatId, isTyping);
        },
        updateUserIsTypingFromServer: (
            state: ConversationsState,
            action: PayloadAction<{ userId: string; chatId: string; isTyping: boolean }>,
        ) => {
            const { userId, chatId, isTyping } = action.payload;
            updateUserTypingState(state, userId, chatId, isTyping);
        },
        updateBotResponseStatusFromServer: (
            state: ConversationsState,
            action: PayloadAction<{ chatId: string; status: string }>,
        ) => {
            const { chatId, status } = action.payload;
            const conversation = state.conversations[chatId];
            conversation.botResponseStatus = status;
        },
        setUserFeedback: (
            state: ConversationsState,
            action: PayloadAction<{ userFeedback: UserFeedback; messageIndex: number; chatId?: string }>,
        ) => {
            const { userFeedback, messageIndex, chatId } = action.payload;
            const id = chatId ?? state.selectedId;
            state.conversations[id].messages[messageIndex].userFeedback = userFeedback;
            frontLoadChat(state, id);
        },
    },
});

export const {
    setConversations,
    editConversationTitle,
    editConversationInput,
    editConversationSystemDescription,
    editConversationMemoryBalance,
    setSelectedConversation,
    addConversation,
    updateConversationFromUser,
    updateConversationFromServer,
    updateMessageState,
    updateUserIsTyping,
    updateUserIsTypingFromServer,
    setUsersLoaded,
    setUserFeedback,
} = conversationsSlice.actions;

export default conversationsSlice.reducer;

const frontLoadChat = (state: ConversationsState, id: string) => {
    const conversation = state.conversations[id];
    const { [id]: _, ...rest } = state.conversations;
    state.conversations = { [id]: conversation, ...rest };
};

const updateConversation = (state: ConversationsState, chatId: string, message: IChatMessage) => {
    const requestUserFeedback = message.userId === 'bot' && message.type === ChatMessageType.Message;
    state.conversations[chatId].messages.push({
        ...message,
        userFeedback: requestUserFeedback ? UserFeedback.Requested : undefined,
    });
    frontLoadChat(state, chatId);
};

const updateUserTypingState = (state: ConversationsState, userId: string, chatId: string, isTyping: boolean) => {
    const conversation = state.conversations[chatId];
    const user = conversation.users.find((u) => u.id === userId);
    if (user) {
        user.isTyping = isTyping;
    }
};
