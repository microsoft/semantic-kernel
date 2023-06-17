// Copyright (c) Microsoft. All rights reserved.

import { FC, useCallback } from 'react';

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Tooltip } from '@fluentui/react-components';
import { ArrowDownloadRegular, ShareRegular } from '@fluentui/react-icons';
import { useChat } from '../../libs/useChat';
import { useFile } from '../../libs/useFile';

interface ShareBotMenuProps {
    chatId: string;
    chatTitle: string;
}

export const ShareBotMenu: FC<ShareBotMenuProps> = ({ chatId, chatTitle }) => {
    const chat = useChat();
    const { downloadFile } = useFile();

    const onDownloadBotClick = useCallback(async () => {
        // TODO: Add a loading indicator
        const content = await chat.downloadBot(chatId);
        downloadFile(
            `chat-history-${chatTitle}-${new Date().toISOString()}.json`,
            JSON.stringify(content),
            'text/json',
        );
    }, [chat, chatId, chatTitle, downloadFile]);

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Tooltip content="Share" relationship="label">
                    <Button icon={<ShareRegular />} appearance="transparent" />
                </Tooltip>
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    <MenuItem icon={<ArrowDownloadRegular />} onClick={onDownloadBotClick}>
                        Download your Bot
                    </MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
