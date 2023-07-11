// Copyright (c) Microsoft. All rights reserved.

import { AlertType } from '../../../libs/models/AlertType';
import { UserData } from '../users/UsersState';

export interface AppState {
    alerts: Alert[];
    activeUserInfo?: UserData;
}

export interface Alert {
    message: string;
    type: AlertType;
}
