// Copyright (c) Microsoft. All rights reserved.

import { combineReducers, createAction, Reducer } from '@reduxjs/toolkit';
import appReducer from '../features/app/appSlice';
import conversationsReducer from '../features/conversations/conversationsSlice';
import pluginsReducer from '../features/plugins/pluginsSlice';

// Define a top-level root state reset action
export const resetApp = createAction('resetApp');

// Define a root reducer that combines all the reducers
const rootReducer: Reducer = combineReducers({
    app: appReducer,
    conversations: conversationsReducer,
    plugins: pluginsReducer,
});

// Define a special resetApp reducer that handles resetting the entire state
export const resetAppReducer: Reducer = (state: any, action: any) => {
    if (action.type === resetApp.type) {
        state = {
            // Explicitly call each individual reducer with undefined state.
            // This allows the reducers to handle the reset logic and return the initial state with the correct type.
            app: appReducer(undefined, action),
            conversations: conversationsReducer(undefined, action),
            plugins: pluginsReducer(undefined, action),
        };
    }

    return rootReducer(state, action);
};

export default resetAppReducer;
