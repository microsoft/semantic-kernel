/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export interface ILogger {
    trace(msg: string): void;
    debug(msg: string): void;
    warn(msg: string): void;
    error(msg: string): void;
}

export class NullLogger implements ILogger {
    trace(msg: string): void {
        // No action
    }

    debug(msg: string): void {
        // No action
    }

    warn(msg: string): void {
        // No action
        console;
    }

    error(msg: string): void {
        // No action
    }
}
