/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import {
    Button,
    Dropdown,
    makeStyles,
    Option,
    Spinner,
} from "@fluentui/react-components";
import { ChatMessageContent, ChatUser } from "../common/ChatConstants";
import SimpleChat from "./SimpleChat";
import ChatHeader from "./ChatHeader";

export enum TeacherStudentInteractionUser {
    TEACHER = "TEACHER",
    STUDENT = "STUDENT",
}

export interface StudentTeacherEntry {
    processId: string;
    content?: string;
    user: TeacherStudentInteractionUser;
}

interface TeacherStudentInteractionChatProps {
    cloudTechnologyName: string;
    newStudentAgentResponses: StudentTeacherEntry[];
    onStartNewProcess?: (processId: string) => Promise<boolean>;
    onSendTeacherQuestion?: (
        teacherInteraction: StudentTeacherEntry
    ) => Promise<boolean>;
    subscribeToSpecificProcessId?: (processId: string) => Promise<void>;
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
    headerContainer: {
        display: "flex",
        justifyContent: "space-between",
    },
});

const teacherMathQuestions = [
    "What is 2 + 2?",
    "Can you explain the Pythagorean theorem?",
    "What is the integral of sin(x)?",
    "What is the area of a circle?",
];

const TeacherStudentInteractionChat: React.FC<
    TeacherStudentInteractionChatProps
> = ({
    cloudTechnologyName,
    newStudentAgentResponses,
    onStartNewProcess,
    onSendTeacherQuestion,
    subscribeToSpecificProcessId
}) => {
    const styles = useStyles();

    const [messages, setMessages] = useState<ChatMessageContent[]>([]);
    const [processId, setProcessId] = useState<string>();
    const [startingNewProcess, setStartingNewProcess] =
        useState<boolean>(false);
    const [selectedTeacherQuestion, setSelectedTeacherQuestion] =
        useState<string>();

    useEffect(() => {
        if (processId) {
            subscribeToSpecificProcessId?.(processId);
        }
    }, [processId]);

    useEffect(() => {
        if (processId) {
            // subscribeToSpecificProcessId(processId);
        }
    }, [processId]);

    const formatStudentResponseString = (response: string) => {
        return `Student Agent: ${response}`;
    };

    useEffect(() => {
        if (newStudentAgentResponses.length > 0) {
            const lastResponse =
                newStudentAgentResponses[newStudentAgentResponses.length - 1];
            if (lastResponse.processId !== processId) {
                console.warn(
                    `Received response for a different processId - ignoring ${lastResponse}`
                );
                return;
            }

            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    sender: ChatUser.ASSISTANT,
                    content: formatStudentResponseString(
                        lastResponse.content ?? ""
                    ),
                    timestamp: new Date().toLocaleString(),
                },
            ]);
        }
    }, [newStudentAgentResponses]);

    const OnStartNewProcessClicked = () => {
        // Need to know processId to be able to subscribe to incoming events from this process once it is running
        // processId is used as identifier to start/resume process
        const newProcessId = uuidv4();
        setProcessId(newProcessId);

        onStartNewProcess?.(newProcessId)
            .then((result) => {
                if (result) {
                    setMessages((prevMessages) => [...prevMessages]);
                }
            })
            .finally(() => {
                setStartingNewProcess(false);
            });

        setMessages((prevMessages) => [
            ...prevMessages,
            {
                sender: ChatUser.USER,
                action: `New process started - ${newProcessId}`,
                timestamp: new Date().toLocaleString(),
            },
        ]);
        setStartingNewProcess(true);
    };

    const onSendTeacherQuestionClicked = () => {
        if (!processId) {
            alert("Process ID is not set. Please start a new process first.");
            return;
        }
        if (!selectedTeacherQuestion) {
            alert("Please select a teacher question first.");
            return;
        }

        onSendTeacherQuestion?.({
            processId,
            user: TeacherStudentInteractionUser.TEACHER,
            content: selectedTeacherQuestion,
        })
            .then((result) => {
                if (result) {
                    console.log("Successfully sent teacher question");
                }
            })
            .catch((error) => {
                console.error("Error sending teacher question:", error);
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {
                        sender: ChatUser.ASSISTANT,
                        content: `Something went wrong and could not send question - ${error}`,
                        timestamp: new Date().toLocaleString(),
                    },
                ]);
            });

        setMessages((prevMessages) => [
            ...prevMessages,
            {
                sender: ChatUser.USER,
                content: `User asked teacher question - ${selectedTeacherQuestion}`,
                timestamp: new Date().toLocaleString(),
            },
        ]);
    };

    const onClearChat = () => {
        setMessages([]);
        setProcessId("");
    };

    return (
        <div className={styles.root}>
            <ChatHeader
                header={`Teacher Student Interaction with ${cloudTechnologyName}`}
                processId={processId}
            />
            <SimpleChat messages={messages} />
            <div className={styles.buttonsFamily}>
                <Button
                    appearance="primary"
                    icon={
                        startingNewProcess ? <Spinner size="tiny" /> : undefined
                    }
                    onClick={OnStartNewProcessClicked}
                    disabled={startingNewProcess}
                >
                    Start Process
                </Button>
                {/* {processId && ( */}
                <Dropdown
                    disabled={!processId}
                    placeholder="Select teacher question"
                    onOptionSelect={(_e: any, data: { optionValue: string }) =>
                        setSelectedTeacherQuestion(data.optionValue)
                    }
                >
                    {teacherMathQuestions.map((question) => (
                        <Option key={question} value={question}>
                            {question}
                        </Option>
                    ))}
                </Dropdown>
                <Button
                    disabled={!processId || !selectedTeacherQuestion}
                    onClick={onSendTeacherQuestionClicked}
                >
                    Send Teacher Question
                </Button>
                <Button
                    appearance="subtle"
                    onClick={onClearChat}
                    disabled={!processId}
                >
                    Clear chat
                </Button>
            </div>
        </div>
    );
};

export default TeacherStudentInteractionChat;
