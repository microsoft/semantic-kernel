// Copyright (c) Microsoft. All rights reserved.

import { FC, useEffect, useState } from 'react';

import {
    Avatar,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { IChatUser } from '../../../libs/models/ChatUser';
import { useGraph } from '../../../libs/useGraph';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { setUsersLoaded } from '../../../redux/features/conversations/conversationsSlice';
import { Users } from '../../../redux/features/users/UsersState';
import { ScrollBarStyles } from '../../../styles';

interface ShareBotMenuProps {
    participants: IChatUser[];
}
const useClasses = makeStyles({
    root: {
        display: 'flex',
        ...ScrollBarStyles,
        ...shorthands.padding(tokens.spacingVerticalNone, tokens.spacingVerticalXS),
        ...shorthands.border(tokens.spacingVerticalM),
        ...shorthands.borderRight(tokens.spacingHorizontalXS),
    },
    list: {
        display: 'flex',
        flexDirection: 'column',
        height: 'min-content',
        maxHeight: '220px',
        width: '200px',
        overflowWrap: 'anywhere',
        ...shorthands.gap(tokens.spacingVerticalS),
    },
});

export const ParticipantsList: FC<ShareBotMenuProps> = ({ participants }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { users } = useAppSelector((state: RootState) => state.users);
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const msGraph = useGraph();

    const chatUsers = conversations[selectedId].users;
    const [loadedParticipants, setLoadedParticipants] = useState(mapParticipantsNames(participants, users));

    useEffect(() => {
        if (!conversations[selectedId].userDataLoaded) {
            void msGraph.loadUsers(chatUsers.map((user: IChatUser) => user.id)).then((loadedUsers?: Users) => {
                if (loadedUsers) {
                    dispatch(setUsersLoaded(selectedId));
                    setLoadedParticipants(mapParticipantsNames(participants, loadedUsers));
                }
            });
        }

        // Limiting dependencies or else this effect is triggered on all user typing events or new chat messages
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedId, chatUsers.length]);

    return (
        <Popover positioning={'below-end'} size="small">
            <PopoverTrigger>
                <Tooltip content="Chat participants" relationship="label">
                    <Avatar initials={`+${Math.min(participants.length, 100)}`} />
                </Tooltip>
            </PopoverTrigger>
            <PopoverSurface className={classes.root}>
                <div className={classes.list}>
                    {loadedParticipants.map((participant) => (
                        <Persona
                            textAlignment="center"
                            name={participant.name}
                            key={participant.id}
                            avatar={{ color: 'colorful' }}
                        />
                    ))}
                </div>
            </PopoverSurface>
        </Popover>
    );
};

const mapParticipantsNames = (participants: IChatUser[], usersData: Users) => {
    return participants.map((participant) => ({
        ...participant,
        // falsy lint check, users[userId] can be null if user data hasn't been loaded
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        name: usersData[participant.id.split('.')[0]]?.displayName ?? participant.id,
    }));
};
