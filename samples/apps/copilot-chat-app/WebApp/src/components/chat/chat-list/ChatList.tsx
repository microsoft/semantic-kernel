import { Button, Label, makeStyles, shorthands, Text } from '@fluentui/react-components';
import { Tree, TreeItem } from '@fluentui/react-components/unstable';

import { BotAdd20Regular } from '@fluentui/react-icons';
import { FC } from 'react';
import { useChat } from '../../../libs/useChat';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { ChatListItem } from './ChatListItem';

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
    const chat = useChat();

    const onAddChat = () => {
        chat.createChat();
    };

    return (
        <>
            <div className={classes.root}>
                <div className={classes.header}>
                    <Text weight="bold" size={500}>
                        Conversations
                    </Text>
                    <div>
                        {/* TODO: Allow users to filter conversations by name
                        <Button
                        icon={<Filter20Regular />}
                        appearance="transparent" /> */}
                        <Button icon={<BotAdd20Regular />} appearance="transparent" onClick={onAddChat} />
                    </div>
                </div>
                <Label className={classes.label}>Your Bot</Label>
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
                                        ? { background: 'var(--colorNeutralBackground1Selected)' }
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
                                        messages.length > 0 ? messages[lastMessage].content : 'Click to start the chat'
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
