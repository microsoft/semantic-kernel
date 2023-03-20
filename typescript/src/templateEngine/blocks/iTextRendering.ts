// Copyright (c) Microsoft. All rights reserved.

import { ContextVariables } from '../../orchestration/contextVariables';

/**
 * Interface of static blocks that don't need async IO to be rendered.
 */
export interface ITextRendering {
    /**
     * Render the block using only the given variables.
     *
     * @param variables Optional variables used to render the block.
     * @returns Rendered content.
     */
    render(variables?: ContextVariables): string;
}
