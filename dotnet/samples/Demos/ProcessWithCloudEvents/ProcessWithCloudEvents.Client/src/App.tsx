/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { useState } from "react";
import "./App.css";
import { GrpcDocumentationGenerationClient } from "./services/grpc/gen/documentGeneration.client";
import {
    Button,
    Divider,
    Dropdown,
    makeStyles,
    MessageBar,
    MessageBarActions,
    MessageBarBody,
    MessageBarTitle,
    Option,
    Title1,
} from "@fluentui/react-components";
import {
    AppPages,
    AppPagesDetails,
    CloudTechnologiesDetails,
    CloudTechnology,
} from "./common/AppConstants";
import GenerateDocsChat, {
    DocumentReview,
    NewDocument,
} from "./components/GenerateDocumentsChat";
import { ExitIcon } from "./components/Icons";

interface AppProps {
    grpcDocClient?: GrpcDocumentationGenerationClient;
}

const useStyles = makeStyles({
    root: {
        alignItems: "flex-start",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        rowGap: "20px",
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
    },
    innerContainer: {
        margin: "20px",
        width: "96%",
        height: "100%",
    },
    divider: {
        marginTop: "20px",
        marginBottom: "20px",
    },
    dropdownContainer: {
        display: "grid",
        gridTemplateRows: "repeat(2fr)",
        justifyItems: "start",
        gap: "2px",
        maxWidth: "400px",
    },
    settingsContainer: {
        display: "flex",
        columnGap: "20px",
    },
});

