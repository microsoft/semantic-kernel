// Copyright (c) Microsoft. All rights reserved.

/*import { Button, Tooltip } from '@fluentui/react-components';
import { AddFilled, AddRegular, bundleIcon } from '@fluentui/react-icons';
import { FC } from 'react';
import { useChat } from '../../../libs/useChat';

interface NewBotMenuProps {}

export const NewBotMenu: FC<NewBotMenuProps> = () => {
    const chat = useChat();
    const BotAdd20 = bundleIcon(AddFilled, AddRegular);

    const onAddChat = () => {
        void chat.createChat();
    };

    return (
        <div>
            <Tooltip content="Create new conversation" relationship="label">
                <Button
                    data-testid="createNewConversationButton"
                    icon={<BotAdd20 />}
                    appearance="transparent"
                    onClick={onAddChat}
                />
            </Tooltip>
        </div>
    );
};

*/
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
import { AddFilled, AddRegular, bundleIcon } from '@fluentui/react-icons';
import { useChat } from '../../../libs/useChat';
import { InvitationJoinDialog } from '../invitation-dialog/InvitationJoinDialog';

interface NewBotMenuProps {
    onFileUpload: () => void;
}

export const NewBotMenu: FC<NewBotMenuProps> = ({ onFileUpload }) => {
    const chat = useChat();
    // It needs to keep the menu open to keep the FileUploader reference
    // when the file uploader is clicked.
    const [isJoiningBot, setIsJoiningBot] = useState(false);

    const BotAdd20 = bundleIcon(AddFilled, AddRegular);
    //    const BotAdd20 = bundleIcon(BotAdd20Filled, BotAdd20Regular);

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
                        <Button
                            data-testid="createNewConversationButton"
                            icon={<BotAdd20 />}
                            appearance="transparent"
                        />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem data-testid="addNewBotMenuItem" onClick={onAddChat}>
                            New Chat Session
                        </MenuItem>
                        <Divider></Divider>
                        <MenuItem data-testid="uploadABotMenuItem" disabled onClick={onFileUpload}>
                            <div>Upload Saved Chat</div>
                        </MenuItem>
                        <MenuItem data-testid="joinABotMenuItem" disabled onClick={onJoinClick}>
                            Add Live Chat Code
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            {isJoiningBot && <InvitationJoinDialog onCloseDialog={onCloseDialog} />}
        </div>
    );
};
