// Copyright (c) Microsoft Corporation. All rights reserved.

import { SKContext } from '../orchestration';

/**
 * Class with extension methods for semantic functions.
 */
export class FunctionExtensions {
    /**
     * Extension method to aggregate partitioned results of a semantic function.
     * @param func Semantic Kernel function.
     * @param partitionedInput Input to aggregate.
     * @param context Semantic Kernel context.
     * @returns Aggregated results.
     */
    public static async aggregatePartitionedResults(
        func: ISKFunction,
        partitionedInput: string[],
        context: SKContext
    ): Promise<string[]> {
        const results = [];

        for (const partition of partitionedInput) {
            context.variables.update(partition);
            context = await func.invokeAsync(context);
            results.push(context.variables.toString());
        }

        context.variables.update(results.join('\n'));
        return context;
    }
}
