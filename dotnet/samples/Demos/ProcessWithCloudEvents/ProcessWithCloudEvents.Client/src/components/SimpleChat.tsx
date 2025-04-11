/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { Chat, ChatMessage, ChatMyMessage } from "@fluentui-contrib/react-chat";
import { Divider, makeStyles } from "@fluentui/react-components";
import { ChatMessageContent, ChatUser } from "../common/ChatConstants";

const useStyles = makeStyles({
    chatContainer: {
        minHeight: "50vh",
        overflowY: "auto",
        boxSizing: "border-box",
        border: "1px solid #ccc",
        maxHeight: "50vh",
        width: "100%",
    },
});

interface SimpleChatProps {
    messages: ChatMessageContent[];
}

const SimpleChat: React.FC<SimpleChatProps> = ({ messages }) => {
    const styles = useStyles();

    const renderMessage = (message: ChatMessageContent) => {
        if (message.action) {
            return <Divider key={`action-${message.action}-${message.sender}`}>{message.action}</Divider>;
        }

        switch (message.sender) {
            case ChatUser.ASSISTANT:
                return <ChatMessage author={"Assistant"} timestamp={message.timestamp} key={`assistant-${message.timestamp}`}>{message.content}</ChatMessage>;

            case ChatUser.USER:
                return <ChatMyMessage author={"User"} timestamp={message.timestamp} key={`user-${message.timestamp}`}>{message.content}</ChatMyMessage>;

            default:
                return <></>;
        }
    };

    return (
        <Chat className={styles.chatContainer}>
            {messages.map((m) => renderMessage(m))}
        </Chat>
    );
};

export default SimpleChat;
