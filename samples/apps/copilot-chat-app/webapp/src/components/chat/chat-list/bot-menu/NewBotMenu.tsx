// Copyright (c) Microsoft. All rights reserved.

import { FC, useState } from 'react';

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Tooltip } from '@fluentui/react-components';
import { ArrowUploadRegular, BotAdd20Regular, PeopleTeamAddRegular } from '@fluentui/react-icons';
import { useChat } from '../../../../libs/useChat';
import { useAppSelector } from '../../../../redux/app/hooks';
import { RootState } from '../../../../redux/app/store';
import { FeatureKeys } from '../../../../redux/features/app/AppState';
import { BotAdd20 } from '../../../shared/BundledIcons';
import { InvitationJoinDialog } from '../../invitation-dialog/InvitationJoinDialog';

interface NewBotMenuProps {
    onFileUpload: () => void;
}

export const NewBotMenu: FC<NewBotMenuProps> = ({ onFileUpload }) => {
    const chat = useChat();
    const { features } = useAppSelector((state: RootState) => state.app);

    // It needs to keep the menu open to keep the FileUploader reference
    // when the file uploader is clicked.
    const [isJoiningBot, setIsJoiningBot] = useState(false);

    const onAddChat = () => {
        void chat.createChat();
    };
    const onJoinClick = () => {
        setIsJoiningBot(true);
    };

    const onCloseDialog = () => {
        setIsJoiningBot(false);
    };

    return (
        <div>
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Tooltip content="Create new conversation" relationship="label">
                        <Button
                            data-testid="createNewConversationButton"
                            icon={<BotAdd20 />}
                            appearance="transparent"
                        />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem data-testid="addNewBotMenuItem" icon={<BotAdd20Regular />} onClick={onAddChat}>
                            Add a new Bot
                        </MenuItem>
                        <MenuItem
                            data-testid="uploadABotMenuItem"
                            disabled={!features[FeatureKeys.BotAsDocs].enabled}
                            icon={<ArrowUploadRegular />}
                            onClick={onFileUpload}
                        >
                            <div>Upload a Bot</div>
                        </MenuItem>
                        <MenuItem
                            data-testid="joinABotMenuItem"
                            disabled={!features[FeatureKeys.MultiUserChat].enabled}
                            icon={<PeopleTeamAddRegular />}
                            onClick={onJoinClick}
                        >
                            Join a Bot
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            {isJoiningBot && <InvitationJoinDialog onCloseDialog={onCloseDialog} />}
        </div>
    );
};
