/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ParameterView } from './parameterView';

export interface IFunctionView {
    /**
     * Name of the function. The name is used by the registry and in prompt templates e.g. {{skillName.functionName}}
     */
    name: string;

    /**
     * Name of the skill containing the function. The name is used by the registry and in prompt templates e.g. {{skillName.functionName}}
     */
    skillName: string;

    /**
     * Function description. The description is used in combination with embeddings when searching relevant functions.
     */
    description: string;

    /**
     * Whether the delegate points to a semantic function
     */
    isSemantic: boolean;

    /**
     * Whether the delegate is an asynchronous function
     */
    isAsync: boolean;

    /**
     * List of function parameters
     */
    parameters: ParameterView[];
}

/**
 * Class used to copy and export data from the registry.
 * @remarks
 * The data is mutable, but changes do not affect the registry.
 */
export class FunctionView {
    /**
     * Create a function view.
     * @param name Function name
     * @param skillName Skill name, e.g. the function namespace
     * @param description Function description
     * @param parameters List of function parameters provided by the skill developer
     * @param isSemantic Whether the function is a semantic one (or native is False)
     * @param isAsync Whether the function is async. Note: all semantic functions are async.
     */
    public static create(
        name: string = '',
        skillName: string = '',
        description: string = '',
        parameters: ParameterView[] = [],
        isSemantic: boolean = false,
        isAsync: boolean = true
    ): IFunctionView {
        return {
            name,
            skillName,
            description,
            parameters,
            isSemantic,
            isAsync,
        };
    }
}
