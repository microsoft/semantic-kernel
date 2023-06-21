// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { EnablePluginPayload, initialState, Plugin, Plugins, PluginsState } from './PluginsState';

export const pluginsState = createSlice({
    name: 'plugins',
    initialState,
    reducers: {
        connectPlugin: (state: PluginsState, action: PayloadAction<EnablePluginPayload>) => {
            let plugin: Plugin;
            let authData = action.payload.accessToken;

            switch (action.payload.plugin) {
                case Plugins.MsGraph:
                    plugin = state.MsGraph;
                    break;
                case Plugins.Jira:
                    plugin = state.Jira;
                    authData = `${action.payload.email as string}:${action.payload.accessToken as string}`;
                    break;
                case Plugins.GitHub:
                    plugin = state.GitHub;
                    break;
                case Plugins.Klarna:
                    plugin = state.Klarna;
                    authData = 'klarna-auth-data';
                    break;
            }

            plugin.enabled = true;
            plugin.authData = authData;
            plugin.apiProperties = action.payload.apiProperties;
        },
        disconnectPlugin: (state: PluginsState, action: PayloadAction<Plugins>) => {
            switch (action.payload) {
                case Plugins.MsGraph:
                    state.MsGraph = initialState.Jira;
                    break;
                case Plugins.Jira:
                    state.Jira = initialState.MsGraph;
                    break;
                case Plugins.GitHub:
                    state.GitHub = initialState.GitHub;
                    break;
                case Plugins.Klarna:
                    state.Klarna = initialState.Klarna;
                    break;
            }
        },
    },
});

export const { connectPlugin, disconnectPlugin } = pluginsState.actions;

export default pluginsState.reducer;
