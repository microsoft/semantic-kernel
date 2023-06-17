// Copyright (c) Microsoft. All rights reserved.

import { configureStore } from '@reduxjs/toolkit';
import { AppState } from '../features/app/AppState';
import { ConversationsState } from '../features/conversations/ConversationsState';
import { PluginsState } from '../features/plugins/PluginsState';
import resetStateReducer, { resetApp } from './rootReducer';

export const store = configureStore({
    reducer: resetStateReducer,
});

export type RootState = {
    app: AppState;
    conversations: ConversationsState;
    plugins: PluginsState;
};

export type AppDispatch = typeof store.dispatch;

// Function to reset the app state
export const resetState = () => {
    store.dispatch(resetApp());
};
