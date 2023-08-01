// Copyright (c) Microsoft. All rights reserved.

import { AuthenticatedTemplate, UnauthenticatedTemplate, useIsAuthenticated, useMsal } from '@azure/msal-react';
import { Subtitle1, makeStyles, shorthands, tokens } from '@fluentui/react-components';

import * as React from 'react';
import { FC, useEffect } from 'react';
import { UserSettings } from './components/header/UserSettings';
import { PluginGallery } from './components/open-api-plugins/PluginGallery';
import BackendProbe from './components/views/BackendProbe';
import { ChatView } from './components/views/ChatView';
import Loading from './components/views/Loading';
import { Login } from './components/views/Login';
import { AlertType } from './libs/models/AlertType';
import { useChat } from './libs/useChat';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { RootState } from './redux/app/store';
import { addAlert, setActiveUserInfo } from './redux/features/app/appSlice';

export const useClasses = makeStyles({
    container: {
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100%',
        ...shorthands.overflow('hidden'),
    },
    header: {
        alignItems: 'center',
        backgroundColor: tokens.colorBrandForeground2,
        color: tokens.colorNeutralForegroundOnBrand,
        display: 'flex',
        '& h1': {
            paddingLeft: tokens.spacingHorizontalXL,
            display: 'flex',
        },
        height: '48px',
        justifyContent: 'space-between',
        width: '100%',
    },
    persona: {
        marginRight: tokens.spacingHorizontalXXL,
    },
    cornerItems: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingHorizontalS),
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
    const dispatch = useAppDispatch();

    const { instance, inProgress } = useMsal();
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);
    const isAuthenticated = useIsAuthenticated();

    const chat = useChat();

    useEffect(() => {
        if (isAuthenticated) {
            let isActiveUserInfoSet = activeUserInfo !== undefined;
            if (!isActiveUserInfoSet) {
                const account = instance.getActiveAccount();
                if (!account) {
                    dispatch(addAlert({ type: AlertType.Error, message: 'Unable to get active logged in account.' }));
                } else {
                    dispatch(
                        setActiveUserInfo({
                            id: account.homeAccountId,
                            email: account.username, // username in an AccountInfo object is the email address
                            username: account.name ?? account.username,
                        }),
                    );
                }
                isActiveUserInfoSet = true;
            }

            if (appState === AppState.LoadingChats) {
                // Load all chats from memory
                void chat.loadChats().then((succeeded) => {
                    if (succeeded) {
                        setAppState(AppState.Chat);
                    }
                });
            }
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [instance, inProgress, isAuthenticated, appState]);

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
                        <div data-testid="logOutMenuList" className={classes.cornerItems}>
                            <PluginGallery />
                            <UserSettings
                                setLoadingState={() => {
                                    setAppState(AppState.SigningOut);
                                }}
                            />
                        </div>
                    </div>
                    {appState === AppState.ProbeForBackend && (
                        <BackendProbe
                            uri={process.env.REACT_APP_BACKEND_URI as string}
                            onBackendFound={() => {
                                setAppState(AppState.LoadingChats);
                            }}
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
