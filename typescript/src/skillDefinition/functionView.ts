// Copyright (c) Microsoft Corporation. All rights reserved.

import { ParameterView } from './parameterView';

export interface IFunctionView {
    // Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    name: string;
    // Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    skillName: string;
    // Function description. The description is used in combination with embeddings when searching relevant functions.
    description: string;
    // Whether the delegate points to a semantic function
    isSemantic: boolean;
    // Whether the delegate is an asynchronous function
    isAsynchronous: boolean;
    // List of function parameters
    parameters: ParameterView[];
}

/**
 * Class used to copy and export data from the skill collection.
 * The data is mutable, but changes do not affect the skill collection.
 */
export class FunctionView implements IFunctionView {
    // Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    public name: string;
    // Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    public skillName: string;
    // Function description. The description is used in combination with embeddings when searching relevant functions.
    public description: string;
    // Whether the delegate points to a semantic function
    public isSemantic: boolean;
    // Whether the delegate is an asynchronous function
    public isAsynchronous: boolean;
    // List of function parameters
    public parameters: ParameterView[];

    /**
     * Create a function view.
     * @param name Function name.
     * @param skillName Skill name, e.g. the function namespace.
     * @param description Function description.
     * @param parameters List of function parameters provided by the skill developer.
     * @param isSemantic Whether the function is a semantic one (or native is False).
     * @param IsAsynchronous Whether the function is async. Note: all semantic functions are async.
     */
    public constructor(
        name: string = '',
        skillName: string = '',
        description: string = '',
        parameters: ParameterView[] = [],
        isSemantic: boolean,
        isAsynchronous: boolean = true
    ) {
        this.name = name;
        this.skillName = skillName;
        this.description = description;
        this.parameters = parameters;
        this.isSemantic = isSemantic;
        this.isAsynchronous = isAsynchronous;
    }
}
