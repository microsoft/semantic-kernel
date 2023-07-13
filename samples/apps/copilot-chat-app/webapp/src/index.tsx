import { IPublicClientApplication, PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { FluentProvider } from '@fluentui/react-components';
import ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import App from './App';
import { Constants } from './Constants';
import MissingEnvVariablesError from './components/views/MissingEnvVariablesError';
import './index.css';
import { AuthHelper } from './libs/auth/AuthHelper';
import { store } from './redux/app/store';

import React from 'react';
import { getMissingEnvVariables } from './checkEnv';
import { semanticKernelLightTheme } from './styles';

if (!localStorage.getItem('debug')) {
    localStorage.setItem('debug', `${Constants.debug.root}:*`);
}

let container: HTMLElement | null = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);

        const missingEnvVariables = getMissingEnvVariables();
        const validEnvFile = missingEnvVariables.length === 0;

        let msalInstance: IPublicClientApplication | null = null;
        if (validEnvFile) {
            msalInstance = new PublicClientApplication(AuthHelper.msalConfig);

            void msalInstance.handleRedirectPromise().then((response) => {
                if (response) {
                    msalInstance?.setActiveAccount(response.account);
                }
            });
        }

        root.render(
            <React.StrictMode>
                {!validEnvFile && <MissingEnvVariablesError missingVariables={missingEnvVariables} />}
                {validEnvFile && (
                    <ReduxProvider store={store}>
                        {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
                        <MsalProvider instance={msalInstance!}>
                            <FluentProvider className="app-container" theme={semanticKernelLightTheme}>
                                <App />
                            </FluentProvider>
                        </MsalProvider>
                    </ReduxProvider>
                )}
            </React.StrictMode>,
        );
    }
});
