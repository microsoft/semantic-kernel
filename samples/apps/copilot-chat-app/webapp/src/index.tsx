import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import App from './App';
import { Constants } from './Constants';
import './index.css';
import { AuthHelper } from './libs/auth/AuthHelper';
import { store } from './redux/app/store';

import React from 'react';


if (!localStorage.getItem('debug')) {
    localStorage.setItem('debug', `${Constants.debug.root}:*`);
}

const msalInstance = new PublicClientApplication(AuthHelper.msalConfig);

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
