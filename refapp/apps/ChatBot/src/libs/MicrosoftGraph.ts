// Copyright (c) Microsoft. All rights reserved.

// Copyright (c) Microsoft. All rights reserved.
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { Client, ResponseType } from '@microsoft/microsoft-graph-client';
import { msalInstance } from '../main';
import { AuthHelper } from './AuthHelper';

const getAsync = async <T>(url: string): Promise<T> => {
    const client = await getClientAsync();
    return (await client.api(url).get()) as T;
};

const getMyPhotoAsync = async (): Promise<string> => {
    return await getPhotoAsync('/me/photo/$value');
};

const getPhotoAsync = async (url: string): Promise<string> => {
    const client = await getClientAsync();
    const response = (await client.api(url).responseType(ResponseType.RAW).get()) as Response;
    const blob = await response.blob();
    return await blobToBase64Async(blob);
};

const getClientAsync = async (): Promise<Client> => {
    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const response = await msalInstance
        .acquireTokenSilent({
            ...AuthHelper.loginRequest,
            account,
        })
        .catch(async (error: any) => {
            if (error instanceof InteractionRequiredAuthError) {
                return await AuthHelper.loginAsync(msalInstance);
            }
            throw error;
        });

    if (!response) {
        throw new Error('error acquiring access token');
    }

    return Client.init({
        authProvider: (done) => {
            done(null, response.accessToken);
        },
    });
};

const blobToBase64Async = async (blob: Blob): Promise<string> => {
    return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => {
            resolve(reader.result as string);
        };
        reader.readAsDataURL(blob);
    });
};

export const MicrosoftGraph = {
    getAsync,
    getMyPhotoAsync,
    getPhotoAsync,
};
