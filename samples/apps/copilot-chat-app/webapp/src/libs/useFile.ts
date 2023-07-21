// Copyright (c) Microsoft. All rights reserved.

import { SelectedFileStatus } from '../components/chat/tabs/DocumentsTab';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { FeatureKeys } from '../redux/features/app/AppState';
import { addAlert } from '../redux/features/app/appSlice';
import { AlertType } from './models/AlertType';
import { useChat } from './useChat';
import { useContentModerator } from './useContentModerator';

export const useFile = () => {
    const { features } = useAppSelector((state: RootState) => state.app);
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);
    const dispatch = useAppDispatch();
    const contentModerator = useContentModerator();

    const chat = useChat();

    async function loadFile<T>(file: File, loadCallBack: (data: T) => Promise<void>): Promise<T> {
        return await new Promise((resolve, reject) => {
            const fileReader = new FileReader();
            fileReader.onload = async (event: ProgressEvent<FileReader>) => {
                const content = event.target?.result as string;
                try {
                    const parsedData = JSON.parse(content) as T;
                    await loadCallBack(parsedData);
                    resolve(parsedData);
                } catch (e) {
                    reject(e);
                }
            };
            fileReader.onerror = reject;
            fileReader.readAsText(file);
        });
    }

    function downloadFile(filename: string, content: string, type: string) {
        const data: BlobPart[] = [content];
        let file: File | null = new File(data, filename, { type });

        const link = document.createElement('a');
        link.href = URL.createObjectURL(file);
        link.download = filename;

        link.click();
        URL.revokeObjectURL(link.href);
        link.remove();
        file = null;
    }

    function loadImage(file: File, loadCallBack: (base64Image: string) => Promise<void>): Promise<string> {
        return new Promise((resolve, reject) => {
            const fileReader = new FileReader();
            fileReader.onload = async (event: ProgressEvent<FileReader>) => {
                const content = event.target?.result as string;
                try {
                    await loadCallBack(content);
                    resolve(content);
                } catch (e) {
                    reject(e);
                }
            };
            fileReader.onerror = reject;
            fileReader.readAsDataURL(file);
        });
    }

    const handleImport = async (
        setDocumentImporting: React.Dispatch<React.SetStateAction<boolean>>,
        documentFileRef: React.MutableRefObject<HTMLInputElement | null>,
        setSelectedDocuments?: React.Dispatch<React.SetStateAction<SelectedFileStatus[]>>,
        file?: File,
        dragAndDropFiles?: FileList,
    ) => {
        const files = dragAndDropFiles ?? documentFileRef.current?.files;

        if (file || (files && files.length > 0)) {
            setDocumentImporting(true);
            // Deep copy the FileList into an array so that the function
            // maintains a list of files to import before the import is complete.
            const filesArray = file ? [file] : files ? Array.from(files) : [];
            const filesToUploadArray: File[] = [];
            const imageErrors: string[] = [];

            // Required for components that show import progress
            setSelectedDocuments?.(
                filesArray.map((file) => ({
                    name: file.name,
                    countDown: file.size / 1000, // Hack: count down is the number of seconds to complete the import.
                })),
            );

            for (const file of filesArray) {
                if (features[FeatureKeys.AzureContentSafety].enabled && file.type.startsWith('image/')) {
                    try {
                        await handleImageUpload(file);
                        filesToUploadArray.push(file);
                    } catch (e: any) {
                        imageErrors.push((e as Error).message);
                    }
                } else {
                    filesToUploadArray.push(file);
                }
            }

            if (imageErrors.length > 0) {
                setDocumentImporting(false);
                const errorMessage = `Failed to upload image(s): ${imageErrors.join('; ')}`;
                dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            }

            if (filesToUploadArray.length > 0) {
                chat.importDocument(selectedId, filesToUploadArray).finally(() => {
                    setDocumentImporting(false);
                });
            }
        }

        // Reset the file input so that the onChange event will
        // be triggered even if the same file is selected again.
        if (documentFileRef.current?.value) {
            documentFileRef.current.value = '';
        }
    };

    const handleImageUpload = async (file: File) => {
        await loadImage(file, contentModerator.analyzeImage).catch((error: Error) => {
            throw new Error(`'${file.name}': ${error.message}`);
        });
    };

    return {
        loadFile,
        downloadFile,
        loadImage,
        handleImport,
    };
};
