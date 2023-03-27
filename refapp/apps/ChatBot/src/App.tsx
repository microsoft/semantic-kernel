// Copyright (c) Microsoft. All rights reserved.

import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { makeStyles, Subtitle1 } from '@fluentui/react-components';
import { FC, useEffect } from 'react';
import { Login } from './components/Login';
import { ChatView } from './components/views/ChatView';
import { useChat } from './libs/useChat';
import { useAppSelector } from './redux/app/hooks';
import { RootState } from './redux/app/store';

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
        height: '5vh',
        color: '#FFF',
        display: 'flex',
        '& h1': {
            paddingLeft: '20px',
            alignItems: 'center',
            display: 'flex',
        }
    },
});

const App: FC = () => {
    // const [viewState, setViewState] = useState<
    //     'loading' | 'hub' | 'view' | 'edit' | 'upload' | 'memory' | 'settings'
    //     >('view');
    const classes = useClasses();
    const { conversations } = useAppSelector((state: RootState) => state.conversations);
    const chat = useChat();

    useEffect(() => {
        const keys = Object.keys(conversations);
        chat.setSelectedChat(keys[0]);
    }, []);

    return (
        <div>
            <UnauthenticatedTemplate>
                <Login />
            </UnauthenticatedTemplate>
            <AuthenticatedTemplate>
                <div style={{ display: 'flex', width: '100%', flexDirection: 'column', height: '100vh' }}>
                    <div className={classes.header} >
                        <Subtitle1 as="h1">Copilot Starter App</Subtitle1>
                    </div>
                    <ChatView />
                </div>
            </AuthenticatedTemplate>
        </div>
    );
};

export default App;
