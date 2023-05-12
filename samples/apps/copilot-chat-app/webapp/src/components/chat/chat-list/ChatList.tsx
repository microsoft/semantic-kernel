// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { Tree, TreeItem } from '@fluentui/react-components/unstable';
import { FC } from 'react';
import { isPlan } from '../../../libs/semantic-kernel/sk-utilities';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { ChatListItem } from './ChatListItem';
import { NewBotMenu } from './NewBotMenu';

const useClasses = makeStyles({
    root: {
        width: '25%',
        minHeight: '100%',
        overflowX: 'hidden',
        overflowY: 'auto',
        scrollbarWidth: 'thin',
        backgroundColor: '#F0F0F0',
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginRight: '1em',
        marginLeft: '1em',
        alignItems: 'center',
        height: '4.8em',
        '& controls': {
            ...shorthands.gap('10px'),
            display: 'flex',
        },
    },
    label: {
        marginLeft: '1em',
    },
});

export const ChatList: FC = () => {
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    return (
        <>
            <div className={classes.root}>
                <div className={classes.header}>
                    <Text weight="bold" size={500}>
                        Conversations
                    </Text>
                    <NewBotMenu />
                </div>
                <Tree aria-label={'chat list'}>
                    {Object.keys(conversations).map((id) => {
                        const convo = conversations[id];
                        const messages = convo.messages;
                        const lastMessage = convo.messages.length - 1;
                        return (
                            <TreeItem
                                key={id}
                                leaf
                                style={
                                    id === selectedId
                                        ? { background: tokens.colorNeutralBackground1 }
                                        : undefined
                                }
                            >
                                <ChatListItem
                                    id={id}
                                    header={convo.title}
                                    timestamp={new Date(messages[lastMessage].timestamp).toLocaleTimeString([], {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                    })}
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
        </>
    );
};
