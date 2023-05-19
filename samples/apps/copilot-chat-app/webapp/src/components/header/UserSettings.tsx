// Copyright (c) Microsoft. All rights reserved.

import { FC } from 'react';

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

export const useClasses = makeStyles({
    root: {
        marginRight: '20px',
    },
    persona: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingVerticalMNudge),
        '&:hover': {},
    },
});

export const UserSettings: FC = () => {
    const classes = useClasses();
    const { instance } = useMsal();

    const account = instance.getActiveAccount();

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                {
                    <Avatar
                        className={classes.root}
                        key={account?.name}
                        name={account?.name}
                        size={28}
                        badge={{ status: 'available' }}
                    />
                }
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    <MenuItem className={classes.persona}>
                        <Persona
                            name={account?.name}
                            secondaryText={account?.username}
                            presence={{ status: 'available' }}
                            avatar={{ color: 'colorful' }}
                        />
                    </MenuItem>
                    <MenuDivider />
                    <MenuItem onClick={async () => await AuthHelper.logoutAsync(instance)}>Log Out</MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
