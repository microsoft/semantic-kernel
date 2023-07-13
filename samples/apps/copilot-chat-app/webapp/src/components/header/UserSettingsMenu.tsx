// Copyright (c) Microsoft. All rights reserved.

import { FC, useCallback, useState } from 'react';

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
import { useAppSelector } from '../../redux/app/hooks';
import { RootState, resetState } from '../../redux/app/store';
import { SettingsDialog } from './settings-dialog.tsx/SettingsDialog';

export const useClasses = makeStyles({
    root: {
        marginRight: '20px',
    },
    persona: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingVerticalMNudge),
    },
});

interface IUserSettingsProps {
    setLoadingState: () => void;
}

export const UserSettingsMenu: FC<IUserSettingsProps> = ({ setLoadingState }) => {
    const classes = useClasses();
    const { instance } = useMsal();

    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);

    const [openSettingsDialog, setOpenSettingsDialog] = useState(false);

    const onLogout = useCallback(() => {
        setLoadingState();
        AuthHelper.logoutAsync(instance);
        resetState();
    }, [instance, setLoadingState]);

    return (
        <>
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    {
                        <Avatar
                            className={classes.root}
                            key={activeUserInfo?.username}
                            name={activeUserInfo?.username}
                            size={28}
                            badge={{ status: 'available' }}
                        />
                    }
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <Persona
                            className={classes.persona}
                            name={activeUserInfo?.username}
                            secondaryText={activeUserInfo?.email}
                            presence={{ status: 'available' }}
                            avatar={{ color: 'colorful' }}
                        />
                        <MenuDivider />
                        <MenuItem data-testid="settingsMenuItem" onClick={() => setOpenSettingsDialog(true)}>
                            Settings
                        </MenuItem>
                        <MenuItem data-testid="logOutMenuButton" onClick={onLogout}>
                            Sign out
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            <SettingsDialog open={openSettingsDialog} closeDialog={() => setOpenSettingsDialog(false)} />
        </>
    );
};
