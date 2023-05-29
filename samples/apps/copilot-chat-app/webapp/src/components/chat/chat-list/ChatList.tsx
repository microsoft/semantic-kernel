// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { Tree, TreeItem } from '@fluentui/react-components/unstable';
import { FC } from 'react';
import { isPlan } from '../../../libs/utils/PlanUtils';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
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
});

export const ChatList: FC = () => {
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Text weight="bold" size={500} className={classes.title}>
                    Conversations
                </Text>
                <NewBotMenu />
            </div>
            <Tree aria-label={'chat list'} className={classes.list}>
                {Object.keys(conversations).map((id) => {
                    const convo = conversations[id];
                    const messages = convo.messages;
                    const lastMessage = convo.messages.length - 1;
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
