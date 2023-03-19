// Copyright (c) Microsoft Corporation. All rights reserved.

import { SKContext } from '../orchestration';
import { ParameterView } from '../registry';

/**
 * Interface for prompt template.
 */
export interface IPromptTemplate {
    /**
     * Get the list of parameters required by the template, using configuration and template info.
     * @returns List of parameters
     */
    getParameters(): ParameterView[];

    /**
     * Render the template using the information in the context.
     * @param executionContext Kernel execution context helpers
     * @returns Prompt rendered to string
     */
    render(executionContext: SKContext): Promise<string>;
}
