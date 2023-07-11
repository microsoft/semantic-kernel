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
import { useAppSelector } from '../../redux/app/hooks';
import { RootState, resetState } from '../../redux/app/store';

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

    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);

    const onLogout = useCallback(() => {
        setLoadingState();
        AuthHelper.logoutAsync(instance);
        resetState();
    }, [instance, setLoadingState]);
    const handleMenuItemClick = () => {
        alert(
            'Display a settings box with: 1/ enable disable dark mode, 2/ enable disable downloading and uploading a chat session, 3/ enable disable sharing live chat session codes. Have a flipper to display Advanced. In Advanced section let the user edit: 1/ the metaprompt, 2/ see the short term memories, 3/ see the long term memories.',
        );
    };
    return (
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
                    <MenuItem className={classes.persona}>
                        <Persona
                            name={activeUserInfo?.username}
                            secondaryText={activeUserInfo?.email}
                            presence={{ status: 'available' }}
                            avatar={{ color: 'colorful' }}
                        />
                    </MenuItem>
                    <MenuItem onClick={handleMenuItemClick}>Settings</MenuItem>
                    <MenuDivider />
                    <MenuItem data-testid="logOutMenuButton" onClick={onLogout}>
                        Sign out
                    </MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
