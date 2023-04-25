import GithubAvatar from '../../../assets/github-icon.png';
import JiraAvatar from '../../../assets/jira-icon.png';

export const enum Plugins {
    MsGraph = 'Microsoft Graph',
    Jira = 'Jira',
    GitHub = 'GitHub',
}

export const enum AuthHeaderTags {
    MsGraph = 'graph',
    Jira = 'gira',
    GitHub = 'github',
    Ado = 'ado',
}

type AuthRequirements = {
    username?: boolean;
    password?: boolean;
    accessToken?: boolean;
    OAuth?: boolean;
    Msal?: boolean;
    scopes?: string[];
    helpLink?: string;
};

type Plugin = {
    name: Plugins;
    enabled: boolean;
    authRequirements: AuthRequirements; // token or encoded auth header value
    headerTag: AuthHeaderTags;
    icon?: string;
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
        enabled: false,
        authRequirements: {
            Msal: true,
        },
        headerTag: AuthHeaderTags.MsGraph,
    },
    Jira: {
        name: Plugins.Jira,
        enabled: false,
        authRequirements: {
            username: true,
            accessToken: true,
            helpLink: 'https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/',
        },
        icon: JiraAvatar,
        headerTag: AuthHeaderTags.Jira,
    },
    GitHub: {
        name: Plugins.GitHub,
        enabled: false,
        authRequirements: {
            accessToken: true,
            helpLink:
                'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token',
        },
        icon: GithubAvatar,
        headerTag: AuthHeaderTags.GitHub,
    },
};

export type EnablePluginPayload = {
    plugin: Plugins;
    username: string;
    password: string;
    accessToken: string;
};
