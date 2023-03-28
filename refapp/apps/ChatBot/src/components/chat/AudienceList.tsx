// Copyright (c) Microsoft. All rights reserved.

import { useAccount } from '@azure/msal-react';
import { makeStyles, Persona } from '@fluentui/react-components';
import { useChat } from '../../libs/useChat';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';

const useClasses = makeStyles({
    root: {
        width: '100%',
        textAlign: 'end',
        height: '32px',
        display: 'flex',
    },
});

export const AudienceList: React.FC = () => {
    const classes = useClasses();
    const account = useAccount();
    const chat = useChat();
    const { audience } = useAppSelector((state: RootState) => state.chat);

    const botMember = chat.getAudienceMemberForId('bot');

    return (
        <div className={classes.root}>
            {audience
                .filter((member) => member.id !== account?.homeAccountId)
                .map((member) => (
                    <Persona
                        key={member.id}
                        size="small"
                        avatar={{ image: { src: member.photo } }}
                        presence={{ status: member.online ? 'available' : 'offline' }}
                    />
                ))}
            <Persona size="small" avatar={{ image: { src: botMember?.photo } }} presence={{ status: 'available' }} />
        </div>
    );
};
