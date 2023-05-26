// Copyright (c) Microsoft. All rights reserved.

import { Button, Input, InputOnChangeData, makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { Tree, TreeItem } from '@fluentui/react-components/unstable';
import { Dismiss20Regular, Filter20Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';
import { useChat } from '../../../libs/useChat';
import { isPlan } from '../../../libs/utils/PlanUtils';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { ChatListItem } from './ChatListItem';
import { NewBotMenu } from './NewBotMenu';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        width: '25%',
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
    const chat = useChat();

    const [isFiltering, setIsFiltering] = useState(false);
    const [searchString, setSearchString] = useState('');

    const { conversations, filteredConversations, selectedId } = useAppSelector(
        (state: RootState) => state.conversations,
    );
    const displayedConversations = isFiltering ? filteredConversations : conversations;

    const onFilterClick = () => {
        setIsFiltering(!isFiltering);
    };

    const onFilterCancel = () => {
        chat.clearConversationsFilter();
        setSearchString('');
        setIsFiltering(!isFiltering);
    };

    const onSearch = (ev: any, data: InputOnChangeData) => {
        ev.preventDefault();
        setSearchString(data.value);
        chat.filterChats(data.value);
    };

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {!isFiltering && (
                    <>
                        <Text weight="bold" size={500}>
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
                            className={classes.input}
                            value={searchString}
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
                {Object.keys(displayedConversations).map((id) => {
                    const convo = conversations[id];
                    const messages = convo.messages;
                    const lastMessage = convo.messages.length - 1;
                    return (
                        <TreeItem
                            key={id}
                            leaf
                            style={id === selectedId ? { background: tokens.colorNeutralBackground1 } : undefined}
                        >
                            <ChatListItem
                                id={id}
                                header={convo.title}
                                timestamp={convo.lastUpdatedTimestamp ?? messages[lastMessage].timestamp}
                                preview={
                                    messages.length > 0
                                        ? isPlan(messages[lastMessage].content)
                                            ? 'Click to view proposed plan'
                                            : (messages[lastMessage].content as string)
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
