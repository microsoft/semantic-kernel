import { AlertType } from '../../../libs/models/AlertType';

// Copyright (c) Microsoft. All rights reserved.
export interface AppState {
    alert?: {
        message: string;
        type: AlertType;
    };
    unclaimed?: boolean;
    documentId?: string;
}
