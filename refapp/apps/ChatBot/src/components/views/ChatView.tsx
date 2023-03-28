import { makeStyles } from "@fluentui/react-components";
import { FC } from "react";
import { ChatList } from "../chat/chat-list/ChatList";
import { ChatWindow } from "../chat/ChatWindow";

const useClasses = makeStyles({
    container: {
        display: 'flex',
        flexDirection: 'row',
        alignContent: 'start',
        justifyContent: 'space-between',
        width: '100%',
        minHeight: '95vh',
    }
});

export const ChatView: FC = () => {
    const classes = useClasses();
    return (
        <div className={classes.container}>
            <ChatList />
            <ChatWindow />
        </div>
    )
}