import { makeStyles, shorthands } from '@fluentui/react-components';
import { FC } from 'react';
import { ChatWindow } from '../chat/ChatWindow';
import { ChatList } from '../chat/chat-list/ChatList';

const useClasses = makeStyles({
    container: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'row',
        alignContent: 'start',
        height: '100%',
    },
});

export const ChatView: FC = () => {
    const classes = useClasses();

    return (
        <div className={classes.container}>
            <ChatList />
            <ChatWindow />
        </div>
    );
};
