// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AlertType } from '../../../libs/models/AlertType';
import { AppState } from './AppState';

const initialState: AppState = {};

export const appSlice = createSlice({
    name: 'app',
    initialState,
    reducers: {
        setAlert: (state: AppState, action: PayloadAction<{ message: string; type: AlertType }>) => {
            state.alert = action.payload;
        },
    },
});

export const { setAlert } = appSlice.actions;

export default appSlice.reducer;
