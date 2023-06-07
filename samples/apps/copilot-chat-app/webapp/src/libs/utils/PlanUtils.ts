// Copyright (c) Microsoft. All rights reserved.

import { Constants } from '../../Constants';
import { IPlan, IPlanInput } from '../models/Plan';

export const isPlan = (object: string) => {
    // backslash has to be escaped since it's a JSON string
    // eslint-disable-next-line
    const planPrefix = `proposedPlan\":`;
    return object.indexOf(planPrefix) !== -1;
};

export const getPlanView = (response: string): IPlan | null => {
    if (isPlan(response)) {
        try {
            const parsedResponse = JSON.parse(response);
            const plan = parsedResponse.proposedPlan;
            const planType = parsedResponse.Type;
            const userIntentPrefix = 'User Intent:User intent: ';
            const index = plan.description.indexOf(userIntentPrefix);
            const stateParameters = extractInputs(plan.state);

            return {
                userIntent: plan.description,
                description: index !== -1 ? plan.description.substring(index + userIntentPrefix.length).trim() : '',
                skill: plan.skill_name.replace('Microsoft.SemanticKernel.Planning.Plan', ''),
                function: plan.name.replace('Microsoft.SemanticKernel.Planning.Plan', ''),
                stepInputs: stateParameters,
                stepOutputs: plan.outputs,
                steps: extractPlanSteps(plan, stateParameters, planType),
            };
        } catch (e: any) {
            console.error('Error parsing plan: ' + response);
        }
    }
    return null;
};

const extractPlanSteps = (plan: any, stateParameters: IPlanInput[], planType: string) => {
    const planSteps = plan.steps;
    return planSteps.map((step: any) => {
        return {
            skill: step['skill_name'],
            function: step['name'],
            description: step['description'],
            // If plan came from ActionPlanner, use parameters from top-level plan state
            // If plan came from SequentialPlanner, extract step parameters from respective step object
            stepInputs: planType === 'Action' ? stateParameters : extractInputs(step.parameters),
            stepOutputs: step.outputs,
            steps: extractPlanSteps(step, stateParameters, planType),
        };
    });
};

const extractInputs = (parametersArray: IPlanInput[]) => {
    const parameters: IPlanInput[] = [];
    for (var param in parametersArray) {
        if (
            // Omit reserved context variable names
            !Constants.sk.reservedWords.includes(parametersArray[param].Key.trim()) &&
            parametersArray[param].Value.trim() !== ''
        ) {
            parameters.push(parametersArray[param]);
        }
    }

    return parameters;
};
