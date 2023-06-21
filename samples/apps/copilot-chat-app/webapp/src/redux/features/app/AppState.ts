// Copyright (c) Microsoft. All rights reserved.

import { AlertType } from '../../../libs/models/AlertType';

export interface AppState {
    alerts: Alert[];
}

export interface Alert {
    message: string;
    type: AlertType;
}
