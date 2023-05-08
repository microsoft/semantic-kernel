// Copyright (c) Microsoft. All rights reserved.

import { useAccount, useMsal } from '@azure/msal-react';
import { Label, makeStyles } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';
import { ChatUser } from '../../libs/models/ChatUser';
import { SKBotAudienceMember } from '../../libs/semantic-kernel/bot-agent/models/SKBotAudienceMember';
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
    const { accounts } = useMsal();
    const account = useAccount(accounts[0] || {});
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { audience, botTypingTimestamp } = conversations[selectedId];
    const [typing, setTyping] = React.useState<SKBotAudienceMember[]>([]);

    // if audience is changed, check back in 5 seconds to see if they are still typing
    React.useEffect(() => {
        const timeoutDuration = Constants.bot.typingIndicatorTimeoutMs;
        const checkAreTyping = () => {
            const updatedTyping: ChatUser[] = [];
            if (botTypingTimestamp > Date.now() - timeoutDuration) {
                updatedTyping.push({
                    ...Constants.bot.profile,
                    online: true,
                    lastTypingTimestamp: botTypingTimestamp,
                });
            }
            const typingAudience = audience.filter(
                (chatUser: ChatUser) =>
                    chatUser.id !== account?.homeAccountId &&
                    chatUser.lastTypingTimestamp > Date.now() - timeoutDuration,
            );
            updatedTyping.push(...typingAudience);

            setTyping(updatedTyping);
        };
        checkAreTyping();
        const timer = setTimeout(() => {
            checkAreTyping();
        }, timeoutDuration + 1000);
        return () => clearTimeout(timer);
    }, [account?.homeAccountId, audience, botTypingTimestamp]);

    let message = '';
    switch (typing.length) {
        case 0:
            break;
        case 1:
            message = `${typing[0].fullName} is typing...`;
            break;
        case 2:
            message = `${typing[0].fullName} and ${typing[1].fullName} are typing...`;
            break;
        default:
            message = `${typing[0].fullName}, ${typing[1].fullName}, and ${typing.length - 2} others are typing...`;
            break;
    }

    return (
        <div className={classes.root}>
            <Label>{message}</Label>
        </div>
    );
};
