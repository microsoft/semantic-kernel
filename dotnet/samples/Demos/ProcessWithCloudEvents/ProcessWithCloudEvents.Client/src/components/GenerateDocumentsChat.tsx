/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import {
    Button,
    Card,
    CardHeader,
    Input,
    Label,
    makeStyles,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Spinner,
    Title2,
    useId,
} from "@fluentui/react-components";
import Markdown from "react-markdown";
import { ChatMessageContent, ChatUser } from "../common/ChatConstants";
import SimpleChat from "./SimpleChat";
import { CheckIcon, RejectIcon } from "./Icons";

export interface NewDocument {
    title?: string;
    processId: string;
    content?: string;
}

export interface DocumentReview {
    accepted: boolean;
    processId: string;
    suggestions: string;
}

interface GenerateDocsChatProps {
    cloudTechnologyName: string;
    generatedDocuments: NewDocument[];
    publishedDocuments: NewDocument[];
    onCreateNewDocument: (document: NewDocument) => Promise<string>;
    onUserReviewedDocument: (userReview: DocumentReview) => Promise<boolean>;
    subscribeToSpecificProcessId: (processId: string) => Promise<void>;
}

const useStyles = makeStyles({
    root: {
        display: "flex",
        flexDirection: "column",
        rowGap: "8px",
        width: "90%",
    },
    processIdContainer: {
        display: "flex",
        flexDirection: "column",
        rowGap: "8px",
        alignItems: "flex-end",
    },
    buttonsFamily: {
        display: "flex",
        columnGap: "40px",
    },
    suggestionsContainer: {
        display: "flex",
        flexDirection: "column",
        rowGap: "8px",
    },
    newDocHeaderHeader: {
        marginTop: "0",
    },
    headerContainer: {
        display: "flex",
        justifyContent: "space-between",
    },
});

