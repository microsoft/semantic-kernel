export interface FeatureDocumentationRequest {
    title: string;
    userDescription: string;
    content: string;
    processId: string;
}

export interface DocumentationContentRequest {
    title: string;
    content: string;
    assistantMessage: string;
    processData?: ProcessData;
}

export interface DocumentationApprovalRequest {
    documentationApproved: boolean;
    reason: string;
    processData?: ProcessData;
}

export interface ProcessData {
    processId: string;
}