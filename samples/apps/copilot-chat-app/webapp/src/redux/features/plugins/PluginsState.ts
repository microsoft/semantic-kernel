import { Constants } from '../../../Constants';
import GithubIcon from '../../../assets/github-icon.png';
import GraphIcon from '../../../assets/graph-api-icon.png';
import JiraIcon from '../../../assets/jira-icon.png';

export const enum Plugins {
    MsGraph = 'Microsoft Graph',
    Jira = 'Jira',
    GitHub = 'GitHub',
}

export const enum AuthHeaderTags {
    MsGraph = 'graph',
    Jira = 'jira',
    GitHub = 'github',
}

export type PluginAuthRequirements = {
    username?: boolean;
    password?: boolean;
    personalAccessToken?: boolean;
    OAuth?: boolean;
    Msal?: boolean;
    scopes?: string[];
    helpLink?: string;
};

export type Plugin = {
    name: Plugins;
    company: string;
    description: string;
    enabled: boolean;
    authRequirements: PluginAuthRequirements; // token or encoded auth header value
    headerTag: AuthHeaderTags;
    icon: string;
    authData?: string;
};

export interface PluginsState {
    MsGraph: Plugin;
    Jira: Plugin;
    GitHub: Plugin;
}

export const initialState: PluginsState = {
    MsGraph: {
        name: Plugins.MsGraph,
        company: 'Microsoft',
        description: 'Use your Microsoft Account to access your personal Graph information and Microsoft services.',
        enabled: false,
        authRequirements: {
            Msal: true,
            scopes: Constants.msGraphScopes,
        },
        headerTag: AuthHeaderTags.MsGraph,
        icon: GraphIcon,
    },
    Jira: {
        name: Plugins.Jira,
        company: 'Atlassian',
        description: 'Authorize Copilot Chat to post and link with Jira when there are issues.',
        enabled: false,
        authRequirements: {
            username: true,
            personalAccessToken: true,
            helpLink: 'https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/',
        },
        icon: JiraIcon,
        headerTag: AuthHeaderTags.Jira,
    },
    GitHub: {
        name: Plugins.GitHub,
        company: 'Microsoft',
        description:
            'Integrate Github with Copilot Chat, i.e., allow Copilot ChatBot to list active Pull Requests for you.',
        enabled: false,
        authRequirements: {
            personalAccessToken: true,
            helpLink:
                'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token',
        },
        icon: GithubIcon,
        headerTag: AuthHeaderTags.GitHub,
    },
};

export type EnablePluginPayload = {
    plugin: Plugins;
    username?: string;
    password?: string;
    accessToken?: string;
};
