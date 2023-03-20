/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../utils/logger';
import { IRetryMechanism } from './iRetryMechanism';

/**
 * A retry mechanism that does not retry.
 */
export class PassThroughWithoutRetry implements IRetryMechanism {
    public async executeWithRetryAsync(action: () => Promise<void>, log: ILogger): Promise<void> {
        try {
            await action();
        } catch (err: any) {
            log.warn(`Error executing action, not retrying: ${(err as Error).toString()}`);
            throw err;
        }
    }
}
