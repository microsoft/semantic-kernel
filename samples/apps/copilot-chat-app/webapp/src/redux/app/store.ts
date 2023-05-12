// Copyright (c) Microsoft. All rights reserved.

import { configureStore } from '@reduxjs/toolkit';
import appReducer from '../features/app/appSlice';
import conversationsReducer from '../features/conversations/conversationsSlice';
import { registerSignalREvents, signalRMiddleware, startSignalRConnection } from '../features/message-relay/signalRMiddleware';
import pluginsReducer from '../features/plugins/pluginsSlice';

export const store = configureStore({
    reducer: {
        app: appReducer,
        conversations: conversationsReducer,
        plugins: pluginsReducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(signalRMiddleware)
});

// Start the signalR connection to make sure messages are
// sent to all clients and received by all clients
startSignalRConnection(store);
registerSignalREvents(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
