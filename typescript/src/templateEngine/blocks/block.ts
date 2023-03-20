// Copyright (c) Microsoft. All rights reserved.

import { ILogger, NullLogger } from '../../utils/logger';

/**
 * Base class for blocks parsed from a prompt template.
 */
export abstract class Block {
    // The block content.
    private readonly _content: string;

    // Application logger.
    protected readonly log: ILogger;

    /**
     * Base constructor.
     *
     * @constructor
     * @param content Block content.
     * @param log Application logger.
     */
    protected constructor(content?: string, log?: ILogger) {
        this.log = log ?? new NullLogger();
        this._content = content ?? '';
    }

    /**
     * Check if the block content is valid.
     *
     * @returns True if the block content is valid.
     */
    public abstract isValid(): boolean;
}
