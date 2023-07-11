// Copyright (c) Microsoft. All rights reserved.

import { Constants } from '../../../Constants';

export interface UsersState {
    users: Users;
}

export const initialState: UsersState = {
    users: {
        bot: Constants.bot.profile,
    },
};

export type Users = Record<string, UserData>;

export interface UserData {
    id: string;
    displayName?: string;
    userPrincipalName?: string; // email
    photo?: string | undefined; // TODO: change this to required when we enable token / Graph support
}
