import { IPlan, IPlanInput } from '../models/Plan';

export const isPlan = (object: string) => {
    // backslash has to be escaped since it's a JSON string
    // eslint-disable-next-line
    const planPrefix = `proposedPlan\":`;
    return object.indexOf(planPrefix) !== -1;
};

export const parsePlan = (response: string): IPlan | null => {
    if (isPlan(response)) {
        const parsedResponse = JSON.parse(response);
        const plan = parsedResponse.proposedPlan;
        const userIntentPrefix = 'User intent: ';
        const index = plan.description.indexOf(userIntentPrefix);

        return {
            userIntent: plan.description,
            description: index !== -1 ? plan.description.substring(index + userIntentPrefix.length).trim() : '',
            steps: extractPlanSteps(plan),
        };
    }
    return null;
};

const extractPlanSteps = (plan: any) => {
    const planInputs: IPlanInput[] = [];
    for (var input in plan.state) {
        if (
            // Omit reserved context variable names
            plan.state[input].Key !== 'INPUT' &&
            plan.state[input].Key !== 'server_url' &&
            plan.state[input].Key !== 'server-url'
        ) {
            planInputs.push(plan.state[input]);
        }
    }

    const planSteps = plan.steps;
    return planSteps.map((step: any) => {
        return {
            skill: step['skill_name'],
            function: step['name'],
            description: step['description'],
            stepInputs: planInputs,
        };
    });
};
