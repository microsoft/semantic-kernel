// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { AuthorRoles, IChatMessage } from '../../libs/models/ChatMessage';
import { GetResponseOptions, useChat } from '../../libs/useChat';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { FeatureKeys } from '../../redux/features/app/AppState';
import { updateConversationFromUser } from '../../redux/features/conversations/conversationsSlice';
import { SharedStyles } from '../../styles';
import { ChatInput } from './ChatInput';
import { ChatHistory } from './chat-history/ChatHistory';

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
        ...shorthands.margin(tokens.spacingVerticalXS),
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
    const { activeUserInfo, features } = useAppSelector((state: RootState) => state.app);

    const messages = conversations[selectedId].messages;
    const classes = useClasses();

    const dispatch = useAppDispatch();
    const scrollViewTargetRef = React.useRef<HTMLDivElement>(null);
    const scrollTargetRef = React.useRef<HTMLDivElement>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);

    const [isDraggingOver, setIsDraggingOver] = React.useState(false);
    const onDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
        if (!features[FeatureKeys.SimplifiedExperience].enabled) {
            e.preventDefault();
            setIsDraggingOver(true);
        }
    };
    const onDragLeave = (e: React.DragEvent<HTMLDivElement | HTMLTextAreaElement>) => {
        if (!features[FeatureKeys.SimplifiedExperience].enabled) {
            e.preventDefault();
            setIsDraggingOver(false);
        }
    };

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

    const handleSubmit = async (options: GetResponseOptions) => {
        log('submitting user chat message');

        const chatInput: IChatMessage = {
            timestamp: new Date().getTime(),
            userId: activeUserInfo?.id as string,
            userName: activeUserInfo?.username as string,
            content: options.value,
            type: options.messageType,
            authorRole: AuthorRoles.User,
        };

        dispatch(updateConversationFromUser({ message: chatInput }));

        await chat.getResponse(options);

        setShouldAutoScroll(true);
    };

    return (
        <div className={classes.root} onDragEnter={onDragEnter} onDragOver={onDragEnter} onDragLeave={onDragLeave}>
            <div ref={scrollViewTargetRef} className={classes.scroll}>
                <div ref={scrollViewTargetRef} className={classes.history}>
                    <ChatHistory messages={messages} onGetResponse={handleSubmit} />
                </div>
                <div>
                    <div ref={scrollTargetRef} />
                </div>
            </div>
            <div className={classes.input}>
                <ChatInput isDraggingOver={isDraggingOver} onDragLeave={onDragLeave} onSubmit={handleSubmit} />
            </div>
        </div>
    );
};

const scrollToTarget = (element: HTMLElement | null) => {
    if (!element) return;
    element.scrollIntoView({ block: 'start', behavior: 'smooth' });
};
