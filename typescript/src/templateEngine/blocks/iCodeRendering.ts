// Copyright (c) Microsoft. All rights reserved.

import { SKContext } from '../../orchestration';

/**
 * Interface of dynamic blocks that need async IO to be rendered.
 */
export interface ICodeRendering {
    /**
     * Render the block using the given context, potentially using external I/O.
     *
     * @param context SK execution context.
     * @returns Rendered content.
     */
    renderCode(context: SKContext): Promise<string>;
}
