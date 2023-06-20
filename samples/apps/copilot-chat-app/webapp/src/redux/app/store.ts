// Copyright (c) Microsoft. All rights reserved.

import { configureStore } from '@reduxjs/toolkit';
import { AppState } from '../features/app/AppState';
import { ConversationsState } from '../features/conversations/ConversationsState';
import { registerSignalREvents, signalRMiddleware, startSignalRConnection } from '../features/message-relay/signalRMiddleware';
import { PluginsState } from '../features/plugins/PluginsState';
import resetStateReducer, { resetApp } from './rootReducer';

export const store = configureStore({
    reducer: resetStateReducer,
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(signalRMiddleware)
});

export type RootState = {
    app: AppState;
    conversations: ConversationsState;
    plugins: PluginsState;
};

export const getSelectedChatID = () : string => {
    return store.getState().conversations.selectedId;
};

// Start the signalR connection to make sure messages are
// sent to all clients and received by all clients
startSignalRConnection(store);
registerSignalREvents(store);

export type AppDispatch = typeof store.dispatch;

// Function to reset the app state
export const resetState = () => {
    store.dispatch(resetApp());
};
