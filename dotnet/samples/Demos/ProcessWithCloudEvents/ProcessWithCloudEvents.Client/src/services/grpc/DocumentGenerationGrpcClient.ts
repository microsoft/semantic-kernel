/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { GrpcWebFetchTransport } from "@protobuf-ts/grpcweb-transport";
import { GrpcDocumentationGenerationClient } from "./gen/documentGeneration.client";

const createGrpcDocGenerationClient = () => {
    try {
        const transport = new GrpcWebFetchTransport({
            baseUrl: "http://localhost:58640",
            format: "text",
        });
        return new GrpcDocumentationGenerationClient(transport);
    } catch (error) {
        console.error("Could not create connection with gRPC server", error);
        return undefined;
    }
};

export const grpcDocService = createGrpcDocGenerationClient();
