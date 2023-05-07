// Copyright (c) Microsoft. All rights reserved.

import { Label, makeStyles, mergeClasses, Persona, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { AuthorRoles, IChatMessage } from '../../libs/models/ChatMessage';
import { SKBotAudienceMember } from '../../libs/semantic-kernel/bot-agent/models/SKBotAudienceMember';
import { useChat } from '../../libs/useChat';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        maxWidth: '75%',
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
    },
    header: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        ...shorthands.gap(tokens.spacingHorizontalL),
    },
    content: {
        wordBreak: 'break-word',
        minWidth: '260px',
    },
    canvas: {
        width: '100%',
        textAlign: 'center',
    },
});

interface ChatHistoryItemProps {
    audience: SKBotAudienceMember[];
    message: IChatMessage;
}

const createCommandLink = (command: string) => {
    const escapedCommand = encodeURIComponent(command);
    return `<span style="text-decoration: underline; cursor: pointer" data-command="${escapedCommand}" onclick="(function(){ let chatInput = document.getElementById('chat-input'); chatInput.value = decodeURIComponent('${escapedCommand}'); chatInput.focus(); return false; })();return false;">${command}</span>`;
};

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = (props) => {
    const { message } = props;
    const chat = useChat();
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    const content = message.content
        .trim()
        .replace(/[\u00A0-\u9999<>&]/g, function (i: string) {
            return `&#${i.charCodeAt(0)};`;
        })
        .replace(/^sk:\/\/.*$/gm, (match: string) => createCommandLink(match))
        .replace(/^!sk:.*$/gm, (match: string) => createCommandLink(match))
        .replace(/\n/g, '<br />')
        .replace(/ {2}/g, '&nbsp;&nbsp;');

    const date = new Date(message.timestamp);
    let time = date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
    });

    // if not today, prepend date
    if (date.toDateString() !== new Date().toDateString()) {
        time =
            date.toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
            }) +
            ' ' +
            time;
    }

    const isMe = message.authorRole === AuthorRoles.User;
    const member = chat.getAudienceMemberForId(message.userName, selectedId, conversations[selectedId].audience);
    const avatar = isMe
        ? member?.photo
            ? { image: { src: member.photo } }
            : undefined
        : { image: { src: conversations[selectedId].botProfilePicture } };
    const fullName = member?.fullName ?? message.userName;

    return (
        <>
            <div className={isMe ? mergeClasses(classes.root, classes.alignEnd) : classes.root}>
                {!isMe && <Persona className={classes.persona} avatar={avatar} />}
                <div className={isMe ? mergeClasses(classes.item, classes.me) : classes.item}>
                    <div className={classes.header}>
                        {!isMe && <Label weight="semibold">{fullName}</Label>}
                        <Label className={mergeClasses(classes.time, classes.alignEnd)} size="small">
                            {time}
                        </Label>
                    </div>
                    <div className={classes.content} dangerouslySetInnerHTML={{ __html: content }} />
                </div>
            </div>
        </>
    );
};
