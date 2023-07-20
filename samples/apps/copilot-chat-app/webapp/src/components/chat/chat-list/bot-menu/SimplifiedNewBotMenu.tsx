// Copyright (c) Microsoft. All rights reserved.

import { FC, useState } from 'react';

import {
    Button,
    Divider,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Tooltip,
} from '@fluentui/react-components';
import { useChat } from '../../../../libs/useChat';
import { useAppSelector } from '../../../../redux/app/hooks';
import { RootState } from '../../../../redux/app/store';
import { FeatureKeys } from '../../../../redux/features/app/AppState';
import { Add20 } from '../../../shared/BundledIcons';
import { InvitationJoinDialog } from '../../invitation-dialog/InvitationJoinDialog';

interface SimplifiedNewBotMenuProps {
    onFileUpload: () => void;
}

export const SimplifiedNewBotMenu: FC<SimplifiedNewBotMenuProps> = ({ onFileUpload }) => {
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
                    <Tooltip content="Add a chat" relationship="label">
                        <Button data-testid="createNewConversationButton" icon={<Add20 />} appearance="transparent" />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem data-testid="addNewBotMenuItem" onClick={onAddChat}>
                            New Chat Session
                        </MenuItem>
                        <Divider />
                        <MenuItem
                            data-testid="uploadABotMenuItem"
                            disabled={!features[FeatureKeys.BotAsDocs].enabled}
                            // TODO: Fix, not sure if it works right
                            onClick={onFileUpload}
                        >
                            <div>Upload Saved Chat</div>
                        </MenuItem>
                        <MenuItem
                            data-testid="joinABotMenuItem"
                            disabled={!features[FeatureKeys.MultiUserChat].enabled}
                            onClick={onJoinClick}
                        >
                            Join Shared Chat
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            {isJoiningBot && <InvitationJoinDialog onCloseDialog={onCloseDialog} />}
        </div>
    );
};
