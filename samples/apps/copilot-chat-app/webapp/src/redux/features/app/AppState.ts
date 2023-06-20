import { AlertType } from '../../../libs/models/AlertType';

// Copyright (c) Microsoft. All rights reserved.
export interface AppState {
    alerts?: Alerts;
    loggedInUserInfo?: LoggedInUserInfo;
}

export interface LoggedInUserInfo {
    id: string;
    email: string;
    fullName: string;
}

export type Alert = {
    message: string;
    type: AlertType;
};

export type Alerts = { [key: string]: Alert };
