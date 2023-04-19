import { AlertType } from '../../../libs/models/AlertType';

// Copyright (c) Microsoft. All rights reserved.
export interface AppState {
    alerts?: Alerts;
    unclaimed?: boolean;
    documentId?: string;
}

export type Alert = {
    message: string;
    type: AlertType;
};

export type Alerts = { [key: string]: Alert };
