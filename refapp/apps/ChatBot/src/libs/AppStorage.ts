// Copyright (c) Microsoft. All rights reserved.

export class AppStorage {
    public static instance: AppStorage | undefined;

    public static getInstance = () => {
        if (!this.instance) {
            this.instance = new AppStorage();
        }
        return this.instance;
    };

    public getValueOrDefault = <T>(storageKey: string, defaultValue: T) => {
        const value = window.localStorage.getItem(storageKey);
        if (value) {
            return value as T;
        }
        return defaultValue;
    };

    public saveValue = (storageKey: string, value?: unknown) => {
        if (!value) {
            window.localStorage.removeItem(storageKey);
            return;
        }

        window.localStorage.setItem(storageKey, value as string);
    };

    public loadObject = <T>(storageKey: string) => {
        return this.deserializeData<T>(window.localStorage.getItem(storageKey));
    };

    public saveObject = (storageKey: string, object?: unknown) => {
        if (!object) {
            window.localStorage.removeItem(storageKey);
            return;
        }

        window.localStorage.setItem(storageKey, JSON.stringify(object));
    };

    private readonly deserializeData = <T>(data: string | null) => {
        if (!data) {
            return undefined;
        }
        try {
            return JSON.parse(data) as T;
        } catch (error) {
            console.error(error);
            return undefined;
        }
    };
}
