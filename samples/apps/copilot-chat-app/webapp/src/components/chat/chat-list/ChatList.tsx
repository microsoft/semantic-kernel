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
import { Tree, TreeItem } from '@fluentui/react-components/unstable';
import { Dismiss20Regular, Filter20Regular } from '@fluentui/react-icons';
import { FC, useEffect, useState } from 'react';
import { ChatMessageType } from '../../../libs/models/ChatMessage';
import { isPlan } from '../../../libs/utils/PlanUtils';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { Conversations } from '../../../redux/features/conversations/ConversationsState';
import { Breakpoints } from '../../../styles';
import { ChatListItem } from './ChatListItem';
import { NewBotMenu } from './NewBotMenu';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        width: '25%',
        minWidth: '5rem',
        backgroundColor: '#F0F0F0',
        flexDirection: 'column',
        '@media (max-width: 25%)': {
            display: 'none',
        },
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
        ...shorthands.margin('4px'),
        '&::-webkit-scrollbar-track': {
            backgroundColor: 'transparent',
        },
        alignItems: 'stretch',
    },
    header: {
        ...shorthands.padding(tokens.spacingVerticalXXS, tokens.spacingHorizontalXS),
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginRight: '1em',
        marginLeft: '1em',
        alignItems: 'center',
        height: '4.8em',
        ...Breakpoints.small({
            justifyContent: 'center',
        }),
    },
    title: {
        ...Breakpoints.small({
            display: 'none',
        }),
    },
    input: {
        ...shorthands.padding(tokens.spacingHorizontalNone),
        ...shorthands.border(tokens.borderRadiusNone),
        width: 'calc(100% - 24px)',
        backgroundColor: 'transparent',
        fontSize: '20px',
    },
});

export const ChatList: FC = () => {
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    const [isFiltering, setIsFiltering] = useState(false);
    const [filterText, setFilterText] = useState('');
    const [conversationsView, setConversationsView] = useState(conversations);

    useEffect(() => {
        // Ensure local component state is in line with app state.
        if (filterText !== '') {
            // Reapply search string to the updated conversations list.
            const filteredConversations: Conversations = {};
            for (var key in conversations) {
                if (conversations[key].title.toLowerCase().includes(filterText.toLowerCase())) {
                    filteredConversations[key] = conversations[key];
                }
            }
            setConversationsView(filteredConversations);
        }
        else {
            // If no search string, show full conversations list.
            setConversationsView(conversations);
        }
    }, [conversations, filterText]);

    const onFilterClick = () => {
        setIsFiltering(true);
    };

    const onFilterCancel = () => {
        setFilterText('');
        setIsFiltering(false);
    };

    const onSearch = (ev: any, data: InputOnChangeData) => {
        ev.preventDefault();
        setFilterText(data.value);
    };

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {!isFiltering && (
                    <>
                        <Text weight="bold" size={500} className={classes.title}>
                            Conversations
                        </Text>
                        <div>
                            <Button icon={<Filter20Regular />} appearance="transparent" onClick={onFilterClick} />
                            <NewBotMenu />
                        </div>
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
                        <div>
                            <Button icon={<Dismiss20Regular />} appearance="transparent" onClick={onFilterCancel} />
                        </div>
                    </>
                )}
            </div>
            <Tree aria-label={'chat list'} className={classes.list}>
                {Object.keys(conversationsView).map((id) => {
                    const convo = conversationsView[id];
                    const messages = convo.messages;
                    const lastMessage = messages[convo.messages.length - 1];
                    const isSelected = id === selectedId;

                    return (
                        <TreeItem
                            key={id}
                            leaf
                            style={isSelected ? { background: tokens.colorNeutralBackground1 } : undefined}
                        >
                            <ChatListItem
                                id={id}
                                isSelected={isSelected}
                                header={convo.title}
                                timestamp={convo.lastUpdatedTimestamp ?? lastMessage.timestamp}
                                preview={
                                    messages.length > 0
                                        ? lastMessage.type === ChatMessageType.Document
                                            ? 'Sent a file'
                                            : isPlan(lastMessage.content)
                                            ? 'Click to view proposed plan'
                                            : (lastMessage.content as string)
                                        : 'Click to start the chat'
                                }
                                botProfilePicture={convo.botProfilePicture}
                            />
                        </TreeItem>
                    );
                })}
            </Tree>
        </div>
    );
};
