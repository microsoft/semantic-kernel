/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export class CaseInsensitiveMap<T, U> extends Map<T, U> {
    public set(key: T, value: U): this {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.set(key, value);
    }

    public get(key: T): U | undefined {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.get(key);
    }

    public has(key: T): boolean {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.has(key);
    }

    public delete(key: T): boolean {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.delete(key);
    }
}
