/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export interface IDeployment {
    id: string;
    model: string;
    status: string;
    object: string;
}

export interface IAzureDeployments {
    data: IDeployment[];
}
