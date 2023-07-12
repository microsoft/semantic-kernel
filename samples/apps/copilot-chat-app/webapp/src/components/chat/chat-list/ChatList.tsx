// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Input,
    InputOnChangeData,
    makeStyles,
    mergeClasses,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { bundleIcon, Dismiss20Filled, Dismiss20Regular, Filter20Filled, Filter20Regular } from '@fluentui/react-icons';
import { FC, useCallback, useEffect, useRef, useState } from 'react';
import { AlertType } from '../../../libs/models/AlertType';
import { Bot } from '../../../libs/models/Bot';
import { ChatMessageType } from '../../../libs/models/ChatMessage';
import { useChat } from '../../../libs/useChat';
import { useFile } from '../../../libs/useFile';
import { isPlan } from '../../../libs/utils/PlanUtils';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { addAlert } from '../../../redux/features/app/appSlice';
import { Conversations } from '../../../redux/features/conversations/ConversationsState';
import { Breakpoints } from '../../../styles';
import { FileUploader } from '../../FileUploader';
import { ChatListItem } from './ChatListItem';
import { NewBotMenu } from './NewBotMenu';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexShrink: 0,
        width: '320px',
        backgroundColor: tokens.colorNeutralBackground4,
        flexDirection: 'column',
        ...shorthands.overflow('hidden'),
        ...Breakpoints.small({
            width: '64px',
        }),
    },
    list: {
        overflowY: 'auto',
        overflowX: 'hidden',
        '&:hover': {
            '&::-webkit-scrollbar-thumb': {
                backgroundColor: tokens.colorScrollbarOverlay,
                visibility: 'visible',
            },
        },
        '&::-webkit-scrollbar-track': {
            backgroundColor: tokens.colorSubtleBackground,
        },
        alignItems: 'stretch',
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginRight: tokens.spacingVerticalM,
        marginLeft: tokens.spacingHorizontalXL,
        alignItems: 'center',
        height: '60px',
        ...Breakpoints.small({
            justifyContent: 'center',
        }),
    },
    title: {
        flexGrow: 1,
        ...Breakpoints.small({
            display: 'none',
        }),
    },
    botsHeader: {
        marginTop: 0,
        marginBottom: tokens.spacingVerticalSNudge,
        marginLeft: tokens.spacingHorizontalXL,
        marginRight: tokens.spacingHorizontalXL,
        fontWeight: tokens.fontWeightRegular,
        fontSize: tokens.fontSizeBase200,
        color: tokens.colorNeutralForeground3,
        ...Breakpoints.small({
            display: 'none',
        }),
    },
    input: {
        flexGrow: 1,
        ...shorthands.padding(tokens.spacingHorizontalNone),
        ...shorthands.border(tokens.borderRadiusNone),
        backgroundColor: tokens.colorSubtleBackground,
        fontSize: tokens.fontSizeBase500,
    },
});

export const ChatList: FC = () => {
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    const [isFiltering, setIsFiltering] = useState(false);
    const [filterText, setFilterText] = useState('');
    const [conversationsView, setConversationsView] = useState(conversations);

    const chat = useChat();
    const fileHandler = useFile();
    const dispatch = useAppDispatch();

    const Dismiss20 = bundleIcon(Dismiss20Filled, Dismiss20Regular);
    const Filter20 = bundleIcon(Filter20Filled, Filter20Regular);

    const sortConversations = (conversations: Conversations): Conversations => {
        // sort conversations by last activity
        const sortedIds = Object.keys(conversations).sort((a, b) => {
            if (conversations[a].lastUpdatedTimestamp === undefined) {
                return 1;
            }
            if (conversations[b].lastUpdatedTimestamp === undefined) {
                return -1;
            }
            // eslint-disable-next-line  @typescript-eslint/no-non-null-assertion
            return conversations[a].lastUpdatedTimestamp! - conversations[b].lastUpdatedTimestamp!;
        });

        // Add conversations to sortedConversations in the order of sortedIds.
        const sortedConversations: Conversations = {};
        sortedIds.forEach((id) => {
            sortedConversations[id] = conversations[id];
        });
        return sortedConversations;
    };

    useEffect(() => {
        // Ensure local component state is in line with app state.
        if (filterText !== '') {
            // Reapply search string to the updated conversations list.
            const filteredConversations: Conversations = {};
            for (const key in conversations) {
                if (conversations[key].title.toLowerCase().includes(filterText.toLowerCase())) {
                    filteredConversations[key] = conversations[key];
                }
            }
            setConversationsView(filteredConversations);
        } else {
            // If no search string, show full conversations list.
            setConversationsView(sortConversations(conversations));
        }
    }, [conversations, filterText]);

    const onFilterClick = () => {
        setIsFiltering(true);
    };

    const onFilterCancel = () => {
        setFilterText('');
        setIsFiltering(false);
    };

    const onSearch = (ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
        ev.preventDefault();
        setFilterText(data.value);
    };

    const fileUploaderRef = useRef<HTMLInputElement>(null);
    const onUpload = useCallback(
        (file: File) => {
            console.log('asdf');
            fileHandler.loadFile<Bot>(file, chat.uploadBot).catch((error) =>
                dispatch(
                    addAlert({
                        message: `Failed to parse uploaded file. ${error instanceof Error ? error.message : ''}`,
                        type: AlertType.Error,
                    }),
                ),
            );
        },
        [fileHandler, chat, dispatch],
    );

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {!isFiltering && (
                    <>
                        <Text weight="bold" size={500} className={classes.title} as="h2">
                            Conversations
                        </Text>

                        <Button icon={<Filter20 />} appearance="transparent" onClick={onFilterClick} />
                        <NewBotMenu onFileUpload={() => fileUploaderRef.current?.click()} />

                        <FileUploader
                            ref={fileUploaderRef}
                            acceptedExtensions={['.txt', '.json']}
                            onSelectedFile={onUpload}
                        />
                    </>
                )}
                {isFiltering && (
                    <>
                        <Input
                            placeholder="Filter by name"
                            className={mergeClasses(classes.input, classes.title)}
                            onChange={onSearch}
                            autoFocus
                        />
                        <Button icon={<Dismiss20 />} appearance="transparent" onClick={onFilterCancel} />
                    </>
                )}
            </div>
            <Text as="h3" className={classes.botsHeader}>
                Your bots
            </Text>
            <div aria-label={'chat list'} className={classes.list}>
                {Object.keys(conversationsView).map((id) => {
                    const convo = conversationsView[id];
                    const messages = convo.messages;
                    const lastMessage = messages[convo.messages.length - 1];
                    const isSelected = id === selectedId;

                    return (
                        <ChatListItem
                            id={id}
                            key={id}
                            isSelected={isSelected}
                            header={convo.title}
                            timestamp={convo.lastUpdatedTimestamp ?? lastMessage.timestamp}
                            preview={
                                messages.length > 0
                                    ? lastMessage.type === ChatMessageType.Document
                                        ? 'Sent a file'
                                        : isPlan(lastMessage.content)
                                        ? 'Click to view proposed plan'
                                        : lastMessage.content
                                    : 'Click to start the chat'
                            }
                            botProfilePicture={convo.botProfilePicture}
                        />
                    );
                })}
            </div>
        </div>
    );
};
