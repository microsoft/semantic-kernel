// Copyright (c) Microsoft. All rights reserved.

import { FC, useCallback, useRef, useState } from 'react';

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Tooltip } from '@fluentui/react-components';
import { ArrowUploadRegular, BotAdd20Regular, PeopleTeamAddRegular } from '@fluentui/react-icons';
import { AlertType } from '../../../libs/models/AlertType';
import { Bot } from '../../../libs/models/Bot';
import { useChat } from '../../../libs/useChat';
import { useFile } from '../../../libs/useFile';
import { useAppDispatch } from '../../../redux/app/hooks';
import { addAlert } from '../../../redux/features/app/appSlice';
import { FileUploader } from '../../FileUploader';
import { InvitationJoinDialog } from '../invitation-dialog/InvitationJoinDialog';

export const NewBotMenu: FC = () => {
    const dispatch = useAppDispatch();
    const chat = useChat();
    const fileHandler = useFile();
    // It needs to keep the menu open to keep the FileUploader reference
    // when the file uploader is clicked.
    const [isNewBotMenuOpen, setIsNewBotMenuOpen] = useState(false);
    const [isJoiningBot, setIsJoiningBot] = useState(false);

    const fileUploaderRef = useRef<HTMLInputElement>(null);

    const onAddChat = () => {
        chat.createChat();
        setIsNewBotMenuOpen(false);
    };

    const onUpload = useCallback(
        (file: File) => {
            fileHandler
                .loadFile<Bot>(file, chat.uploadBot)
                .catch((error) =>
                    dispatch(
                        addAlert({ message: `Failed to parse uploaded file. ${error.message}`, type: AlertType.Error }),
                    ),
                );
            setIsNewBotMenuOpen(false);
        },
        [fileHandler, chat, dispatch],
    );

    const onJoinClick = () => {
        setIsJoiningBot(true);
    };

    const onCloseDialog = () => {
        setIsNewBotMenuOpen(false);
        setIsJoiningBot(false);
    };

    return (
        <div>
            <Menu open={isNewBotMenuOpen}>
                <MenuTrigger disableButtonEnhancement>
                    <Tooltip content="Create new conversation" relationship="label">
                        <Button
                            icon={<BotAdd20Regular />}
                            appearance="transparent"
                            onClick={() => setIsNewBotMenuOpen(!isNewBotMenuOpen)}
                        />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem icon={<BotAdd20Regular />} onClick={onAddChat}>
                            Add a new Bot
                        </MenuItem>
                        <MenuItem
                            icon={<ArrowUploadRegular />}
                            onClick={() => fileUploaderRef.current?.click()}
                        >
                            <div>Upload a Bot</div>
                            <FileUploader
                                ref={fileUploaderRef}
                                acceptedExtensions={['.txt', '.json']}
                                onSelectedFile={onUpload}
                            />
                        </MenuItem>
                        <MenuItem icon={<PeopleTeamAddRegular />} onClick={onJoinClick}>
                            Join a Bot
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            {isJoiningBot && <InvitationJoinDialog onCloseDialog={onCloseDialog} />}
        </div>
    );
};
