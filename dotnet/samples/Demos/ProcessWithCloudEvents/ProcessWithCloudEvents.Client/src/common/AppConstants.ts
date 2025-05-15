/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */

// When more process samples are added, add them to this enum and the AppPagesDetails map below.
// Additionally update the AppPagesDetails map to include the new process sample and its details.
export enum AppPages {
    DocumentGeneration = "DocumentGeneration",
}

interface EnumDetails {
    name: string;
    description: string;
}

export const AppPagesDetails = new Map<AppPages, EnumDetails>([
    [
        AppPages.DocumentGeneration,
        {
            name: "Document Generation",
            description:
                "Demo used to show case document generation using different cloud technologies with SK Processes",
        },
    ],
]);

// When more cloud technologies are added, add them to this enum and the CloudTechnologiesDetails map below.
// Additionally update the CloudTechnologiesDetails map to include the new technology and its details.
export enum CloudTechnology {
    GRPC = "GRPC",
}

export const CloudTechnologiesDetails = new Map<CloudTechnology, EnumDetails>(
    [
        [CloudTechnology.GRPC, {name: "gRPC", description: "gRPC Protocol"}]
    ]
);

