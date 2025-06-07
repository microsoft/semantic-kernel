/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { useState } from "react";
import "./App.css";
import { SignalRDocumentationGenerationClient } from "./services/signalr/documentGeneration.client";
import { ProcessFrameworkHttpClient } from "./services/signalr/ProcessFrameworkClient";
import {
    Divider,
    Title1,
    makeStyles,
} from "@fluentui/react-components";
import { CloudTechnologiesDetails, CloudTechnology } from './common/AppConstants';
import GenerateDocsChat, {
    DocumentReview,
    NewDocument,
} from "./components/GenerateDocumentsChat";

interface AppProps {
    signalRClient: SignalRDocumentationGenerationClient;
    httpClient: ProcessFrameworkHttpClient;
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
    settingsContainer: {
        display: "flex",
        columnGap: "20px",
    },
});

const App: React.FC<AppProps> = ({ signalRClient, httpClient }) => {
    const styles = useStyles();

    const [generatedDocuments, setGeneratedDocuments] = useState<NewDocument[]>(
        []
    );
    const [publishedDocuments, setPublishedDocuments] = useState<NewDocument[]>(
        []
    );

    const onCreateDocumentRequest = async (
        document: NewDocument
    ): Promise<string> => {
        try {
            await httpClient.generateDocumentation({
                processId: document.processId,
                content: document.title ?? "",
                title: document.title ?? "",
                assistantMessage: "",
            });
            return document.processId;
        } catch (error) {
            console.error("[HTTP] Error creating document request", error);
            return "";
        }
    };

    const onUserReviewedDocument = async (
        userReview: DocumentReview
    ): Promise<boolean> => {
        try {
            await httpClient.requestDocumentationReview({
                processId: userReview.processId,
                documentationApproved: userReview.accepted,
                reason: userReview.suggestions,
            });
            return true;
        } catch (error) {
            console.error("[HTTP] Error submitting user review", error);
            return false;
        }
    };

    const subscribeToSpecificProcessId = async (processId: string): Promise<void> => {
        signalRClient.subscribeToProcessEvents(processId, {
            onPublishedDocument: (message) => {
                setPublishedDocuments((prevDocs) => [
                    ...prevDocs,
                    {
                        processId: message.processData?.processId ?? "",
                        content: message.content,
                        title: message.title,
                    },
                ]);
                console.log("[SignalR] Published document received: ", message);
            },
            onDocumentForReview: (message) => {
                setGeneratedDocuments((prevDocs) => [
                    ...prevDocs,
                    {
                        processId: message.processData?.processId ?? "",
                        content: message.content,
                        title: message.title,
                    },
                ]);
                console.log("[SignalR] Document for review received: ", message);
            },
        });
    };

    return (
        <div className={styles.root}>
            <div className={styles.innerContainer}>
                <Title1>SK Processes with Cloud events</Title1>
                <Divider className={styles.divider} />
                <div className={styles.settingsContainer}></div>
                <Divider className={styles.divider} />
                <GenerateDocsChat
                    cloudTechnologyName={
                        CloudTechnologiesDetails.get(CloudTechnology.SIGNALR)!.name
                    }
                    onCreateNewDocument={onCreateDocumentRequest}
                    onUserReviewedDocument={onUserReviewedDocument}
                    subscribeToSpecificProcessId={subscribeToSpecificProcessId}
                    generatedDocuments={generatedDocuments}
                    publishedDocuments={publishedDocuments}
                />
            </div>
        </div>
    );
};

export default App;
