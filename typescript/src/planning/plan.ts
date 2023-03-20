// Copyright (c) Microsoft. All rights reserved.

/**
 * Object that contains details about a plan and its goal and details of its execution.
 */
export class Plan {
    // Internal constant string representing the ID key.
    private readonly idKey: string = 'PLAN__ID';

    // Internal constant string representing the goal key.
    private readonly goalKey: string = 'PLAN__GOAL';

    // Internal constant string representing the plan key.
    private readonly planKey: string = 'PLAN__PLAN';

    // Internal constant string representing the arguments key.
    private readonly argumentsKey: string = 'PLAN__ARGUMENTS';

    // Internal constant string representing the is complete key.
    private readonly isCompleteKey: string = 'PLAN__ISCOMPLETE';

    // Internal constant string representing the is successful key.
    private readonly isSuccessfulKey: string = 'PLAN__ISSUCCESSFUL';

    // Internal constant string representing the result key.
    private readonly resultKey: string = 'PLAN__RESULT';

    // The ID of the plan.
    // Can be used to track creation of a plan and execution over multiple steps.
    public id: string = '';

    // The goal of the plan.
    public goal: string = '';

    // The plan details in string.
    public planString: string = '';

    // The arguments for the plan.
    public arguments: string = '';

    // Flag indicating if the plan is complete.
    public isComplete: boolean = false;

    // Flag indicating if the plan is successful.
    public isSuccessful: boolean = false;

    // The result of the plan execution.
    public result: string = '';

    /**
     * To help with writing plans to ContextVariables.
     *
     * @returns JSON string representation of the Plan.
     */
    public toJson(): string {
        return JSON.stringify(this);
    }

    /**
     * To help with reading plans from ContextVariables.
     *
     * @param json JSON string representation of a Plan.
     * @returns An instance of a Plan object.
     */
    public static fromJson(json: string): Plan {
        return (JSON.parse(json) as Plan) ?? new Plan();
    }
}
