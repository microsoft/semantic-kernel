// Copyright (c) Microsoft. All rights reserved.

import { AnyAction, Dispatch, MiddlewareAPI, MiddlewareArray, ThunkMiddleware, configureStore } from '@reduxjs/toolkit';
import { AppState } from '../features/app/AppState';
import { ConversationsState } from '../features/conversations/ConversationsState';
import {
    registerSignalREvents,
    signalRMiddleware,
    startSignalRConnection,
} from '../features/message-relay/signalRMiddleware';
import { PluginsState } from '../features/plugins/PluginsState';
import { UsersState } from '../features/users/UsersState';
import resetStateReducer, { resetApp } from './rootReducer';

export type StoreMiddlewareAPI = MiddlewareAPI<Dispatch, RootState>;
export type Store = typeof store;
export const store = configureStore<
    RootState,
    AnyAction,
    MiddlewareArray<
        [ThunkMiddleware<RootState>, (store: StoreMiddlewareAPI) => (next: Dispatch) => (action: any) => any]
    >
>({
    reducer: resetStateReducer,
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(signalRMiddleware),
});

export interface RootState {
    app: AppState;
    conversations: ConversationsState;
    plugins: PluginsState;
    users: UsersState;
}

export const getSelectedChatID = (): string => {
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