const GenerateDocsChat: React.FC<GenerateDocsChatProps> = ({
    cloudTechnologyName,
    generatedDocuments,
    publishedDocuments,
    onCreateNewDocument,
    onUserReviewedDocument,
    subscribeToSpecificProcessId,
}) => {
    const styles = useStyles();
    const newDocNameId = useId("input");
    const docRejectedId = useId("input");

    const [messages, setMessages] = useState<ChatMessageContent[]>([]);
    const [processId, setProcessId] = useState<string>();
    const [newDocContent, setNewDocContent] = useState<string>();
    const [rejectSuggestions, setRejectSuggestions] = useState<string>();
    const [creatingNewDocument, setCreatingNewDocument] =
        useState<boolean>(false);
    const [allowUserReview, setAllowUserReview] = useState<boolean>(false);

    useEffect(() => {
        if (processId) {
            subscribeToSpecificProcessId(processId);
        }
    }, [processId]);

    const formatNewDocumentString = (doc: NewDocument, header: string) => {
        const content = `### Title: ${doc.title}\n### Content:\n${doc.content}`;

        return (
            <Card>
                <CardHeader header={<Title2 weight="semibold">{header}</Title2>} />
                <Markdown>{content}</Markdown>
            </Card>
        );
    };

    useEffect(() => {
        if (generatedDocuments.length > 0) {
            const lastDoc = generatedDocuments[generatedDocuments.length - 1];
            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    sender: ChatUser.ASSISTANT,
                    content: formatNewDocumentString(
                        lastDoc,
                        "Document for review"
                    ),
                    timestamp: new Date().toLocaleString(),
                },
            ]);
            setAllowUserReview(true);
        }
    }, [generatedDocuments]);

    useEffect(() => {
        if (publishedDocuments.length > 0) {
            const lastDoc = publishedDocuments[publishedDocuments.length - 1];
            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    sender: ChatUser.ASSISTANT,
                    content: formatNewDocumentString(
                        lastDoc,
                        "Published document"
                    ),
                    timestamp: new Date().toLocaleString(),
                },
            ]);
            setAllowUserReview(false);
        }
    }, [publishedDocuments]);

    const onCreateNewDocumentClicked = () => {
        if (newDocContent === "") {
            alert("Document title cannot be empty");
            return;
        }

        // Need to know processId to be able to subscribe to incoming events from this process once it is running
        // processId is used as identifier to start/resume process
        const newProcessId = uuidv4();
        setProcessId(newProcessId);
        setAllowUserReview(false);

        onCreateNewDocument({
            processId: newProcessId,
            title: newDocContent ?? "",
        })
            .then((result) => {
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {
                        sender: ChatUser.ASSISTANT,
                        action: `Document generated - ${result}`,
                    },
                ]);
            })
            .finally(() => {
                setCreatingNewDocument(false);
            });
        setMessages((prevMessages) => [
            ...prevMessages,
            {
                sender: ChatUser.USER,
                content: `User created new document request - ${newDocContent}`,
                timestamp: new Date().toLocaleString(),
            },
        ]);
        setCreatingNewDocument(true);
    };

    const onClearChat = () => {
        setMessages([]);
        setProcessId("");
        setRejectSuggestions("");
        setAllowUserReview(false);
    };

    const onUserRejectedDocument = () => {
        if (!processId) {
            alert("Process id cannot be empty, create document first");
            return;
        }

        if (!rejectSuggestions) {
            alert(
                "Must provide non empty suggestions on rejection of a document"
            );
            return;
        }

        onUserReviewedDocument({
            accepted: false,
            suggestions: rejectSuggestions ?? "",
            processId: processId!,
        }).then(() => {
            setMessages((prevMessages) => [
                ...prevMessages,

                {
                    sender: ChatUser.ASSISTANT,
                    action: "Document generated with suggestions",
                },
            ]);
        });

        setMessages((prevMessages) => [
            ...prevMessages,
            {
                sender: ChatUser.USER,
                content: `User rejected document providing suggestions: ${rejectSuggestions}`,
                timestamp: new Date().toLocaleString(),
            },
            { sender: ChatUser.ASSISTANT, action: "Document rejected" },
        ]);
        setRejectSuggestions("");
    };

    const onUserApprovedDocument = () => {
        if (!processId) {
            alert("Process id cannot be empty, create document first");
            return;
        }

        onUserReviewedDocument({
            accepted: true,
            suggestions: "",
            processId: processId!,
        }).then(() => {
            setMessages((prevMessages) => [
                ...prevMessages,
                { sender: ChatUser.ASSISTANT, action: "Document Approved" },
            ]);
        });

        setMessages((prevMessages) => [
            ...prevMessages,
            {
                sender: ChatUser.USER,
                content: "User send approval of document",
                timestamp: new Date().toLocaleString(),
            },
        ]);
        setRejectSuggestions("");
    };

    return (
        <div className={styles.root}>
            <div className={styles.headerContainer}>
                <Title2>Document Generation with {cloudTechnologyName}</Title2>
                <div className={styles.processIdContainer}>
                    <Label>ProcessId : </Label>
                    <Label>{processId ?? "-"}</Label>
                </div>
            </div>
            <SimpleChat messages={messages} />
            <div className={styles.buttonsFamily}>
                <Popover withArrow>
                    <PopoverTrigger>
                        <Button
                            appearance="primary"
                            icon={
                                creatingNewDocument ? (
                                    <Spinner size="tiny" />
                                ) : undefined
                            }
                        >
                            Create new document
                        </Button>
                    </PopoverTrigger>
                    <PopoverSurface>
                        <div>
                            <h3 className={styles.newDocHeaderHeader}>
                                New Document
                            </h3>
                            <Label htmlFor={newDocNameId}>Title/Name: </Label>
                            <Input
                                required
                                id={newDocNameId}
                                onChange={(_e, d) => setNewDocContent(d.value)}
                            />
                            <Button onClick={onCreateNewDocumentClicked}>
                                Create
                            </Button>
                        </div>
                    </PopoverSurface>
                </Popover>

                <div>
                    <Button
                        icon={<CheckIcon />}
                        onClick={onUserApprovedDocument}
                        disabled={!allowUserReview}
                    >
                        Accept Document
                    </Button>
                    <Popover withArrow>
                        <PopoverTrigger>
                            <Button
                                icon={<RejectIcon />}
                                disabled={!allowUserReview}
                            >
                                Reject Document
                            </Button>
                        </PopoverTrigger>
                        <PopoverSurface>
                            <div className={styles.suggestionsContainer}>
                                <h3 className={styles.newDocHeaderHeader}>
                                    Document Rejected - add suggestions
                                </h3>
                                <div>
                                    <Label htmlFor={docRejectedId}>
                                        Suggestions:{" "}
                                    </Label>
                                    <Input
                                        onChange={(_e, d) =>
                                            setRejectSuggestions(d.value)
                                        }
                                        required
                                        id={docRejectedId}
                                    />
                                </div>
                                <Button onClick={onUserRejectedDocument}>
                                    Send suggestions
                                </Button>
                            </div>
                        </PopoverSurface>
                    </Popover>
                </div>
                <Button appearance="subtle" onClick={onClearChat}>
                    Clear chat
                </Button>
            </div>
        </div>
    );
};

export default GenerateDocsChat;
