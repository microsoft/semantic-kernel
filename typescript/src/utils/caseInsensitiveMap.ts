/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export class CaseInsensitiveMap<T, U> extends Map<T, U> {
    public override set(key: T, value: U): this {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.set(key, value);
    }

    public override get(key: T): U | undefined {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.get(key);
    }

    public override has(key: T): boolean {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.has(key);
    }

    public override delete(key: T): boolean {
        if (typeof key === 'string') {
            key = key.toLowerCase() as any as T;
        }

        return super.delete(key);
    }
}
