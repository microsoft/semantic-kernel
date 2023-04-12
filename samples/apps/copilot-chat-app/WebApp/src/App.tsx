// Copyright (c) Microsoft. All rights reserved.

import { AuthenticatedTemplate, UnauthenticatedTemplate, useIsAuthenticated } from '@azure/msal-react';
import { Avatar, makeStyles, Spinner, Subtitle1 } from '@fluentui/react-components';
import * as React from 'react';
import { FC, useEffect } from 'react';
import { msalInstance } from '.';
import { Login } from './components/Login';
import BackendProbe from './components/views/BackendProbe';
import { ChatView } from './components/views/ChatView';
import { useChat } from './libs/useChat';

const useClasses = makeStyles({
    container: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        justifyContent: 'space-between',
    },
    header: {
        backgroundColor: '#9c2153',
        width: '100%',
        height: '48px',
        color: '#FFF',
        display: 'flex',
        '& h1': {
            paddingLeft: '20px',
            display: 'flex',
        },
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    persona: {
        marginRight: '20px',
    },
});

enum AppState {
    ProbeForBackend,
    LoadingChats,
    Chat,
}

const App: FC = () => {
    const [appState, setAppState] = React.useState(AppState.ProbeForBackend);
    const classes = useClasses();
    const account = msalInstance.getActiveAccount();

    const isAuthenticated = useIsAuthenticated();
    const chat = useChat();

    useEffect(() => {
        if (isAuthenticated) {
            // Load all chats from memory
            chat.loadChats().then(() => {
                setAppState(AppState.Chat);
            });
        }
    }, [isAuthenticated]);

    return (
        <div>
            <UnauthenticatedTemplate>
                <Login />
            </UnauthenticatedTemplate>
            <AuthenticatedTemplate>
                {appState === AppState.ProbeForBackend && (
                    <BackendProbe
                        uri={process.env.REACT_APP_BACKEND_URI as string}
                        onBackendFound={() => setAppState(AppState.LoadingChats)}
                    />
                )}
                {appState === AppState.LoadingChats && <Spinner labelPosition="below" label="Loading Chats" />}
                {appState === AppState.Chat && (
                    <div style={{ display: 'flex', width: '100%', flexDirection: 'column', height: '100vh' }}>
                        <div className={classes.header}>
                            <Subtitle1 as="h1">Copilot Chat</Subtitle1>
                            <Avatar
                                className={classes.persona}
                                key={account?.name}
                                name={account?.name}
                                size={28}
                                badge={{ status: 'available' }}
                            />
                        </div>
                        <ChatView />
                    </div>
                )}
            </AuthenticatedTemplate>
        </div>
    );
};

export default App;