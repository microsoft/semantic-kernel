export type IPlanInput = {
    // These have to be capitalized to match the server response
    Key: string;
    Value: string;
};

export type IPlan = {
    userIntent: string;
    skill: string;
    function: string;
    description: string;
    steps: IPlan[];
    stepInputs: IPlanInput[];
    stepOutputs: string[];
};
