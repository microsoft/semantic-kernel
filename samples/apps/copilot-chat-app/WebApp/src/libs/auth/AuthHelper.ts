// Copyright (c) Microsoft. All rights reserved.

import {
    Configuration,
    EndSessionRequest,
    IPublicClientApplication,
    LogLevel,
    RedirectRequest,
} from '@azure/msal-browser';
import debug from 'debug';
import { Constants } from '../../Constants';

const log = debug(Constants.debug.root).extend('authHelper');

const msalConfig: Configuration = {
    auth: {
        ...Constants.msal.auth,
        redirectUri: window.origin,
    },
    cache: Constants.msal.cache,
    system: {
        loggerOptions: {
            loggerCallback: (level: LogLevel, message: string, containsPii: boolean) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        log('error:', message);
                        return;
                    case LogLevel.Info:
                        log('info:', message);
                        return;
                    case LogLevel.Verbose:
                        log('verbose:', message);
                        return;
                    case LogLevel.Warning:
                        log('warn:', message);
                        return;
                    default:
                        log(message);
                }
            },
        },
        windowHashTimeout: 9000, // Applies just to popup calls - In milliseconds
        iframeHashTimeout: 9000, // Applies just to silent calls - In milliseconds
        loadFrameTimeout: 9000, // Applies to both silent and popup calls - In milliseconds
    },
};

const loginRequest: RedirectRequest = {
    scopes: Constants.msal.skScopes,
    // Uncomment the following if you want users to consent to all necessary scopes upfront
    // extraScopesToConsent: Constants.msGraphScopes, // or Constants.adoScopes
};

const logoutRequest: EndSessionRequest = {
    postLogoutRedirectUri: window.origin,
};

const ssoSilentRequest = async (msalInstance: IPublicClientApplication) => {
    await msalInstance.ssoSilent(loginRequest);
};

const loginAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'redirect') {
        await instance.loginRedirect(loginRequest);
    } else {
        await instance.loginPopup(loginRequest);
    }
};

const logoutAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'popup') {
        void instance.logoutPopup(logoutRequest);
    }
    if (Constants.msal.method === 'redirect') {
        void instance.logoutRedirect(logoutRequest);
    }
};

// SKaS = Semantic Kernel as a Service
// Gets token with scopes to authorize SKaS specifically
const getSKaSAccessToken = async (instance: IPublicClientApplication) => {
    return instance.acquireTokenSilent(loginRequest).then((token) => {
        return token.accessToken;
    });
};

export const AuthHelper = {
    getSKaSAccessToken,
    msalConfig,
    loginRequest,
    logoutRequest,
    ssoSilentRequest,
    loginAsync,
    logoutAsync,
};
