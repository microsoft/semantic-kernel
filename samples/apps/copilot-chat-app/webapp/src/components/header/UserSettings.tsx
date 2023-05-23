// Copyright (c) Microsoft. All rights reserved.

import { FC, useCallback } from 'react';

import { useMsal } from '@azure/msal-react';
import {
    Avatar,
    Menu,
    MenuDivider,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { AuthHelper } from '../../libs/auth/AuthHelper';
import { resetState } from '../../redux/app/store';

export const useClasses = makeStyles({
    root: {
        marginRight: '20px',
    },
    persona: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingVerticalMNudge),
        '&:hover': {},
    },
});

interface IUserSettingsProps {
    setLoadingState: () => void;
}

export const UserSettings: FC<IUserSettingsProps> = ({ setLoadingState }) => {
    const classes = useClasses();
    const { instance } = useMsal();

    const account = instance.getActiveAccount();

    const onLogout = useCallback(async () => {
        setLoadingState();
        await AuthHelper.logoutAsync(instance);
        resetState();
    }, [instance, setLoadingState]);

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                {
                    <Avatar
                        className={classes.root}
                        key={account?.name ?? account?.username}
                        name={account?.name ?? account?.username}
                        size={28}
                        badge={{ status: 'available' }}
                    />
                }
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    <MenuItem className={classes.persona}>
                        <Persona
                            name={account?.name ?? account?.username}
                            secondaryText={account?.username}
                            presence={{ status: 'available' }}
                            avatar={{ color: 'colorful' }}
                        />
                    </MenuItem>
                    <MenuDivider />
                    <MenuItem onClick={onLogout}>Log Out</MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
