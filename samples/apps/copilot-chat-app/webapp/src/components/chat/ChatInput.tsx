// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Button, Spinner, Textarea, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { AttachRegular, MicRegular, SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React, { useRef } from 'react';
import { Constants } from '../../Constants';
import { AuthHelper } from '../../libs/auth/AuthHelper';
import { AlertType } from '../../libs/models/AlertType';
import { ChatMessageType } from '../../libs/models/ChatMessage';
import { DocumentImportService } from '../../libs/services/DocumentImportService';
import { GetResponseOptions } from '../../libs/useChat';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { addAlert } from '../../redux/features/app/appSlice';
import { editConversationInput } from '../../redux/features/conversations/conversationsSlice';
import { CopilotChatTokens } from '../../styles';
import { SpeechService } from './../../libs/services/SpeechService';
import { TypingIndicatorRenderer } from './typing-indicator/TypingIndicatorRenderer';

const log = debug(Constants.debug.root).extend('chat-input');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.margin(0, '72px'),
    },
    typingIndicator: {
        maxHeight: '28px',
    },
    content: {
        ...shorthands.gap(tokens.spacingHorizontalM),
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
    },
    input: {
        width: '100%',
    },
    textarea: {
        maxHeight: '80px',
    },
    controls: {
        display: 'flex',
        flexDirection: 'row',
    },
    essentials: {
        display: 'flex',
        flexDirection: 'row',
        marginLeft: 'auto', // align to right
    },
    functional: {
        display: 'flex',
        flexDirection: 'row',
    },
    dragAndDrop: {
        ...shorthands.border('2px', ' solid', CopilotChatTokens.backgroundColor),
        ...shorthands.padding('8px'),
        textAlign: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        fontSize: '14px',
        color: CopilotChatTokens.backgroundColor,
        caretColor: 'transparent',
    },
});

interface ChatInputProps {
    // Hardcode to single user typing. For multi-users, it should be a list of ChatUser who are typing.
    isTyping?: boolean;
    isDraggingOver?: boolean;
    onDragLeave: React.DragEventHandler<HTMLDivElement | HTMLTextAreaElement>;
    onSubmit: (options: GetResponseOptions) => void;
}

export const ChatInput: React.FC<ChatInputProps> = (props) => {
    const { isTyping, isDraggingOver, onDragLeave, onSubmit } = props;
    const classes = useClasses();
    const { instance, inProgress } = useMsal();
    const account = instance.getActiveAccount();
    const dispatch = useAppDispatch();
    const [value, setValue] = React.useState('');
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const [documentImporting, SetDocumentImporting] = React.useState(false);
    const documentImportService = new DocumentImportService(process.env.REACT_APP_BACKEND_URI as string);
    const documentFileRef = useRef<HTMLInputElement | null>(null);
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    React.useEffect(() => {
        async function initSpeechRecognizer() {
            const speechService = new SpeechService(process.env.REACT_APP_BACKEND_URI as string);
            var response = await speechService.getSpeechTokenAsync(
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
            if (response.isSuccess) {
                const recognizer = await speechService.getSpeechRecognizerAsyncWithValidKey(response);
                setRecognizer(recognizer);
            }
        }

        initSpeechRecognizer();
    }, [instance, inProgress]);

    React.useEffect(() => {
        const chatState = conversations[selectedId];
        setValue(chatState.input);
    }, [conversations, selectedId]);

    const handleSpeech = () => {
        setIsListening(true);
        if (recognizer) {
            recognizer.recognizeOnceAsync((result) => {
                if (result.reason === speechSdk.ResultReason.RecognizedSpeech) {
                    if (result.text && result.text.length > 0) {
                        handleSubmit(result.text);
                    }
                }
                setIsListening(false);
            });
        }
    };

    const selectDocument = () => {
        documentFileRef.current?.click();
    };

    const importDocument = async (dragAndDropFile?: File) => {
        const documentFile = dragAndDropFile ?? documentFileRef.current?.files?.[0];
        if (documentFile) {
            try {
                SetDocumentImporting(true);
                const document = await documentImportService.importDocumentAsync(
                    account!.homeAccountId!,
                    selectedId,
                    documentFile,
                    await AuthHelper.getSKaaSAccessToken(instance, inProgress),
                );

                handleSubmit(JSON.stringify(document), ChatMessageType.Document);
            } catch (e: any) {
                const errorMessage = `Failed to upload document. Details: ${e.message ?? e}`;
                dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            }
            SetDocumentImporting(false);
        }

        // Reset the file input so that the onChange event will
        // be triggered even if the same file is selected again.
        documentFileRef.current!.value = '';
    };

    const handleDrop = async (e: React.DragEvent<HTMLTextAreaElement>) => {
        onDragLeave(e);
        await importDocument(e.dataTransfer?.files[0]);
    };

    const handleSubmit = (value: string, messageType: ChatMessageType = ChatMessageType.Message) => {
        try {
            if (value.trim() === '') {
                return; // only submit if value is not empty
            }
            onSubmit({ value, messageType, chatId: selectedId });
            setValue('');
            dispatch(editConversationInput({ id: selectedId, newInput: '' }));
        } catch (error) {
            const message = `Error submitting chat input: ${(error as Error).message}`;
            log(message);
            dispatch(
                addAlert({
                    type: AlertType.Error,
                    message,
                }),
            );
        }
    };

    return (
        <div className={classes.root}>
            <div className={classes.typingIndicator}>{isTyping ? <TypingIndicatorRenderer /> : null}</div>
            <div className={classes.content}>
                <Textarea
                    id="chat-input"
                    resize="vertical"
                    textarea={{
                        className: isDraggingOver
                            ? mergeClasses(classes.dragAndDrop, classes.textarea)
                            : classes.textarea,
                    }}
                    className={classes.input}
                    value={isDraggingOver ? 'Drop your files here' : value}
                    onDrop={handleDrop}
                    onFocus={() => {
                        // update the locally stored value to the current value
                        const chatInput = document.getElementById('chat-input') as HTMLTextAreaElement;
                        if (chatInput) {
                            setValue(chatInput.value);
                        }
                    }}
                    onChange={(_event, data) => {
                        if (isDraggingOver) {
                            return;
                        }

                        setValue(data.value);
                        dispatch(editConversationInput({ id: selectedId, newInput: data.value }));
                    }}
                    onKeyDown={(event) => {
                        if (event.key === 'Enter' && !event.shiftKey) {
                            event.preventDefault();
                            handleSubmit(value);
                        }
                    }}
                />
            </div>
            <div className={classes.controls}>
                <div className={classes.functional}>
                    {/* Hidden input for file upload. Only accept .txt files for now. */}
                    <input
                        type="file"
                        ref={documentFileRef}
                        style={{ display: 'none' }}
                        accept=".txt,.pdf"
                        multiple={false}
                        onChange={() => importDocument()}
                    />
                    <Button
                        disabled={documentImporting}
                        appearance="transparent"
                        icon={<AttachRegular />}
                        onClick={() => selectDocument()}
                    />
                    {documentImporting && <Spinner size="tiny" />}
                </div>
                <div className={classes.essentials}>
                    {recognizer && (
                        <Button
                            appearance="transparent"
                            disabled={isListening}
                            icon={<MicRegular />}
                            onClick={() => handleSpeech()}
                        />
                    )}
                    <Button appearance="transparent" icon={<SendRegular />} onClick={() => handleSubmit(value)} />
                </div>
            </div>
        </div>
    );
};
