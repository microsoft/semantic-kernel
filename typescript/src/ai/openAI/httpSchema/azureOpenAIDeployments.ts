// Copyright (c) Microsoft Corporation. All rights reserved.

export interface IAzureOpenAIDeployment {
    id: string;
    model: string;
    status: string;
    object: string;
}

export interface IAzureOpenAIDeployments {
    data: IAzureOpenAIDeployment[];
}

export class AzureOpenAIDeployment implements IAzureOpenAIDeployment {
    private _status: string = '';
    private _type: string = '';
    public id: string = '';
    public model: string = '';

    public get status(): string {
        return this._status;
    }

    public set status(value: string) {
        this._status = value?.trim().toLowerCase() ?? '';
    }

    public get object(): string {
        return this._type;
    }

    public set object(value: string) {
        this._type = value?.trim().toLowerCase() ?? '';
    }

    public isAvailableDeployment(): boolean {
        return this.object === 'deployment' && this.status === 'succeeded';
    }
}

export class AzureOpenAIDeployments implements IAzureOpenAIDeployments {
    public data: IAzureOpenAIDeployment[] = [];
}
