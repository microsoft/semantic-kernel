import { IAsk, IAskInput } from '../model/Ask';
import { IKeyConfig } from '../model/KeyConfig';
import { SemanticKernel } from './SemanticKernel';

export interface IPlanCreated {
    onPlanCreated: (ask: IAsk, plan: string) => void;
}

export class TaskRunner {
    // eslint-disable-next-line @typescript-eslint/space-before-function-paren
    constructor(
        private readonly sk: SemanticKernel,
        private readonly keyConfig: IKeyConfig,
        private readonly maxSteps: number = 10,
    ) {}

    runTask = async (
        taskDescription: string,
        taskResponseFormat?: string,
        skills?: string[],
        onPlanCreated?: (ask: IAsk, plan: string) => void,
        onTaskCompleted?: (ask: IAsk, result: string) => void,
    ) => {
        var createPlanRequest = taskDescription;

        if (taskResponseFormat !== undefined) {
            createPlanRequest = `${createPlanRequest} MUST RETURN A SINGLE RESULT IN THIS FORMAT: ${taskResponseFormat}`;
        }

        var createPlanAsk = {
            value: createPlanRequest,
            skills: skills,
        };

        var createPlanResult = await this.sk.createPlanAsync(this.keyConfig, createPlanAsk);

        onPlanCreated?.(createPlanAsk, createPlanResult.value);

        var inputs: IAskInput[] = [...createPlanResult.state];
        var executePlanAsk = {
            inputs: inputs,
            value: createPlanResult.value,
            skills: skills,
        };

        var executePlanResult = await this.sk.executePlanAsync(this.keyConfig, executePlanAsk, this.maxSteps); //the maximum number of steps that the planner will attempt while the problem remains unsolved

        onTaskCompleted?.(executePlanAsk, executePlanResult.value);
    };
}
