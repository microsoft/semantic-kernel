import { makeStyles } from '@fluentui/react-components';
import { FC } from 'react';
import { ChatWindow } from '../chat/ChatWindow';
import { ChatList } from '../chat/chat-list/ChatList';

const useClasses = makeStyles({
    container: {
        display: 'flex',
        flexDirection: 'row',
        alignContent: 'start',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
        maxHeight: '100%',
        position: 'fixed',
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
