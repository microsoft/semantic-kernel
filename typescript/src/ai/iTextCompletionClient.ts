/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ICompleteRequestSettings } from './completeRequestSettings';

export interface ITextCompletionClient {
    completeAsync(text: string, requestSettings: ICompleteRequestSettings): Promise<string>;
    dispose?(): void;
}
