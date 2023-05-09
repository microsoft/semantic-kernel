export type IPlanInput = {
    // These have to be capitalized to match the server response
    Key: string;
    Value: string;
};

export type IPlanStep = {
    skill: string;
    function: string;
    description: string;
    stepInputs: IPlanInput[];
};

export type IPlan = {
    userIntent: string;
    description: string;
    steps: IPlanStep[];
};
