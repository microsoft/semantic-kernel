// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import {
    Caption1,
    Card,
    CardHeader,
    Persona,
    ProgressBar,
    Text,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { AuthorRoles, IChatMessage } from '../../libs/models/ChatMessage';
import { timestampToDateString } from '../utils/TextUtils';
import { getFileIconByFileExtension } from './ChatResourceList';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        alignSelf: 'flex-end',
        width: '35%',
    },
    persona: {
        paddingTop: tokens.spacingVerticalS,
    },
    item: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
    },
    header: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        ...shorthands.gap(tokens.spacingHorizontalL),
        paddingLeft: tokens.spacingHorizontalL,
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
    time: {
        color: tokens.colorNeutralForeground3,
        fontSize: '12px',
        fontWeight: 400,
    },
    icon: {
        height: '32px',
        width: '32px',
    },
    button: {
        height: '18px',
        width: '18px',
    },
    alignEnd: {
        alignSelf: 'flex-start',
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
    const { instance } = useMsal();
    const account = instance.getActiveAccount();
    const isMe = message.authorRole === AuthorRoles.User && message.userId === account?.homeAccountId!;

    let name = '',
        size = '';
    try {
        ({ name, size } = JSON.parse(message.content) as DocumentMessageContent);
    } catch (e) {
        console.error('Error parsing chat history file item: ' + message.content);
    }

    return (
        <div className={isMe ? classes.root : mergeClasses(classes.root, classes.alignEnd)}>
            {!isMe &&
                <Persona
                    className={classes.persona}
                    avatar={{ name: message.userName, color: 'colorful' as 'colorful' }}
                    presence={{ status: 'available' }}
                />}
            <div className={classes.item}>
                <div className={classes.header}>
                {!isMe && <Text weight="semibold">{message.userName}</Text>}
                    <Text className={classes.time}>{timestampToDateString(message.timestamp, true)}</Text>
                </div>
                <Card appearance="filled-alternative" className={classes.card}>
                    <CardHeader
                        className={classes.cardHeader}
                        image={getFileIconByFileExtension(name, { className: classes.icon })}
                        header={<Text className={classes.cardHeaderText}>{name}</Text>}
                        description={<Caption1 className={classes.cardCaption}>{size}</Caption1>}
                        />
                    <ProgressBar thickness="large" color="success" value={1} />
                </Card>
                <span className={isMe ? classes.footer : mergeClasses(classes.footer, classes.alignEnd)}>
                    Success: memory established
                </span>
            </div>
        </div>
    );
};
