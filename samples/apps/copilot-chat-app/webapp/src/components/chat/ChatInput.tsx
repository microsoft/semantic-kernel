// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Button, Spinner, Textarea, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { AttachRegular, ImageRegular, MicRegular, SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React, { useCallback, useRef } from 'react';
import { Constants } from '../../Constants';
import { AuthHelper } from '../../libs/auth/AuthHelper';
import { AlertType } from '../../libs/models/AlertType';
import { ChatMessageType } from '../../libs/models/ChatMessage';
import { GetResponseOptions, useChat } from '../../libs/useChat';
import { useContentModerator } from '../../libs/useContentModerator';
import { useFile } from '../../libs/useFile';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { FeatureKeys } from '../../redux/features/app/AppState';
import { addAlert } from '../../redux/features/app/appSlice';
import { editConversationInput } from '../../redux/features/conversations/conversationsSlice';
import { FileUploader } from '../FileUploader';
import { SpeechService } from './../../libs/services/SpeechService';
import { updateUserIsTyping } from './../../redux/features/conversations/conversationsSlice';
import { ChatStatus } from './ChatStatus';
import { Alerts } from './shared/Alerts';

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
    alert: {
        fontWeight: tokens.fontWeightRegular,
        color: tokens.colorNeutralForeground1,
        backgroundColor: tokens.colorNeutralBackground6,
        fontSize: tokens.fontSizeBase200,
        lineHeight: tokens.lineHeightBase200,
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
        ...shorthands.border(tokens.strokeWidthThick, ' solid', tokens.colorBrandStroke1),
        ...shorthands.padding('8px'),
        textAlign: 'center',
        backgroundColor: tokens.colorNeutralBackgroundInvertedDisabled,
        fontSize: tokens.fontSizeBase300,
        color: tokens.colorBrandForeground1,
        caretColor: 'transparent',
    },
});

interface ChatInputProps {
    isDraggingOver?: boolean;
    onDragLeave: React.DragEventHandler<HTMLDivElement | HTMLTextAreaElement>;
    onSubmit: (options: GetResponseOptions) => Promise<void>;
}

