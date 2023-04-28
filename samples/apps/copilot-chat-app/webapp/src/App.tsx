// Copyright (c) Microsoft. All rights reserved.

import { AuthenticatedTemplate, UnauthenticatedTemplate, useAccount, useIsAuthenticated, useMsal } from '@azure/msal-react';
import { Avatar, Spinner, Subtitle1, makeStyles } from '@fluentui/react-components';
import { Alert } from '@fluentui/react-components/unstable';
import { Dismiss16Regular } from '@fluentui/react-icons';
import * as React from 'react';
import { FC, useEffect } from 'react';
import BackendProbe from './components/views/BackendProbe';
import { ChatView } from './components/views/ChatView';
import { Login } from './components/views/Login';
import { useChat } from './libs/useChat';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { RootState } from './redux/app/store';
import { removeAlert } from './redux/features/app/appSlice';

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
    const { alerts } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();
        
    const { instance, accounts, inProgress } = useMsal();
    const account = useAccount(accounts[0] || {});    
    const isAuthenticated = useIsAuthenticated();

    const chat = useChat();

    useEffect(() => {
        if (isAuthenticated && account && appState === AppState.LoadingChats) {            
            // Load all chats from memory
            async function loadChats() {
                if (await chat.loadChats()) {
                    setAppState(AppState.Chat);
                }
            }

            loadChats();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [instance, inProgress, isAuthenticated, appState]);

    const onDismissAlert = (key: string) => {
        dispatch(removeAlert(key));
    };

    // TODO: handle error case of missing account information
    return (
        <div>
            <UnauthenticatedTemplate>
                <div style={{ display: 'flex', width: '100%', flexDirection: 'column', height: '100vh' }}>
                    <div className={classes.header}>
                        <Subtitle1 as="h1">Copilot Chat</Subtitle1>                        
                    </div>
                    <Login />
                </div>
            </UnauthenticatedTemplate>
            <AuthenticatedTemplate>
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
                    {alerts &&
                        Object.keys(alerts).map((key) => {
                            const alert = alerts[key];
                            return (
                                <Alert
                                    intent={alert.type}
                                    action={{
                                        icon: (
                                            <Dismiss16Regular
                                                aria-label="dismiss message"
                                                onClick={() => onDismissAlert(key)}
                                                color="black"
                                            />
                                        ),
                                    }}
                                    key={key}
                                >
                                    {alert.message}
                                </Alert>
                            );
                        })}
                    {appState === AppState.ProbeForBackend && (
                        <BackendProbe
                            uri={process.env.REACT_APP_BACKEND_URI as string}
                            onBackendFound={() => setAppState(AppState.LoadingChats)}
                        />
                    )}
                    {appState === AppState.LoadingChats && <Spinner labelPosition="below" label="Loading Chats" />}
                    {appState === AppState.Chat && <ChatView />}
                </div>
            </AuthenticatedTemplate>
        </div>
    );
};

export default App;
