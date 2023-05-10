// Copyright (c) Microsoft. All rights reserved.

import { useAccount, useMsal } from '@azure/msal-react';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { AuthorRoles } from '../../libs/models/ChatMessage';
import { useChat } from '../../libs/useChat';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { updateConversation } from '../../redux/features/conversations/conversationsSlice';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';
import { UserAsk, UserAskResult } from './../../libs/semantic-kernel/skMultiUserChat';
import { useSKMultiUserChat } from './../../libs/semantic-kernel/useSKMultiUserChat';

const log = debug(Constants.debug.root).extend('chat-room');

const useClasses = makeStyles({
    root: {
        height: '94.5%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
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

// const EventSendConversationToOtherUsers = (userAsk: UserAsk) => {
//     console.log("Received User Ask from backend: ", userAsk);
// }

// const EventSendChatSkillAskResultToOtherUsers = (userAskResult: UserAskResult) => {
//     const dispatch = useAppDispatch();
//     const { selectedId } = useAppSelector((state: RootState) => state.conversations);

//     const messageResult = {
//         timestamp: new Date().getTime(),
//         userName: 'bot',
//         userId: 'bot',
//         content: userAskResult.value,
//         authorRole: AuthorRoles.Bot,
//     };

//     dispatch(updateConversation({ message: messageResult, chatId: selectedId }));
//     console.log("Received Chatbot Ask Result from backend: ", userAskResult);
// }

export const ChatRoom: React.FC = () => {
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { audience } = conversations[selectedId];
    const messages = conversations[selectedId].messages;
    const classes = useClasses();

    const { accounts } = useMsal();
    const account = useAccount(accounts[0] || {});

    const dispatch = useAppDispatch();
    const scrollViewTargetRef = React.useRef<HTMLDivElement>(null);
    const scrollTargetRef = React.useRef<HTMLDivElement>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);

    // hardcode to care only about the bot typing for now.
    const [isBotTyping, setIsBotTyping] = React.useState(false);

    const chat = useChat();

    var hubConnection;
    const chatRelay = useSKMultiUserChat(process.env.REACT_APP_BACKEND_URI as string);

    React.useEffect(() => {
        // This code will run once, when the component is mounted
        console.log('SignalR setup called');
        // eslint-disable-next-line react-hooks/exhaustive-deps
        hubConnection = chatRelay.setupSignalRConnectionToChatHub();
        
        const EventSendConversationToOtherUsers = (userAsk: UserAsk) => {
            console.log("Received User Ask from backend: ", userAsk);
        }
        
        const EventSendChatSkillAskResultToOtherUsers = (userAskResult: UserAskResult) => {
            const dispatch = useAppDispatch();
            const { selectedId } = useAppSelector((state: RootState) => state.conversations);
        
            const messageResult = {
                timestamp: new Date().getTime(),
                userName: 'bot',
                userId: 'bot',
                content: userAskResult.value,
                authorRole: AuthorRoles.Bot,
            };
        
            dispatch(updateConversation({ message: messageResult, chatId: selectedId }));
            console.log("Received Chatbot Ask Result from backend: ", userAskResult);
        }

        hubConnection.on("SendConversationToOtherUsersFrontEnd", EventSendConversationToOtherUsers);
        hubConnection.on("SendChatSkillAskResultToOtherUsersFrontEnd", EventSendChatSkillAskResultToOtherUsers);
    // Disabling warning so that we can use empty dependency array to invoke this setup call just once 
    }, []);

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

    // const handleNewMessageFromOtherUsers = async () => {
    //     skmultiuserchat
    // }

    const handleSubmit = async (value: string) => {
        log('submitting user chat message');
        const chatInput = {
            timestamp: new Date().getTime(),
            userId: account?.homeAccountId,
            userName: account?.name as string,
            content: value,
            authorRole: AuthorRoles.User,
        };
        setIsBotTyping(true);
        dispatch(updateConversation({ message: chatInput }));
        try {
            await chat.getResponse(value, selectedId);
        } finally {
            setIsBotTyping(false);
        }
        setShouldAutoScroll(true);
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
                <ChatInput isTyping={isBotTyping} onSubmit={handleSubmit} />
            </div>
        </div>
    );
};

const scrollToTarget = (element: HTMLElement | null) => {
    if (!element) return;
    element.scrollIntoView({ block: 'start', behavior: 'smooth' });
};
