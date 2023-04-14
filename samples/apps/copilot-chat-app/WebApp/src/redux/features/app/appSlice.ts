// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Alert, Alerts, AppState } from './AppState';

const initialState: AppState = {};

export const appSlice = createSlice({
    name: 'app',
    initialState,
    reducers: {
        setAlerts: (state: AppState, action: PayloadAction<Alerts>) => {
            state.alerts = action.payload;
        },
        addAlert: (state: AppState, action: PayloadAction<Alert>) => {
            const keys = Object.keys(state.alerts ?? []);
            let newIndex = keys.length.toString();
            if (keys.length >= 3) {
                newIndex = keys[0];
                delete state.alerts![newIndex];
            }
            state.alerts = { ...state.alerts, [newIndex]: action.payload };
        },
        removeAlert: (state: AppState, action: PayloadAction<string>) => {
            if (state.alerts) delete state.alerts[action.payload];
        },
    },
});

export const { addAlert, removeAlert, setAlerts } = appSlice.actions;

export default appSlice.reducer;
