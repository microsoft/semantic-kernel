// Copyright (c) Microsoft. All rights reserved.

import {
    Caption1,
    Card,
    CardHeader,
    ProgressBar,
    Text,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { IChatMessage } from '../../libs/models/ChatMessage';
import { getFileIconByFileExtension } from './ChatResourceList';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignSelf: 'flex-end',
        width: '35%',
    },
    card: {
        height: 'fit-content',
        backgroundColor: tokens.colorNeutralBackground3,
        ...shorthands.gap(0),
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
        alignSelf: 'flex-end',
        fontSize: 'small',
        fontWeight: '500',
        color: tokens.colorNeutralForegroundDisabled,
        ...shorthands.margin(tokens.spacingVerticalXS, 0),
    },
    icon: {
        height: '32px',
        width: '32px',
    },
    button: {
        height: '18px',
        width: '18px',
    },
});

interface ChatHistoryFileItemProps {
    message: IChatMessage;
}

interface DocumentMessageContent {
    name: string;
    size: string;
}

export const ChatHistoryFileItem: React.FC<ChatHistoryFileItemProps> = ({ message }) => {
    const classes = useClasses();

    let name = '',
        size = '';
    try {
        ({ name, size } = JSON.parse(message.content) as DocumentMessageContent);
    } catch (e) {
        console.error('Error parsing chat history file item: ' + message.content);
    }

    return (
        <div className={classes.root}>
            <Card appearance="filled-alternative" className={classes.card}>
                <CardHeader
                    className={classes.cardHeader}
                    image={getFileIconByFileExtension(name, { className: classes.icon })}
                    header={<Text className={classes.cardHeaderText}>{name}</Text>}
                    description={<Caption1 className={classes.cardCaption}>{size}</Caption1>}
                />
                <ProgressBar thickness="large" color="success" value={1} />
            </Card>
            <span className={classes.footer}>Success: memory established</span>
        </div>
    );
};
