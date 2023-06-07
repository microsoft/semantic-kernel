// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Label, makeStyles } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';
import { IChatUser } from '../../libs/models/ChatUser';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';

const useClasses = makeStyles({
    root: {
        paddingLeft: '56px',
        height: '20px',
        display: 'flex',
        alignItems: 'center',
    },
});

export const ChatStatus: React.FC = () => {
    const classes = useClasses();
    const { instance } = useMsal();
    const account = instance.getActiveAccount();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { users } = conversations[selectedId];
    const [typingUserList, setTypingUserList] = React.useState<IChatUser[]>([]);

    // If users is changed, check back in 5 seconds to see if they are still typing.
    React.useEffect(() => {
        const timeoutDuration = Constants.bot.typingIndicatorTimeoutMs;
        const checkAreTyping = () => {
            const updatedTypingUsers: IChatUser[] = users.filter(
                (chatUser: IChatUser) =>
                    chatUser.id !== account?.homeAccountId &&
                    chatUser.lastTypingTimestamp > Date.now() - timeoutDuration,
            );

            setTypingUserList(updatedTypingUsers);
        };
        checkAreTyping();
        const timer = setTimeout(() => {
            checkAreTyping();
        }, timeoutDuration + 1000);
        return () => clearTimeout(timer);
    }, [account?.homeAccountId, users]);

    let message = '';
    switch (typingUserList.length) {
        case 0:
            break;
        case 1:
            message = `${typingUserList[0].fullName} is typing...`;
            break;
        case 2:
            message = `${typingUserList[0].fullName} and ${typingUserList[1].fullName} are typing...`;
            break;
        default:
            message = `${typingUserList[0].fullName}, ${typingUserList[1].fullName}, and ${typingUserList.length - 2} others are typing...`;
            break;
    }

    return (
        <div className={classes.root}>
            <Label>{message}</Label>
        </div>
    );
};
