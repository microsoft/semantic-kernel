import { AuthenticationResult, EventType, PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import App from './App';
import { Constants } from './Constants';
import './index.css';
import { AuthHelper } from './libs/auth/AuthHelper';
import { store } from './redux/app/store';

import debug from 'debug';
import React from 'react';

const log = debug('main');

if (!localStorage.getItem('debug')) {
    localStorage.setItem('debug', `${Constants.debug.root}:*`);
}

export const msalInstance = new PublicClientApplication(AuthHelper.msalConfig);

msalInstance
    .handleRedirectPromise()
    .then(() => {
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length > 0) {
            msalInstance.setActiveAccount(accounts[0]);
        }
    })
    .catch((error: any) => {
        log('Login with redirect failed: ', error);
    });

msalInstance.addEventCallback((event: any) => {
    log('msal event:', event);
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
        const payload = event.payload as AuthenticationResult;
        msalInstance.setActiveAccount(payload.account);
    }
});

let container: HTMLElement | null = null;
document.addEventListener('DOMContentLoaded', () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);
        root.render(
            <React.StrictMode>
                <ReduxProvider store={store}>
                    <MsalProvider instance={msalInstance}>
                        <FluentProvider className="app-container" theme={webLightTheme}>
                            <App />
                        </FluentProvider>
                    </MsalProvider>
                </ReduxProvider>
                ,
            </React.StrictMode>,
        );
    }
});
