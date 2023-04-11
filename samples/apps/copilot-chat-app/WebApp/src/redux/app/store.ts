// Copyright (c) Microsoft. All rights reserved.

import { configureStore } from '@reduxjs/toolkit';
import appReducer from '../features/app/appSlice';
import conversationsReducer from '../features/conversations/conversationsSlice';

export const store = configureStore({
    reducer: {
        app: appReducer,
        conversations: conversationsReducer,
    },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
