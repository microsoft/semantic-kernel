// Copyright (c) Microsoft. All rights reserved.

export interface ILogger {
    trace(msg: string): void;
    debug(msg: string): void;
    warn(msg: string): void;
    error(msg: string): void;
}

export class NullLogger implements ILogger {
    public trace(_msg: string): void {
        // NoOp
    }

    public debug(_msg: string): void {
        // NoOp
    }

    public warn(_msg: string): void {
        // NoOp
    }

    public error(_msg: string): void {
        // NoOp
    }
}
