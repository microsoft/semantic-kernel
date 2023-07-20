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
    show: boolean; // Whether to show the feature in the UX
    label: string;
    disabled?: boolean; // Set to true if you don't want the user to control the visibility of this feature or there's no backend support
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
    RLHF, // Reinforcement Learning from Human Feedback
}

export const Features = {
    [FeatureKeys.DarkMode]: {
        show: false,
        label: 'Dark Mode',
    },
    [FeatureKeys.SimplifiedExperience]: {
        show: true,
        label: 'Simplified Chat Experience',
    },
    [FeatureKeys.PluginsPlannersAndPersonas]: {
        show: false,
        label: 'Plugins & Planners & Personas',
        descriptishow: 'The Plans and Persona tabs are hidden until you turn this on',
    },
    [FeatureKeys.AzureContentSafety]: {
        show: false,
        label: 'Azure Content Safety',
        disabled: true,
    },
    [FeatureKeys.AzureCognitiveSearch]: {
        show: false,
        label: 'Azure Cognitive Search',
        disabled: true,
    },
    [FeatureKeys.BotAsDocs]: {
        show: false,
        label: 'Save/Load Chat Sessions',
    },
    [FeatureKeys.MultiUserChat]: {
        show: false,
        label: 'Live Chat Session Sharing',
    },
    [FeatureKeys.RLHF]: {
        show: false,
        label: 'Reinforcement Learning from Human Feedback',
        descriptishow: 'Enable users to vote on model-generated responses. For demonstration purposes only.',
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
        descriptishow: 'The related icons and menu options are hidden until you turn this on',
        features: [FeatureKeys.BotAsDocs, FeatureKeys.MultiUserChat, FeatureKeys.RLHF],
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
