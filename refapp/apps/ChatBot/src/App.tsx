// Copyright (c) Microsoft. All rights reserved.

import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { makeStyles, Persona, Subtitle1 } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import { Login } from './components/Login';
import { ChatView } from './components/views/ChatView';
import { MicrosoftGraph } from './libs/MicrosoftGraph';
import { msalInstance } from './main';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { RootState } from './redux/app/store';
import { setSelectedConversation } from './redux/features/conversations/conversationsSlice';

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
        paddingRight: '15px'
    }
});

const App: FC = () => {
    // const [viewState, setViewState] = useState<
    //     'loading' | 'hub' | 'view' | 'edit' | 'upload' | 'memory' | 'settings'
    //     >('view');
    const classes = useClasses();
    const { conversations } = useAppSelector((state: RootState) => state.conversations);
    const dispatch = useAppDispatch();
    const account = msalInstance.getActiveAccount();
    const [profilePicture, setProfilePicture] = useState('');

    useEffect(() => {
        // TODO: Load Conversations from BE
        const keys = Object.keys(conversations);
        dispatch(setSelectedConversation(keys[0]));
        MicrosoftGraph.getMyPhotoAsync().then((value) => {
            setProfilePicture(value);
        });
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
                        <Persona
                            className={classes.persona}
                            key={account?.name}
                            size="small"
                            avatar={profilePicture.length > 0 ? { image: { src: profilePicture } } : null}
                            presence={{ status: 'available' }}
                        />
                    </div>
                    <ChatView />
                </div>
            </AuthenticatedTemplate>
        </div>
    );
};

export default App;
