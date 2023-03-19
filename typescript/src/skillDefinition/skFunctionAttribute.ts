// Copyright (c) Microsoft Corporation. All rights reserved.

/**
 * Attribute required to register native functions into the kernel.
 * The registration is required by the prompt templating engine and by the pipeline generator (aka planner).
 * The quality of the description affects the planner ability to reason about complex tasks.
 * The description is used both with LLM prompts and embedding comparisons.
 */
export class SKFunctionAttribute {
    // Function description, to be used by the planner to auto-discover functions.
    public readonly description: string;

    /**
     * Tag a C# function as a native function available to SK.
     * @param description Function description, to be used by the planner to auto-discover functions.
     */
    public constructor(description: string) {
        this.description = description;
    }
}
