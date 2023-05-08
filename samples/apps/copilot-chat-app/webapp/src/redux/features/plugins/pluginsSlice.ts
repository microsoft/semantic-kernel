// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Buffer } from 'buffer';
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

                    // TODO: Aman to change with Jira integration
                    const encodedData = Buffer.from(
                        `${action.payload.username}:${action.payload.accessToken}`,
                    ).toString('base64');
                    authData = encodedData;

                    break;
                case Plugins.GitHub:
                    plugin = state.GitHub;
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
            }

            plugin.enabled = false;
            plugin.authData = undefined;
        },
    },
});

export const { connectPlugin, disconnectPlugin } = pluginsState.actions;

export default pluginsState.reducer;
