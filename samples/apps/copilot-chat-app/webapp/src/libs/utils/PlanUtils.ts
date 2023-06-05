// Copyright (c) Microsoft. All rights reserved.

import { Constants } from '../../Constants';
import { IPlan, IPlanInput } from '../models/Plan';

export const isPlan = (object: string) => {
    // backslash has to be escaped since it's a JSON string
    // eslint-disable-next-line
    const planPrefix = `proposedPlan\":`;
    return object.indexOf(planPrefix) !== -1;
};

export const parsePlan = (response: string): IPlan | null => {
    if (isPlan(response)) {
        try {
            const parsedResponse = JSON.parse(response);
            const plan = parsedResponse.proposedPlan;
            const userIntentPrefix = 'User intent: ';
            const index = plan.description.indexOf(userIntentPrefix);

            return {
                userIntent: plan.description,
                description: index !== -1 ? plan.description.substring(index + userIntentPrefix.length).trim() : '',
                steps: extractPlanSteps(plan),
            };
        } catch (e: any) {
            console.error('Error parsing plan: ' + response);
        }
    }
    return null;
};

const extractPlanSteps = (plan: any) => {
    // If plan came from Actio Planner, extract step parameters from top-level plan state
    const planInputs = extractParameters(plan.state);

    const planSteps = plan.steps;
    return planSteps.map((step: any) => {
        // If plan came from SequentialPlanner, extract step parameters from respective step object
        const stepParameters = extractParameters(step.parameters);

        return {
            skill: step['skill_name'],
            function: step['name'],
            description: step['description'],
            stepInputs: planSteps.length === 1 && planInputs.length > 0 ? planInputs : stepParameters,
        };
    });
};

const extractParameters = (parametersArray: IPlanInput[]) => {
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
