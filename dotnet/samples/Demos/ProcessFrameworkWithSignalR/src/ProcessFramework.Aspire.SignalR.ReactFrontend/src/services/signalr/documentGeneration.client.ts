import * as signalR from "@microsoft/signalr";
import {
    DocumentationApprovalRequest,
    DocumentationContentRequest,
    FeatureDocumentationRequest,
} from "../signalr/documentGeneration";

export class SignalRDocumentationGenerationClient {
    private connection: signalR.HubConnection;

    constructor() {
        this.connection = new signalR.HubConnectionBuilder()
            .withUrl("http://localhost:5125/pfevents") // Replace with your SignalR hub URL
            .withAutomaticReconnect()
            .configureLogging(signalR.LogLevel.Information)
            .build();

        this.connection.on("RequestUserReview", (message: any) => {
            console.log("Received message from SignalR:", message);
            // Handle the received message here
        });

        this.connection.on("PublishDocumentation", (message: any) => {
            console.log("Received message from SignalR:", message);
            // Handle the received message here
        });

        this.connection.start()
            .then(() => console.log("SignalR connection established"))
            .catch((error) => console.error("Could not establish SignalR connection", error));
    }

    async userRequestFeatureDocumentation(input: FeatureDocumentationRequest): Promise<any> {
        return this.connection.invoke("UserRequestFeatureDocumentation", input);
    }

    async requestUserReviewDocumentationFromProcess(input: DocumentationContentRequest): Promise<void> {
        return this.connection.invoke("RequestUserReviewDocumentationFromProcess", input);
    }

    async userReviewedDocumentation(input: DocumentationApprovalRequest): Promise<void> {
        return this.connection.invoke("UserReviewedDocumentation", input);
    }

    async publishDocumentation(input: DocumentationContentRequest): Promise<void> {
        return this.connection.invoke("PublishDocumentation", input);
    }

    subscribeToProcessEvents(_processId: string, handlers: {
        onPublishedDocument: (message: any) => void;
        onDocumentForReview: (message: any) => void;
    }): void {
        this.connection.on("PublishDocumentation", handlers.onPublishedDocument);
        this.connection.on("RequestUserReview", handlers.onDocumentForReview);
    }
}