// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { ChatMessageType, IChatMessage } from '../../libs/models/ChatMessage';
import { GetResponseOptions } from '../../libs/useChat';
import { ChatHistoryFileItem } from './ChatHistoryFileItem';
import { ChatHistoryItem } from './ChatHistoryItem';
import { ChatStatus } from './ChatStatus';

const useClasses = makeStyles({
    root: {
        ...shorthands.gap(tokens.spacingVerticalM),
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '900px',
        width: '100%',
        justifySelf: 'center',
    },
    item: {
        display: 'flex',
        flexDirection: 'column',
    },
});

interface ChatHistoryProps {
    messages: IChatMessage[];
    onGetResponse: (options: GetResponseOptions) => Promise<void>;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, onGetResponse }) => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            {messages
                .slice()
                .sort((a, b) => a.timestamp - b.timestamp)
                .map((message, index) =>
                    message.type === ChatMessageType.Document ? (
                        <ChatHistoryFileItem key={message.timestamp} message={message} />
                    ) : (
                        <ChatHistoryItem
                            key={message.timestamp}
                            message={message}
                            getResponse={onGetResponse}
                            messageIndex={index}
                        />
                    ),
                )}
            <ChatStatus />
        </div>
    );
};
