// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { initialState, UserData, Users, UsersState } from './UsersState';

export const usersSlice = createSlice({
    name: 'users',
    initialState,
    reducers: {
        setUsers: (state: UsersState, action: PayloadAction<Users>) => {
            state.users = action.payload;
        },
        addUser: (state: UsersState, action: PayloadAction<UserData>) => {
            const newUser = action.payload;
            state.users = {
                ...state.users,
                [newUser.id]: action.payload,
            };
        },
    },
});

export const { setUsers, addUser } = usersSlice.actions;

export default usersSlice.reducer;
