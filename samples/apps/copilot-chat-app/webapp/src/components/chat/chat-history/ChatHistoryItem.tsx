// Copyright (c) Microsoft. All rights reserved.

import { Persona, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { AuthorRoles, ChatMessageType, IChatMessage } from '../../../libs/models/ChatMessage';
import { GetResponseOptions, useChat } from '../../../libs/useChat';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { Breakpoints } from '../../../styles';
import { timestampToDateString } from '../../utils/TextUtils';
import { PlanViewer } from '../plan-viewer/PlanViewer';
import { PromptDetails } from '../prompt-details/PromptDetails';
import { ChatHistoryDocumentContent } from './ChatHistoryDocumentContent';
import { ChatHistoryTextContent } from './ChatHistoryTextContent';
import * as utils from './../../utils/TextUtils';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        maxWidth: '75%',
        ...shorthands.borderRadius(tokens.borderRadiusMedium),
        ...Breakpoints.small({
            maxWidth: '100%',
        }),
    },
    debug: {
        position: 'absolute',
        top: '-4px',
        right: '-4px',
    },
    alignEnd: {
        alignSelf: 'flex-end',
    },
    persona: {
        paddingTop: tokens.spacingVerticalS,
    },
    item: {
        backgroundColor: tokens.colorNeutralBackground1,
        ...shorthands.borderRadius(tokens.borderRadiusMedium),
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalL),
    },
    me: {
        backgroundColor: "#e8ebf9",
    },
    time: {
        color: tokens.colorNeutralForeground3,
        fontSize: tokens.fontSizeBase200,
        fontWeight: 400,
    },
    header: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        ...shorthands.gap(tokens.spacingHorizontalL),
    },
    canvas: {
        width: '100%',
        textAlign: 'center',
    },
});

interface ChatHistoryItemProps {
    message: IChatMessage;
    getResponse: (options: GetResponseOptions) => Promise<void>;
    messageIndex: number;
}

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = ({ message, getResponse, messageIndex }) => {
    const classes = useClasses();

    const chat = useChat();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);

    const isMe = message.authorRole === AuthorRoles.User && message.userId === activeUserInfo?.id;
    const isBot = message.authorRole === AuthorRoles.Bot;
    const user = chat.getChatUserById(message.userName, selectedId, conversations[selectedId].users);
    const fullName = user?.fullName ?? message.userName;

    const avatar = isBot
        ? { image: { src: conversations[selectedId].botProfilePicture } }
        : { name: fullName, color: 'colorful' as const };

    let content: JSX.Element;
    if (isBot && message.type === ChatMessageType.Plan) {
        content = <PlanViewer message={message} messageIndex={messageIndex} getResponse={getResponse} />;
    } else if (message.type === ChatMessageType.Document) {
        content = <ChatHistoryDocumentContent isMe={isMe} message={message} />;
    } else {
        content = <ChatHistoryTextContent message={message} />;
    }

    return (
        <div
            className={isMe ? mergeClasses(classes.root, classes.alignEnd) : classes.root}
            // The following data attributes are needed for CI and testing
            data-testid={`chat-history-item-${messageIndex}`}
            data-username={fullName}
            data-content={utils.formatChatTextContent(message.content)}
        >
            {!isMe && <Persona className={classes.persona} avatar={avatar} presence={{ status: 'available' }} />}
            <div className={isMe ? mergeClasses(classes.item, classes.me) : classes.item}>
                <div className={classes.header}>
                    {!isMe && <Text weight="semibold">{fullName}</Text>}
                    <Text className={classes.time}>{timestampToDateString(message.timestamp, true)}</Text>
                    {isBot && <PromptDetails message={message} />}
                </div>
                {content}
            </div>
        </div>
    );
};
