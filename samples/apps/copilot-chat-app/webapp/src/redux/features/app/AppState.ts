import { AlertType } from '../../../libs/models/AlertType';

// Copyright (c) Microsoft. All rights reserved.
export interface AppState {
    alerts?: Alerts;
}

export interface Alert {
    message: string;
    type: AlertType;
}

export type Alerts = Record<string, Alert>;