export const ChatInput: React.FC<ChatInputProps> = ({ isDraggingOver, onDragLeave, onSubmit }) => {
    const classes = useClasses();
    const { instance, inProgress } = useMsal();
    const chat = useChat();
    const dispatch = useAppDispatch();
    const [value, setValue] = React.useState('');
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const [documentImporting, setDocumentImporting] = React.useState(false);
    const documentFileRef = useRef<HTMLInputElement | null>(null);
    const imageUploaderRef = useRef<HTMLInputElement>(null);
    const fileHandler = useFile();
    const contentModerator = useContentModerator();

    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { activeUserInfo, features } = useAppSelector((state: RootState) => state.app);

    React.useEffect(() => {
        async function initSpeechRecognizer() {
            const speechService = new SpeechService(process.env.REACT_APP_BACKEND_URI as string);
            const response = await speechService.getSpeechTokenAsync(
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
            if (response.isSuccess) {
                const recognizer = speechService.getSpeechRecognizerAsyncWithValidKey(response);
                setRecognizer(recognizer);
            }
        }

        initSpeechRecognizer().catch((e) => {
            const errorDetails = e instanceof Error ? e.message : String(e);
            const errorMessage = `Unable to initialize speech recognizer. Details: ${errorDetails}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        });
    }, [dispatch, instance, inProgress]);

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

    const handleImport = (dragAndDropFiles?: FileList) => {
        const files = dragAndDropFiles ?? documentFileRef.current?.files;

        if (files && files.length > 0) {
            setDocumentImporting(true);
            // Deep copy the FileList into an array so that the function
            // maintains a list of files to import before the import is complete.
            const filesArray = Array.from(files);
            const filesToUploadArray: File[] = [];

            filesArray.forEach((file) => {
                if (file.type.startsWith('image/')) {
                    handleImageUpload(file);
                } else {
                    filesToUploadArray.push(file);
                }
            });

            chat.importDocument(selectedId, filesToUploadArray).finally(() => {
                setDocumentImporting(false);
            });
        }

        // Reset the file input so that the onChange event will
        // be triggered even if the same file is selected again.
        if (documentFileRef.current?.value) {
            documentFileRef.current.value = '';
        }
    };

    const handleImageUpload = useCallback(
        (file: File) => {
            void fileHandler
                .loadImage(file, contentModerator.analyzeImage)
                .catch((error: Error) =>
                    dispatch(addAlert({ message: `Failed to upload image. ${error.message}`, type: AlertType.Error })),
                );
        },
        [fileHandler, dispatch, contentModerator],
    );

    const handleSubmit = (value: string, messageType: ChatMessageType = ChatMessageType.Message) => {
        if (value.trim() === '') {
            return; // only submit if value is not empty
        }

        setValue('');
        dispatch(editConversationInput({ id: selectedId, newInput: '' }));
        onSubmit({ value, messageType, chatId: selectedId }).catch((error) => {
            const message = `Error submitting chat input: ${(error as Error).message}`;
            log(message);
            dispatch(
                addAlert({
                    type: AlertType.Error,
                    message,
                }),
            );
        });
    };

    const handleDrop = (e: React.DragEvent<HTMLTextAreaElement>) => {
        if (!features[FeatureKeys.SimplifiedExperience].enabled) {
            onDragLeave(e);
            handleImport(e.dataTransfer.files);
        }
    };

    return (
        <div className={classes.root}>
            <div className={classes.typingIndicator}>
                <ChatStatus />
            </div>
            <Alerts />
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
                        const chatInput = document.getElementById('chat-input');
                        if (chatInput) {
                            setValue((chatInput as HTMLTextAreaElement).value);
                        }
                        // User is considered typing if the input is in focus
                        dispatch(
                            updateUserIsTyping({ userId: activeUserInfo?.id, chatId: selectedId, isTyping: true }),
                        );
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
                    onBlur={() => {
                        // User is considered not typing if the input is not  in focus
                        dispatch(
                            updateUserIsTyping({ userId: activeUserInfo?.id, chatId: selectedId, isTyping: false }),
                        );
                    }}
                />
            </div>
            <div className={classes.controls}>
                {!features[FeatureKeys.SimplifiedExperience].enabled && (
                    <div className={classes.functional}>
                        {/* Hidden input for file upload. Only accept .txt and .pdf files for now. */}
                        <input
                            type="file"
                            ref={documentFileRef}
                            style={{ display: 'none' }}
                            accept=".txt,.pdf,.md,.jpg,.jpeg,.png,.tif,.tiff"
                            multiple={true}
                            onChange={() => {
                                handleImport();
                            }}
                        />
                        <Button
                            disabled={documentImporting}
                            appearance="transparent"
                            icon={<AttachRegular />}
                            onClick={() => documentFileRef.current?.click()}
                        />
                        <FileUploader
                            ref={imageUploaderRef}
                            acceptedExtensions={['.jpeg', '.png']}
                            onSelectedFile={handleImageUpload}
                        />
                        <Button
                            appearance="transparent"
                            icon={<ImageRegular />}
                            onClick={() => imageUploaderRef.current?.click()}
                        />
                        {documentImporting && <Spinner size="tiny" />}
                    </div>
                )}
                <div className={classes.essentials}>
                    {recognizer && (
                        <Button
                            appearance="transparent"
                            disabled={isListening}
                            icon={<MicRegular />}
                            onClick={handleSpeech}
                        />
                    )}
                    <Button
                        appearance="transparent"
                        icon={<SendRegular />}
                        onClick={() => {
                            handleSubmit(value);
                        }}
                    />
                </div>
            </div>
        </div>
    );
};
