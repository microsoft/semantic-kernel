// Copyright (c) Microsoft. All rights reserved.

import {
    AuthenticatedTemplate,
    UnauthenticatedTemplate,
    useIsAuthenticated,
    useMsal,
} from '@azure/msal-react';
import { Subtitle1, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { Alert } from '@fluentui/react-components/unstable';
import { Dismiss16Regular } from '@fluentui/react-icons';
import * as React from 'react';
import { FC, useEffect } from 'react';
import { UserSettings } from './components/header/UserSettings';
import { PluginGallery } from './components/open-api-plugins/PluginGallery';
import BackendProbe from './components/views/BackendProbe';
import { ChatView } from './components/views/ChatView';
import Loading from './components/views/Loading';
import { Login } from './components/views/Login';
import { useChat } from './libs/useChat';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { RootState } from './redux/app/store';
import { removeAlert } from './redux/features/app/appSlice';
import { setLoggedInUserId } from './redux/features/conversations/conversationsSlice';
import { CopilotChatTokens } from './styles';

export const useClasses = makeStyles({
    container: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100vh',
    },
    header: {
        backgroundColor: CopilotChatTokens.backgroundColor,
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
    cornerItems: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingHorizontalXS),
    },
});

enum AppState {
    ProbeForBackend,
    LoadingChats,
    Chat,
    SigningOut,
}

const App: FC = () => {
    const classes = useClasses();

    const [appState, setAppState] = React.useState(AppState.ProbeForBackend);
    const { alerts } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();

    const { instance, inProgress } = useMsal();
    const account = instance.getActiveAccount();
    const isAuthenticated = useIsAuthenticated();

    const chat = useChat();

    useEffect(() => {
        if (isAuthenticated && account) {
            dispatch(setLoggedInUserId(account.homeAccountId));

            if (appState === AppState.LoadingChats) {
                // Load all chats from the backend.
                async function loadChats() {
                    if (await chat.loadChats()) {
                        setAppState(AppState.Chat);
                    }
                }

                loadChats();
            }
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
                <div className={classes.container}>
                    <div className={classes.header}>
                        <Subtitle1 as="h1">Copilot Chat</Subtitle1>
                    </div>
                    {appState === AppState.SigningOut && <Loading text="Signing you out..." />}
                    {appState !== AppState.SigningOut && <Login />}
                </div>
            </UnauthenticatedTemplate>
            <AuthenticatedTemplate>
                <div className={classes.container}>
                    <div className={classes.header}>
                        <Subtitle1 as="h1">Copilot Chat</Subtitle1>
                        <div className={classes.cornerItems}>
                            <PluginGallery />
                            <UserSettings setLoadingState={() => setAppState(AppState.SigningOut)} />
                        </div>
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
                    {appState === AppState.LoadingChats && <Loading text="Loading Chats..." />}
                    {appState === AppState.Chat && <ChatView />}
                </div>
            </AuthenticatedTemplate>
        </div>
    );
};

export default App;
