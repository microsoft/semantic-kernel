// Copyright (c) Microsoft. All rights reserved.

import {
    Caption1,
    Card,
    CardHeader,
    ProgressBar,
    Text,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { IChatMessage } from '../../../libs/models/ChatMessage';
import { getFileIconByFileExtension } from '../ChatResourceList';

const useClasses = makeStyles({
    card: {
        height: 'fit-content',
        width: '275px',
        backgroundColor: tokens.colorNeutralBackground3,
        ...shorthands.gap(0),
        ...shorthands.margin(tokens.spacingVerticalS, 0),
        ...shorthands.padding(tokens.spacingVerticalXS, 0),
    },
    cardCaption: {
        color: tokens.colorNeutralForeground2,
    },
    cardHeader: {
        ...shorthands.margin(0, tokens.spacingHorizontalS),
    },
    cardHeaderText: {
        fontSize: 'small',
        fontWeight: '500',
    },
    footer: {
        float: 'right',
        fontSize: 'small',
        fontWeight: '500',
        color: tokens.colorNeutralForegroundDisabled,
    },
    icon: {
        height: '32px',
        width: '32px',
    },
    floatLeft: {
        float: 'left',
    },
});

interface ChatHistoryDocumentContentProps {
    isMe: boolean;
    message: IChatMessage;
}

interface DocumentMessageContent {
    name: string;
    size: string;
}

export const ChatHistoryDocumentContent: React.FC<ChatHistoryDocumentContentProps> = ({ isMe, message }) => {
    const classes = useClasses();

    let name = '',
        size = '';
    try {
        ({ name, size } = JSON.parse(message.content) as DocumentMessageContent);
    } catch (e) {
        console.error('Error parsing chat history file item: ' + message.content);
    }

    return (
        <>
            <Card appearance="filled-alternative" className={classes.card}>
                <CardHeader
                    className={classes.cardHeader}
                    image={getFileIconByFileExtension(name, { className: classes.icon })}
                    header={<Text className={classes.cardHeaderText}>{name}</Text>}
                    description={
                        <Caption1 block className={classes.cardCaption}>
                            {size}
                        </Caption1>
                    }
                />
                <ProgressBar thickness="large" color="success" value={1} />
            </Card>
            <span className={isMe ? classes.footer : mergeClasses(classes.footer, classes.floatLeft)}>
                Success: memory established
            </span>
        </>
    );
};
