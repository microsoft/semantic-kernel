// Copyright (c) Microsoft. All rights reserved.

export interface UsersState {
    users: Users;
    loggedInUserId: string;
}

export const initialState: UsersState = {
    users: {},
    loggedInUserId: '',
};

export type Users = Record<string, UserData>;

export type UserData = {
    id: string;
    displayName?: string;
    userPrincipalName?: string;
};
