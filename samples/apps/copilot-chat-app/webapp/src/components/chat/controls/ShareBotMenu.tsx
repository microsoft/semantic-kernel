// Copyright (c) Microsoft. All rights reserved.

import React, { FC, useCallback } from 'react';

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Tooltip } from '@fluentui/react-components';
import { ArrowDownloadRegular, PeopleTeamAddRegular, ShareRegular } from '@fluentui/react-icons';
import { useChat } from '../../../libs/useChat';
import { useFile } from '../../../libs/useFile';
import { InvitationCreateDialog } from '../invitation-dialog/InvitationCreateDialog';

interface ShareBotMenuProps {
    chatId: string;
    chatTitle: string;
}

export const ShareBotMenu: FC<ShareBotMenuProps> = ({ chatId, chatTitle }) => {
    const chat = useChat();
    const { downloadFile } = useFile();
    const [isGettingInvitationId, setIsGettingInvitationId] = React.useState(false);

    const onDownloadBotClick = useCallback(() => {
        // TODO: Add a loading indicator
        void chat.downloadBot(chatId).then((content) => {
            downloadFile(
                `chat-history-${chatTitle}-${new Date().toISOString()}.json`,
                JSON.stringify(content),
                'text/json',
            );
        });
    }, [chat, chatId, chatTitle, downloadFile]);

    return (
        <div>
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Tooltip content="Share" relationship="label">
                        <Button data-testid="shareButton" icon={<ShareRegular />} appearance="transparent" />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem
                            data-testid="downloadBotMenuItem"
                            icon={<ArrowDownloadRegular />}
                            onClick={onDownloadBotClick}
                        >
                            Download your Bot
                        </MenuItem>
                        <MenuItem
                            data-testid="inviteOthersMenuItem"
                            icon={<PeopleTeamAddRegular />}
                            onClick={() => setIsGettingInvitationId(true)}
                        >
                            Invite others to your Bot
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            {isGettingInvitationId && (
                <InvitationCreateDialog
                    onCancel={() => {
                        setIsGettingInvitationId(false);
                    }}
                    chatId={chatId}
                />
            )}
        </div>
    );
};
