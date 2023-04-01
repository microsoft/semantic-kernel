// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { ChatMessage } from '../../libs/models/ChatMessage';
import { SKBotAudienceMember } from '../../libs/semantic-kernel/bot-agent/models/SKBotAudienceMember';
import { ChatHistoryItem } from './ChatHistoryItem';
import { ChatStatus } from './ChatStatus';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(tokens.spacingVerticalM),
        maxWidth: '900px',
        width: '100%',
        justifySelf: 'center',
    },
    content: {},
    item: {
        display: 'flex',
        flexDirection: 'column',
    },
});

interface ChatHistoryProps {
    audience: SKBotAudienceMember[];
    messages: ChatMessage[];
}

export const ChatHistory: React.FC<ChatHistoryProps> = (props) => {
    const { audience, messages } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            {messages
                .slice()
                .sort((a, b) => a.timestamp - b.timestamp)
                .map((message) => (
                    <ChatHistoryItem key={message.timestamp} audience={audience} message={message} />
                ))}
            <ChatStatus />
        </div>
    );
};
