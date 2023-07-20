export interface IPlanInput {
    // These have to be capitalized to match the server response
    Key: string;
    Value: string;
}

export enum PlanState {
    NoOp,
    PlanApproved,
    PlanRejected,
    PlanApprovalRequired,
    Disabled,
}

export enum PlanType {
    Action, // single-step
    Sequential, // multi-step
}
