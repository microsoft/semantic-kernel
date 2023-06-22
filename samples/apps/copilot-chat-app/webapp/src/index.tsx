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
import { BrandVariants, createLightTheme } from '@fluentui/react-components';


if (!localStorage.getItem('debug')) {
    localStorage.setItem('debug', `${Constants.debug.root}:*`);
}

let container: HTMLElement | null = null;

const semanticKernelBrandRamp: BrandVariants = {
    10: "#060103",
    20: "#261018",
    30: "#431426",
    40: "#591732",
    50: "#701A3E",
    60: "#861F4B",
    70: "#982C57",
    80: "#A53E63",
    90: "#B15070",
    100: "#BC627E",
    110: "#C6748B",
    120: "#CF869A",
    130: "#D898A8",
    140: "#E0AAB7",
    150: "#E8BCC6",
    160: "#EFCFD6"
};

export const semanticKernelLightTheme = createLightTheme(semanticKernelBrandRamp);

document.addEventListener('DOMContentLoaded', async () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);

        const missingEnvVariables = getMissingEnvVariables();
        const validEnvFile = missingEnvVariables.length === 0;

        var msalInstance: IPublicClientApplication | null = null;
        if (validEnvFile) {
            msalInstance = new PublicClientApplication(AuthHelper.msalConfig);

            msalInstance.handleRedirectPromise().then((response) => {
                if (response) {
                    msalInstance?.setActiveAccount(response?.account);
                }
            });
        }

        root.render(
            <React.StrictMode>
                {!validEnvFile && <MissingEnvVariablesError missingVariables={missingEnvVariables} />}
                {validEnvFile && (
                    <ReduxProvider store={store}>
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
