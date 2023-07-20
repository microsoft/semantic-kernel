// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { IChatUser } from '../../libs/models/ChatUser';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { TypingIndicatorRenderer } from './typing-indicator/TypingIndicatorRenderer';

export const ChatStatus: React.FC = () => {
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { users } = conversations[selectedId];
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);
    const [typingUserList, setTypingUserList] = React.useState<IChatUser[]>([]);

    React.useEffect(() => {
        const checkAreTyping = () => {
            const updatedTypingUsers: IChatUser[] = users.filter(
                (chatUser: IChatUser) => chatUser.id !== activeUserInfo?.id && chatUser.isTyping,
            );

            setTypingUserList(updatedTypingUsers);
        };
        checkAreTyping();
    }, [activeUserInfo, users]);

    return (
        <TypingIndicatorRenderer
            botResponseStatus={conversations[selectedId].botResponseStatus}
            numberOfUsersTyping={typingUserList.length}
        />
    );
};
