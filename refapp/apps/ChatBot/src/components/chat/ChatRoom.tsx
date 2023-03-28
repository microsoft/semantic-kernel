// Copyright (c) Microsoft. All rights reserved.

import { useAccount, useMsal } from '@azure/msal-react';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React, { useEffect, useState } from 'react';
import { Constants } from '../../Constants';
import { AuthHelper } from '../../libs/AuthHelper';
import { ChatMessage } from '../../libs/models/ChatMessage';
import { useSemanticKernel } from '../../libs/semantic-kernel/useSemanticKernel';
import { useChat } from '../../libs/useChat';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { updateConversation } from '../../redux/features/conversations/conversationsSlice';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';

const log = debug(Constants.debug.root).extend('chat-room');

const useClasses = makeStyles({
    root: {
        height: '100%',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: '1fr auto',
        gridTemplateAreas: "'history' 'input'",
    },
    history: {
        ...shorthands.gridArea('history'),
        ...shorthands.padding(tokens.spacingVerticalM),
        overflowY: 'auto',
        display: 'grid',
    },
    input: {
        ...shorthands.gridArea('input'),
        ...shorthands.padding(tokens.spacingVerticalM),
        backgroundColor: tokens.colorNeutralBackground4,
    },
});



export const ChatRoom: React.FC = () => {
    const { audience, messages } = useAppSelector((state: RootState) => state.chat);
    const classes = useClasses();
    const account = useAccount();
    const chat = useChat();
    const dispatch = useAppDispatch();
    const scrollViewTargetRef = React.useRef<HTMLDivElement>(null);
    const scrollTargetRef = React.useRef<HTMLDivElement>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);
    const sk = useSemanticKernel(import.meta.env.VITE_REACT_APP_FUNCTION_URI as string);
    const [accessToken, setAccessToken] = useState('');
    const { instance } = useMsal();

    React.useEffect(() => {
        if (!shouldAutoScroll) return;
        scrollToTarget(scrollTargetRef.current);
    }, [messages, audience, shouldAutoScroll]);

    React.useEffect(() => {
        const onScroll = () => {
            if (!scrollViewTargetRef.current) return;
            const { scrollTop, scrollHeight, clientHeight } = scrollViewTargetRef.current;
            const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
            setShouldAutoScroll(isAtBottom);
        };

        if (!scrollViewTargetRef.current) return;

        const currentScrollViewTarget = scrollViewTargetRef.current;

        currentScrollViewTarget.addEventListener('scroll', onScroll);
        return () => {
            currentScrollViewTarget.removeEventListener('scroll', onScroll);
        };
    }, []);

    if (!account) {
        return null;
    }

    const handleSubmit = async (value: string) => {
        log('submitting user chat message');
        // TODO: handle Submit
        await getResponse(value);
        setShouldAutoScroll(true);
    };

    const requestAccessToken = () => {
        // Silently acquires an access token which is then attached to a request for Microsoft Graph data
        AuthHelper.aquireToken(instance, setAccessToken)
    }

    useEffect(() => {
        requestAccessToken();
    }, []);

    const getResponse = async (value: string) => {
        //POST a simple ask to validate the token
        // const ask = { value: 'clippy', inputs: [{ key: 'style', value: 'Bill & Ted' }] };
        try {
            // TODO: hook up KernelHttpServer
            // var result = await sk.invokeAsync(accessToken, ask, 'funskill', 'joke');
            // console.log(result);
            const messageResult = {
                timestamp: new Date().getTime(),
                sender: account?.homeAccountId,
                content: value // + result.value,
            };
            chat.addMessageToHistory(messageResult).then((value: ChatMessage[]) => {
                dispatch(updateConversation(value));
            });
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    return (
        <div className={classes.root}>
            <div ref={scrollViewTargetRef} className={classes.history}>
                <ChatHistory audience={audience} messages={messages} />
                <div>
                    <div ref={scrollTargetRef} />
                </div>
            </div>
            <div className={classes.input}>
                <ChatInput onSubmit={handleSubmit} />
            </div>
        </div>
    );
};

const scrollToTarget = (element: HTMLElement | null) => {
    if (!element) return;
    element.scrollIntoView({ block: 'start', behavior: 'smooth' });
};
