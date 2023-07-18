// Copyright (c) Microsoft. All rights reserved.

import { Constants } from '../../../Constants';
import GithubIcon from '../../../assets/plugin-icons/github.png';
import JiraIcon from '../../../assets/plugin-icons/jira.png';
import KlarnaIcon from '../../../assets/plugin-icons/klarna.png';
import GraphIcon from '../../../assets/plugin-icons/ms-graph.png';

/*
 * For each OpenAPI Spec you're supporting in the Kernel,
 * add all the relevant information here.
 */
export const enum BuiltInPlugins {
    MsGraph = 'Microsoft Graph',
    Jira = 'Jira',
    GitHub = 'GitHub',
    Klarna = 'Klarna Shopping',
}

export const enum AuthHeaderTags {
    MsGraph = 'graph',
    Jira = 'jira',
    GitHub = 'github',
    Klarna = 'klarna',
}

export interface PluginAuthRequirements {
    username?: boolean;
    email?: boolean;
    password?: boolean;
    personalAccessToken?: boolean;
    OAuth?: boolean;
    Msal?: boolean;
    scopes?: string[];
    helpLink?: string;
}

// Additional information required to enable OpenAPI skills, i.e., server-url
// Key should be the property name and in kebab case (valid format for request header),
// make sure it matches exactly with the property name the API requires
export type AdditionalApiProperties = Record<
    string,
    {
        required: boolean;
        helpLink?: string;
        value?: string;
        description?: string;
    }
>;

export interface Plugin {
    name: BuiltInPlugins | string;
    nameForModel?: string;
    publisher: string;
    description: string;
    enabled: boolean;
    authRequirements: PluginAuthRequirements;
    headerTag: AuthHeaderTags | string;
    icon: string; // Can be imported as shown above or direct URL
    authData?: string; // token or encoded auth header value
    apiProperties?: AdditionalApiProperties;
    manifestDomain?: string; // Website domain hosting the OpenAI Plugin Manifest file for custom plugins
}

export interface PluginsState {
    plugins: Plugins;
}

export type Plugins = Record<string, Plugin>;

export const initialState: PluginsState = {
    plugins: {
        [BuiltInPlugins.MsGraph]: {
            name: BuiltInPlugins.MsGraph,
            publisher: 'Microsoft',
            description: 'Use your Microsoft Account to access your personal Graph information and Microsoft services.',
            enabled: false,
            authRequirements: {
                Msal: true,
                scopes: Constants.msGraphPluginScopes,
            },
            headerTag: AuthHeaderTags.MsGraph,
            icon: GraphIcon,
        },
        [BuiltInPlugins.Jira]: {
            name: BuiltInPlugins.Jira,
            publisher: 'Atlassian',
            description:
                'Authorize Chat Copilot to link with Jira and retrieve specific issues by providing the issue key.',
            enabled: false,
            authRequirements: {
                email: true,
                personalAccessToken: true,
                helpLink: 'https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/',
            },
            icon: JiraIcon,
            headerTag: AuthHeaderTags.Jira,
            apiProperties: {
                'jira-server-url': {
                    description: 'server url, i.e. "https://<your-domain>.atlassian.net/rest/api/latest/"',
                    required: true,
                    helpLink:
                        'https://confluence.atlassian.com/adminjiraserver/configuring-the-base-url-938847830.html',
                },
            },
        },
        [BuiltInPlugins.GitHub]: {
            name: BuiltInPlugins.GitHub,
            publisher: 'Microsoft',
            description:
                'Integrate Github with Chat Copilot, i.e., allow Chat CopilotBot to list active Pull Requests for you.',
            enabled: false,
            authRequirements: {
                personalAccessToken: true,
                scopes: ['Read and Write access to pull requests'],
                helpLink:
                    'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token',
            },
            icon: GithubIcon,
            headerTag: AuthHeaderTags.GitHub,
            apiProperties: {
                owner: {
                    required: false,
                    description: 'account owner of repository. i.e., "microsoft"',
                },
                repo: {
                    required: false,
                    description: 'name of repository. i.e., "semantic-kernel"',
                    helpLink: 'https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests',
                },
            },
        },
        [BuiltInPlugins.Klarna]: {
            name: BuiltInPlugins.Klarna,
            publisher: 'Klarna',
            description: 'Search and compare prices from thousands of online shops.',
            enabled: false,
            authRequirements: {},
            icon: KlarnaIcon,
            headerTag: AuthHeaderTags.Klarna,
        },
    },
};

export interface EnablePluginPayload {
    plugin: string;
    username?: string;
    email?: string;
    password?: string;
    accessToken?: string;
    apiProperties?: AdditionalApiProperties;
}
