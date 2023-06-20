// Copyright (c) Microsoft. All rights reserved.

import { makeStyles } from '@fluentui/react-components';
import React from 'react';
import { IChatMessage } from '../../../libs/models/ChatMessage';
import { convertToAnchorTags } from '../../utils/TextUtils';

const useClasses = makeStyles({
    content: {
        wordBreak: 'break-word',
    },
});

interface ChatHistoryTextContentProps {
    message: IChatMessage;
}

export const ChatHistoryTextContent: React.FC<ChatHistoryTextContentProps> = ({ message }) => {
    const classes = useClasses();

    const content = message.content
        .trim()
        .replace(/[\u00A0-\u9999<>&]/g, function (i: string) {
            return `&#${i.charCodeAt(0)};`;
        })
        .replace(/^sk:\/\/.*$/gm, (match: string) => createCommandLink(match))
        .replace(/^!sk:.*$/gm, (match: string) => createCommandLink(match))
        .replace(/\n/g, '<br />')
        .replace(/ {2}/g, '&nbsp;&nbsp;');

    return <div className={classes.content} dangerouslySetInnerHTML={{ __html: convertToAnchorTags(content) }} />;
};

const createCommandLink = (command: string) => {
    const escapedCommand = encodeURIComponent(command);
    return `<span style="text-decoration: underline; cursor: pointer" data-command="${escapedCommand}" onclick="(function(){ let chatInput = document.getElementById('chat-input'); chatInput.value = decodeURIComponent('${escapedCommand}'); chatInput.focus(); return false; })();return false;">${command}</span>`;
};
