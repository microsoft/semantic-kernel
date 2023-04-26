// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Buffer } from 'buffer';
import { EnablePluginPayload, initialState, Plugins, PluginsState } from './PluginsState';

export const pluginsState = createSlice({
    name: 'plugins',
    initialState,
    reducers: {
        connectPlugin: (state: PluginsState, action: PayloadAction<EnablePluginPayload>) => {
            switch (action.payload.plugin) {
                case Plugins.MsGraph:
                    state.MsGraph.enabled = true;
                    state.MsGraph.authData = action.payload.accessToken;
                    return;
                case Plugins.Jira:
                    state.Jira.enabled = true;
                    const encodedData = Buffer.from(
                        `${action.payload.username}:${action.payload.accessToken}`,
                    ).toString('base64');
                    state.Jira.authData = encodedData;
                    return;
                case Plugins.GitHub:
                    state.GitHub.enabled = true;
                    state.GitHub.authData = action.payload.accessToken;
                    return;
            }
        },
        disconnectPlugin: (state: PluginsState, action: PayloadAction<Plugins>) => {
            switch (action.payload) {
                case Plugins.MsGraph:
                    state.MsGraph.enabled = false;
                    state.MsGraph.authData = undefined;
                    return;
                case Plugins.Jira:
                    state.Jira.enabled = false;
                    state.Jira.authData = undefined;
                    return;
                case Plugins.GitHub:
                    state.GitHub.enabled = false;
                    state.GitHub.authData = undefined;
                    return;
            }
        },
    },
});

export const { connectPlugin, disconnectPlugin } = pluginsState.actions;

export default pluginsState.reducer;
