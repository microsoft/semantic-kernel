/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../utils/logger';

/**
 * Interface for retry mechanisms on AI calls.
 */
export interface IRetryMechanism {
    /**
     * Executes the given action with retry logic.
     * @param action The action to retry on exception.
     * @param log The logger to use.
     * @returns An awaitable task.
     */
    executeWithRetryAsync(action: () => Promise<void>, log: ILogger): Promise<void>;
}
