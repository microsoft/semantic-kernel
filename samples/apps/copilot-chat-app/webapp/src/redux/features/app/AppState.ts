// Copyright (c) Microsoft. All rights reserved.

import { AlertType } from '../../../libs/models/AlertType';

export interface ActiveUserInfo {
    id: string;
    email: string;
    username: string;
}

export interface Alert {
    message: string;
    type: AlertType;
}

interface Feature {
    enabled: boolean;
    label: string;
    disabled?: boolean;
    description?: string;
}

export interface Setting {
    title: string;
    description?: string;
    features: FeatureKeys[];
    stackVertically?: boolean;
    learnMoreLink?: string;
}

export interface TokenUsages {
    prompt: number;
    dependency: number;
}

export interface AppState {
    alerts: Alert[];
    activeUserInfo?: ActiveUserInfo;
    features: Record<FeatureKeys, Feature>;
    settings: Setting[];
    // Total usage across all chats by app session
    tokenUsage: TokenUsages;
}

export enum FeatureKeys {
    DarkMode,
    SimplifiedExperience,
    PluginsPlannersAndPersonas,
    AzureContentSafety,
    AzureCognitiveSearch,
    BotAsDocs,
    MultiUserChat,
}

export const Features = {
    [FeatureKeys.DarkMode]: {
        enabled: false,
        label: 'Dark Mode',
    },
    [FeatureKeys.SimplifiedExperience]: {
        enabled: true,
        label: 'Simplified Chat Experience',
    },
    [FeatureKeys.PluginsPlannersAndPersonas]: {
        enabled: true,
        label: 'Plugins & Planners & Personas',
        description: 'The Plans and Persona tabs are hidden until you turn this on',
    },
    [FeatureKeys.AzureContentSafety]: {
        enabled: false,
        label: 'Azure Content Safety',
        disabled: true,
    },
    [FeatureKeys.AzureCognitiveSearch]: {
        enabled: false,
        label: 'Azure Cognitive Search',
        disabled: true,
    },
    [FeatureKeys.BotAsDocs]: {
        enabled: false,
        label: 'Save/Load Chat Sessions',
    },
    [FeatureKeys.MultiUserChat]: {
        enabled: false,
        label: 'Live Chat Session Sharing',
    },
};

export const Settings = [
    {
        // Basic settings has to stay at the first index. Add all new settings to end of array.
        title: 'Basic',
        features: [FeatureKeys.DarkMode, FeatureKeys.PluginsPlannersAndPersonas],
        stackVertically: true,
    },
    {
        title: 'Display',
        features: [FeatureKeys.SimplifiedExperience],
        stackVertically: true,
    },
    {
        title: 'Azure AI',
        features: [FeatureKeys.AzureContentSafety, FeatureKeys.AzureCognitiveSearch],
        stackVertically: true,
    },
    {
        title: 'Experimental',
        description: 'The related icons and menu options are hidden until you turn this on',
        features: [FeatureKeys.BotAsDocs, FeatureKeys.MultiUserChat],
    },
];

export const initialState: AppState = {
    alerts: [
        {
            message:
                'By using Chat Copilot, you agree to protect sensitive data, not store it in chat, and allow chat history collection for service improvements. This tool is for internal use only.',
            type: AlertType.Info,
        },
    ],
    features: Features,
    settings: Settings,
    tokenUsage: {
        prompt: 0,
        dependency: 0,
    },
};
