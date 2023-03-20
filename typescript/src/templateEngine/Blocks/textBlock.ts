/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../../utils/logger';
import { ContextVariables } from '../../orchestration';
import { Block, BlockTypes } from './block';

/**
 * @private
 */
export class TextBlock extends Block {
    constructor(content: string, log?: ILogger);
    constructor(text: string, startIndex: number, stopIndex: number, log: ILogger);
    constructor(textOrContent: string, startIndexOrLog: number | ILogger, stopIndex?: number, log?: ILogger) {
        super(typeof startIndexOrLog == 'object' ? startIndexOrLog : log);
        if (typeof startIndexOrLog == 'number') {
            this.content = textOrContent.substring(startIndexOrLog, stopIndex - startIndexOrLog);
        } else {
            this.content = textOrContent;
        }
    }

    public get type(): BlockTypes {
        return BlockTypes.Text;
    }

    public isValid(): { valid: boolean; error: string } {
        return {
            valid: true,
            error: '',
        };
    }

    public render(variables?: ContextVariables): string {
        return this.content;
    }
}
