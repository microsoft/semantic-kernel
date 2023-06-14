// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Persona, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { AuthorRoles, IChatMessage } from '../../libs/models/ChatMessage';
import { GetResponseOptions, useChat } from '../../libs/useChat';
import { isPlan } from '../../libs/utils/PlanUtils';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { Breakpoints } from '../../styles';
import { convertToAnchorTags, timestampToDateString } from '../utils/TextUtils';
import { PlanViewer } from './plan-viewer/PlanViewer';
import { PromptDetails } from './prompt-details/PromptDetails';

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
        backgroundColor: tokens.colorBrandBackground2,
    },
    time: {
        color: tokens.colorNeutralForeground3,
        fontSize: '12px',
        fontWeight: 400,
    },
    header: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        ...shorthands.gap(tokens.spacingHorizontalL),
    },
    content: {
        wordBreak: 'break-word',
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

const createCommandLink = (command: string) => {
    const escapedCommand = encodeURIComponent(command);
    return `<span style="text-decoration: underline; cursor: pointer" data-command="${escapedCommand}" onclick="(function(){ let chatInput = document.getElementById('chat-input'); chatInput.value = decodeURIComponent('${escapedCommand}'); chatInput.focus(); return false; })();return false;">${command}</span>`;
};

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = ({ message, getResponse, messageIndex }) => {
    const classes = useClasses();

    const { instance } = useMsal();
    const account = instance.getActiveAccount();

    const chat = useChat();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    const renderPlan = isPlan(message.content);

    const content = !renderPlan
        ? (message.content as string)
              .trim()
              .replace(/[\u00A0-\u9999<>&]/g, function (i: string) {
                  return `&#${i.charCodeAt(0)};`;
              })
              .replace(/^sk:\/\/.*$/gm, (match: string) => createCommandLink(match))
              .replace(/^!sk:.*$/gm, (match: string) => createCommandLink(match))
              .replace(/\n/g, '<br />')
              .replace(/ {2}/g, '&nbsp;&nbsp;')
        : '';

    const isMe = message.authorRole === AuthorRoles.User || message.userId === account?.homeAccountId!;
    const isBot = message.authorRole !== AuthorRoles.User && message.userId === 'bot';
    const user = chat.getChatUserById(message.userName, selectedId, conversations[selectedId].users);
    const fullName = user?.fullName ?? message.userName;

    const avatar = isBot
        ? { image: { src: conversations[selectedId].botProfilePicture } }
        : { name: fullName, color: 'colorful' as 'colorful' };

    return (
        <div
            className={isMe ? mergeClasses(classes.root, classes.alignEnd) : classes.root}
            data-testid={`chat-history-item-${messageIndex}`}   // needed for testing
            data-username={fullName}    // needed for testing
        >
            {!isMe && <Persona className={classes.persona} avatar={avatar} presence={{ status: 'available' }} />}
            <div className={isMe ? mergeClasses(classes.item, classes.me) : classes.item}>
                <div className={classes.header}>
                    {!isMe && <Text weight="semibold">{fullName}</Text>}
                    <Text className={classes.time}>{timestampToDateString(message.timestamp, true)}</Text>
                    {isBot && <PromptDetails message={message} />}
                </div>
                {renderPlan ? (
                    <PlanViewer message={message} messageIndex={messageIndex} getResponse={getResponse} />
                ) : (
                    <div
                        className={classes.content}
                        dangerouslySetInnerHTML={{ __html: convertToAnchorTags(content) }}
                    />
                )}
            </div>
        </div>
    );
};
