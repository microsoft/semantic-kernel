// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { AuthorRoles } from '../../libs/models/ChatMessage';
import { useChat } from '../../libs/useChat';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { updateConversation } from '../../redux/features/conversations/conversationsSlice';
import { SharedStyles } from '../../styles';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';

const log = debug(Constants.debug.root).extend('chat-room');

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
    },
    scroll: {
        ...shorthands.margin('4px'),
        ...SharedStyles.scroll,
    },
    history: {
        ...shorthands.padding(tokens.spacingVerticalM),
        marginLeft: '40px',
        paddingRight: '40px',
        display: 'flex',
        justifyContent: 'center',
    },
    input: {
        ...shorthands.padding(tokens.spacingVerticalM),
    },
});

export const ChatRoom: React.FC = () => {
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const messages = conversations[selectedId].messages;
    const classes = useClasses();

    const { instance } = useMsal();
    const account = instance.getActiveAccount();

    const dispatch = useAppDispatch();
    const scrollViewTargetRef = React.useRef<HTMLDivElement>(null);
    const scrollTargetRef = React.useRef<HTMLDivElement>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);

    // hardcode to care only about the bot typing for now.
    const [isBotTyping, setIsBotTyping] = React.useState(false);

    const chat = useChat();

    React.useEffect(() => {
        if (!shouldAutoScroll) return;
        scrollToTarget(scrollTargetRef.current);
    }, [messages, shouldAutoScroll]);

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

    const handleSubmit = async (
        value: string,
        approvedPlanJson?: string,
        planUserIntent?: string,
        userCancelledPlan?: boolean,
    ) => {
        log('submitting user chat message');

        const chatInput = {
            timestamp: new Date().getTime(),
            userId: account?.homeAccountId,
            userName: (account?.name ?? account?.username) as string,
            content: value,
            authorRole: AuthorRoles.User,
        };

        setIsBotTyping(true);
        dispatch(updateConversation({ message: chatInput }));

        try {
            await chat.getResponse(value, selectedId, approvedPlanJson, planUserIntent, userCancelledPlan);
        } finally {
            setIsBotTyping(false);
        }

        setShouldAutoScroll(true);
    };

    return (
        <div className={classes.root}>
            <div ref={scrollViewTargetRef} className={classes.scroll}>
                <div ref={scrollViewTargetRef} className={classes.history}>
                    <ChatHistory messages={messages} onGetResponse={handleSubmit} />
                </div>
                <div>
                    <div ref={scrollTargetRef} />
                </div>
            </div>
            <div className={classes.input}>
                <ChatInput isTyping={isBotTyping} onSubmit={handleSubmit} />
            </div>
        </div>
    );
};

const scrollToTarget = (element: HTMLElement | null) => {
    if (!element) return;
    element.scrollIntoView({ block: 'start', behavior: 'smooth' });
};
