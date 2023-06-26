// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import React from 'react';
import { IChatUser } from '../../libs/models/ChatUser';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { TypingIndicatorRenderer } from './typing-indicator/TypingIndicatorRenderer';

export const ChatStatus: React.FC = () => {
    const { instance } = useMsal();
    const account = instance.getActiveAccount();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { users } = conversations[selectedId];
    const [typingUserList, setTypingUserList] = React.useState<IChatUser[]>([]);

    React.useEffect(() => {
        const checkAreTyping = () => {
            const updatedTypingUsers: IChatUser[] = users.filter(
                (chatUser: IChatUser) =>
                    chatUser.id !== account?.homeAccountId &&
                    chatUser.isTyping,
            );

            setTypingUserList(updatedTypingUsers);
        };
        checkAreTyping();
    }, [account?.homeAccountId, users]);

    return (
        <TypingIndicatorRenderer isBotTyping={conversations[selectedId].isBotTyping} numberOfUsersTyping={typingUserList.length} />
    );
};
