// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import {
    AvatarGroupItem,
    AvatarGroupPopover,
    Button,
    Input,
    InputOnChangeData,
    Label,
    makeStyles,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    SelectTabData,
    SelectTabEvent,
    shorthands,
    Tab,
    TabList,
    TabValue,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import { Edit24Filled, EditRegular } from '@fluentui/react-icons';
import React, { useEffect, useState } from 'react';
import { AuthHelper } from '../../libs/auth/AuthHelper';
import { AlertType } from '../../libs/models/AlertType';
import { ChatService } from '../../libs/services/ChatService';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { addAlert } from '../../redux/features/app/appSlice';
import { editConversationTitle } from '../../redux/features/conversations/conversationsSlice';
import { ChatResourceList } from './ChatResourceList';
import { ChatRoom } from './ChatRoom';
import { ShareBotMenu } from './ShareBotMenu';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        backgroundColor: '#F5F5F5',
        boxShadow: 'rgb(0 0 0 / 25%) 0 0.2rem 0.4rem -0.075rem',
    },
    header: {
        ...shorthands.borderBottom('1px', 'solid', 'rgb(0 0 0 / 10%)'),
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
        backgroundColor: tokens.colorNeutralBackground4,
        display: 'flex',
        flexDirection: 'row',
        boxSizing: 'border-box',
        width: '100%',
        justifyContent: 'space-between',
    },
    title: {
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'row',
    },
    controls: {
        display: 'flex',
    },
    popoverHeader: {
        ...shorthands.margin('0'),
        paddingBottom: tokens.spacingVerticalXXS,
        fontStyle: 'normal',
        fontWeight: '600',
    },
    popover: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        justifyContent: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXL),
        ...shorthands.gap(tokens.spacingVerticalMNudge),
        width: '398px',
    },
    input: {
        width: '100%',
    },
});

export const ChatWindow: React.FC = () => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chatName = conversations[selectedId].title;
    const [title, setTitle] = useState<string | undefined>(selectedId ?? undefined);
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const { instance, inProgress } = useMsal();

    const chatService = new ChatService(process.env.REACT_APP_BACKEND_URI as string);

    const onSave = async () => {
        if (chatName !== title) {
            try {
                await chatService.editChatAsync(
                    conversations[selectedId].id,
                    title!,
                    await AuthHelper.getSKaaSAccessToken(instance, inProgress),
                );
                
                dispatch(editConversationTitle({ id: selectedId ?? '', newTitle: title ?? '' }));
            } catch (e: any) {
                const errorMessage = `Unable to retrieve chat to change title. Details: ${e.message ?? e}`;
                dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            }
        }
        setIsEditing(!isEditing);
    };

    const [selectedTab, setSelectedTab] = React.useState<TabValue>('chat');
    const onTabSelect = (_event: SelectTabEvent, data: SelectTabData) => {
        setSelectedTab(data.value);
    };

    const onClose = async () => {
        setTitle(chatName);
        setIsEditing(!isEditing);
    };

    const onTitleChange = (_ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
        setTitle(data.value);
    };

    const handleKeyDown = (event: any) => {
        if (event.key === 'Enter') {
            onSave();
        }
    };

    useEffect(() => {
        setTitle(chatName);
        setIsEditing(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedId]);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={classes.title}>
                    <Persona
                        key={'Semantic Kernel Bot'}
                        size="medium"
                        avatar={{ image: { src: conversations[selectedId].botProfilePicture } }}
                        presence={{ status: 'available' }}
                    />
                    <Label size="large" weight="semibold">
                        {chatName}
                    </Label>
                    <Popover open={isEditing}>
                        <PopoverTrigger disableButtonEnhancement>
                            <Tooltip content={'Edit conversation name'} relationship="label">
                                <Button
                                    icon={isEditing ? <Edit24Filled /> : <EditRegular />}
                                    appearance="transparent"
                                    onClick={onClose}
                                    disabled={title === undefined || !title}
                                    aria-label="Edit conversation name"
                                />
                            </Tooltip>
                        </PopoverTrigger>
                        <PopoverSurface className={classes.popover}>
                            <h3 className={classes.popoverHeader}>Bot name</h3>
                            <Input
                                value={title}
                                onChange={onTitleChange}
                                id={title}
                                className={classes.input}
                                onKeyDown={handleKeyDown}
                            />
                        </PopoverSurface>
                    </Popover>
                    <TabList selectedValue={selectedTab} onTabSelect={onTabSelect}>
                        <Tab id="chat" value="chat">
                            Chat
                        </Tab>
                        <Tab id="files" value="files">
                            Files
                        </Tab>
                    </TabList>
                </div>
                <div className={classes.controls}>
                    <AvatarGroupPopover>
                        {conversations[selectedId].users.map((user) => (
                            <AvatarGroupItem name={user.id} key={user.id} />
                        ))}
                    </AvatarGroupPopover>
                    <ShareBotMenu chatId={selectedId} chatTitle={title || ''} />
                </div>
            </div>
            {selectedTab === 'chat' && <ChatRoom />}
            {selectedTab === 'files' && <ChatResourceList chatId={selectedId} />}
        </div>
    );
};
