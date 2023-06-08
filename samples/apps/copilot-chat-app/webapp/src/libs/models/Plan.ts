export type IPlanInput = {
    // These have to be capitalized to match the server response
    Key: string;
    Value: string;
};

export enum PlanState {
    NoOp = 'NoOp',
    PlanApprovalRequired = 'ApprovalRequired',
    PlanApproved = 'Approved',
    PlanRejected = 'Rejected',
}
