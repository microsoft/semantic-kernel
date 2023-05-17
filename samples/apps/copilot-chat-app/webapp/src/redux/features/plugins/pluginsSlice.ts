// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { EnablePluginPayload, initialState, Plugin, Plugins, PluginsState } from './PluginsState';

export const pluginsState = createSlice({
    name: 'plugins',
    initialState,
    reducers: {
        connectPlugin: (state: PluginsState, action: PayloadAction<EnablePluginPayload>) => {
            var plugin: Plugin;
            var authData = action.payload.accessToken;

            switch (action.payload.plugin) {
                case Plugins.MsGraph:
                    plugin = state.MsGraph;
                    break;
                case Plugins.Jira:
                    plugin = state.Jira;                    
                    authData = `${action.payload.email}:${action.payload.accessToken}`;
                    break;
                case Plugins.GitHub:
                    plugin = state.GitHub;
                    break;
                case Plugins.Klarna:
                    plugin = state.Klarna;
                    authData = "klarna-auth-data";
                    break;
            }

            plugin.enabled = true;
            plugin.authData = authData;
            plugin.apiProperties = action.payload.apiProperties;
        },
        disconnectPlugin: (state: PluginsState, action: PayloadAction<Plugins>) => {
            var plugin: Plugin;

            switch (action.payload) {
                case Plugins.MsGraph:
                    plugin = state.MsGraph;
                    break;
                case Plugins.Jira:
                    plugin = state.Jira;
                    break;
                case Plugins.GitHub:
                    plugin = state.GitHub;
                    break;
                case Plugins.Klarna:
                    plugin = state.Klarna;
                    break;
            }

            plugin.enabled = false;
            plugin.authData = undefined;
        },
    },
});

export const { connectPlugin, disconnectPlugin } = pluginsState.actions;

export default pluginsState.reducer;