const App: React.FC<AppProps> = ({ grpcDocClient }) => {
    const styles = useStyles();

    const [selectedCloudTech, setSelectedCloudTech] = useState<CloudTechnology>(
        CloudTechnology.GRPC
    );
    const [selectedAppPage, setSelectedAppPage] = useState<AppPages>(
        AppPages.DocumentGeneration
    );
    const [generatedDocuments, setGeneratedDocuments] = useState<NewDocument[]>(
        []
    );
    const [publishedDocuments, setPublishedDocuments] = useState<NewDocument[]>(
        []
    );

    const [hasGrpcError, setHasGrpcError] = useState(false);

    const onCreateDocumentRequest = (
        document: NewDocument
    ): Promise<string> => {
        if (selectedCloudTech == CloudTechnology.GRPC) {
            if (grpcDocClient) {
                return grpcDocClient
                    .userRequestFeatureDocumentation({
                        processId: document.processId,
                        content: document.title ?? "",
                        title: document.title ?? "",
                        userDescription: "",
                    })
                    .then((result) => {
                        setHasGrpcError(false);
                        return result.response.processId;
                    })
                    .catch((error) => {
                        console.error(
                            "[GRPC] Error requesting document generation",
                            error
                        );
                        setHasGrpcError(true);
                        return "";
                    });
            }
        }

        return new Promise((resolve) => resolve(""));
    };

    const onUserReviewedDocument = (
        userReview: DocumentReview
    ): Promise<boolean> => {
        if (selectedCloudTech == CloudTechnology.GRPC) {
            if (grpcDocClient) {
                return grpcDocClient
                    .userReviewedDocumentation({
                        processData: {
                            processId: userReview.processId,
                        },
                        documentationApproved: userReview.accepted,
                        reason: userReview.suggestions,
                    })
                    .then(() => {
                        console.log("[GRPC] User document review submitted");
                        setHasGrpcError(false);
                        return true;
                    })
                    .catch((error) => {
                        console.error(
                            "[GRPC] Error submitting user document review",
                            error
                        );
                        setHasGrpcError(true);
                        return false;
                    });
            }
        }
        return new Promise((resolve) => resolve(false));
    };

    const subscribeReceiveDocumentForReview = async (processId: string) => {
        if (selectedCloudTech == CloudTechnology.GRPC) {
            if (grpcDocClient) {
                // grpc stream for receiving document for review
                const reviewDocumentStream =
                    grpcDocClient.requestUserReviewDocumentation({
                        processId: processId,
                    });
                for await (const message of reviewDocumentStream.responses) {
                    setGeneratedDocuments((prevDocs) => [
                        ...prevDocs,
                        {
                            processId: message.processData!.processId!,
                            content: message.content,
                            title: message.title,
                        },
                    ]);
                    console.log("[GRPC] Review document received: ", message);
                }
            }
        }
    };

    const subscribeToReceivePublishedDocument = async (processId: string) => {
        if (selectedCloudTech == CloudTechnology.GRPC) {
            if (grpcDocClient) {
                // grpc stream for receiving published document
                const publishedDocumentStream =
                    grpcDocClient.receivePublishedDocumentation({
                        processId: processId,
                    });
                for await (const message of publishedDocumentStream.responses) {
                    setPublishedDocuments((prevDocs) => [
                        ...prevDocs,
                        {
                            processId: message.processData!.processId!,
                            content: message.content,
                            title: message.title,
                        },
                    ]);
                    console.log(
                        "[GRPC] Published document received: ",
                        message
                    );
                }
            }
        }
    };

    const subscribeToSpecificProcessId = async (processId: string) => {
        subscribeReceiveDocumentForReview(processId);
        subscribeToReceivePublishedDocument(processId);
        return Promise.all([
            subscribeReceiveDocumentForReview(processId),
            subscribeToReceivePublishedDocument(processId),
        ]).then(() => {
            return;
        });
    };

    return (
        <div className={styles.root}>
            <div className={styles.innerContainer}>
                <Title1>SK Processes with Cloud events</Title1>
                <Divider className={styles.divider} />
                <div className={styles.settingsContainer}>
                    <div className={styles.dropdownContainer}>
                        <label>1. Select cloud technology: </label>
                        <Dropdown
                            onOptionSelect={(
                                _e: any,
                                data: { optionValue: CloudTechnology }
                            ) =>
                                setSelectedCloudTech(
                                    data.optionValue as CloudTechnology
                                )
                            }
                            defaultValue={
                                CloudTechnologiesDetails.get(selectedCloudTech)
                                    ?.name
                            }
                            defaultSelectedOptions={[selectedCloudTech]}
                        >
                            {[...CloudTechnologiesDetails.entries()].map(
                                ([tech, detail]) => (
                                    <Option key={tech} value={tech}>
                                        {detail.name}
                                    </Option>
                                )
                            )}
                        </Dropdown>
                    </div>
                    <div className={styles.dropdownContainer}>
                        <label>2. Select app to use</label>
                        <Dropdown
                            onOptionSelect={(
                                _e: any,
                                data: { optionValue: AppPages }
                            ) =>
                                setSelectedAppPage(data.optionValue as AppPages)
                            }
                            defaultValue={
                                AppPagesDetails.get(selectedAppPage)?.name
                            }
                            defaultSelectedOptions={[selectedAppPage]}
                        >
                            {[...AppPagesDetails.entries()].map(
                                ([app, detail]) => (
                                    <Option key={app} value={app}>
                                        {detail.name}
                                    </Option>
                                )
                            )}
                        </Dropdown>
                    </div>
                </div>
                <Divider className={styles.divider} />
                {hasGrpcError && (
                    <MessageBar intent="warning">
                        <MessageBarActions
                            containerAction={
                                <Button
                                    aria-label="dismiss"
                                    appearance="transparent"
                                    icon={<ExitIcon />}
                                    onClick={() => setHasGrpcError(false)}
                                />
                            }
                        />
                        <MessageBarBody>
                            <MessageBarTitle>gRPC Client Error</MessageBarTitle>
                            Cannot connect to gRPC Document Generator server,
                            make sure server is running and try again.
                        </MessageBarBody>
                    </MessageBar>
                )}
                {selectedAppPage == AppPages.DocumentGeneration && (
                    <GenerateDocsChat
                        cloudTechnologyName={
                            CloudTechnologiesDetails.get(selectedCloudTech)!
                                .name
                        }
                        onCreateNewDocument={onCreateDocumentRequest}
                        onUserReviewedDocument={onUserReviewedDocument}
                        subscribeToSpecificProcessId={
                            subscribeToSpecificProcessId
                        }
                        generatedDocuments={generatedDocuments}
                        publishedDocuments={publishedDocuments}
                    />
                )}
            </div>
        </div>
    );
};

export default App;
