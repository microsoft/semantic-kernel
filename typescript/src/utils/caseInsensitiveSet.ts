/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export class CaseInsensitiveSet<T> extends Set<T> {
    public override add(value: T): this {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.add(value);
    }

    public override has(value: T): boolean {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.has(value);
    }

    public override delete(value: T): boolean {
        if (typeof value === 'string') {
            value = value.toLowerCase() as any as T;
        }

        return super.delete(value);
    }
}
