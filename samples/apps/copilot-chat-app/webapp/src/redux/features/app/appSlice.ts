// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AlertType } from '../../../libs/models/AlertType';
import { ActiveUserInfo, Alert, AppState } from './AppState';

const initialState: AppState = {
    alerts: [
        {
            message:
                'Copilot chat is designed for internal use only. By using this chat bot, you agree to not to share confidential or customer information or store sensitive information in chat history. Further, you agree that Copilot chat can collect and retain your chat history for service improvement.',
            type: AlertType.Info,
        },
    ],
};

export const appSlice = createSlice({
    name: 'app',
    initialState,
    reducers: {
        setAlerts: (state: AppState, action: PayloadAction<Alert[]>) => {
            state.alerts = action.payload;
        },
        addAlert: (state: AppState, action: PayloadAction<Alert>) => {
            if (state.alerts.length === 3) {
                state.alerts.shift();
            }
            state.alerts.push(action.payload);
        },
        removeAlert: (state: AppState, action: PayloadAction<number>) => {
            state.alerts.splice(action.payload, 1);
        },
        setActiveUserInfo: (state: AppState, action: PayloadAction<ActiveUserInfo>) => {
            state.activeUserInfo = action.payload;
        },
    },
});

export const { addAlert, removeAlert, setAlerts, setActiveUserInfo } = appSlice.actions;

export default appSlice.reducer;
