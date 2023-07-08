// Copyright (c) Microsoft. All rights reserved.

export const isPlan = (object: string) => {
    // backslash has to be escaped since it's a JSON string
    // eslint-disable-next-line
    const planPrefix = `proposedPlan\":`;
    return object.includes(planPrefix);
};
