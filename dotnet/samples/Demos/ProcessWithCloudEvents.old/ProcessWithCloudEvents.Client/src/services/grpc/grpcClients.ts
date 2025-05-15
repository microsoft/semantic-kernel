/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { GrpcWebFetchTransport } from "@protobuf-ts/grpcweb-transport";
import { GrpcDocumentationGenerationClient } from "./gen/documentGeneration.client";
import { GrpcTeacherStudentInteractionClient } from "./gen/teacherStudentInteraction.client";

// For this setup, both clients are using the same server URL - just different grpc services.
// In a real-world scenario, you might have different URLs for different services.
// This is just a placeholder URL. You should replace it with the actual URL of your gRPC server.
const SERVER_URL = "http://localhost:58640";

const getGrpcWebTransport = () => {
    return new GrpcWebFetchTransport({
        baseUrl: SERVER_URL,
        format: "text",
    });
};

const createGrpcDocGenerationClient = () => {
    try {
        const transport = getGrpcWebTransport();
        return new GrpcDocumentationGenerationClient(transport);
    } catch (error) {
        console.error(
            "Could not create connection with gRPC server - document generation",
            error
        );
        return undefined;
    }
};

export const grpcDocService = createGrpcDocGenerationClient();

const createGrpcTeacherStundentInteractionClient = () => {
    try {
        const transport = getGrpcWebTransport();
        return new GrpcTeacherStudentInteractionClient(transport);
    } catch (error) {
        console.error(
            "Could not create connection with gRPC server - Teacher Student Interaction",
            error
        );
        return undefined;
    }
};

export const grpcTeacherStudentService =
    createGrpcTeacherStundentInteractionClient();
