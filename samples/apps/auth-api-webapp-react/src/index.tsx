// Copyright (c) Microsoft. All rights reserved.

import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { BrandVariants, FluentProvider, Theme, createLightTheme } from '@fluentui/react-components';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

const myTheme: BrandVariants = {
    10: '#000000',
    20: '#1F0E13',
    30: '#371520',
    40: '#501A2C',
    50: '#6B1D3A',
    60: '#862048',
    70: '#A02656',
    80: '#B23A65',
    90: '#C24D75',
    100: '#D06285',
    110: '#DE7695',
    120: '#E98BA6',
    130: '#F2A1B7',
    140: '#FAB8C9',
    150: '#FFCFDB',
    160: '#FFE7ED',
};

const lightTheme: Theme = {
    ...createLightTheme(myTheme),
};

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);

const msalConfig = {
    auth: {
        clientId: process.env.REACT_APP_GRAPH_CLIENT_ID as string,
        authority: 'https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad',
        redirectUri: 'http://localhost:3000',
    },
};

const msalInstance = new PublicClientApplication(msalConfig);

root.render(
    <React.StrictMode>
        <FluentProvider theme={lightTheme}>
            <MsalProvider instance={msalInstance}>
                <App />
            </MsalProvider>
        </FluentProvider>
    </React.StrictMode>,
);
