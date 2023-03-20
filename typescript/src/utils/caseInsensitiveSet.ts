/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export class CaseInsensitiveSet<T> extends Set<T> {
    public add(value: T): this {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.add(value);
    }

    public has(value: T): boolean {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.has(value);
    }

    public delete(value: T): boolean {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.delete(value);
    }
}
