// Copyright (c) Microsoft. All rights reserved.
import { useMsal } from '@azure/msal-react';
import { DocumentDeleteService } from './services/DocumentDeleteService';
import { useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { AuthHelper } from './auth/AuthHelper';

export interface FileHandler {
    loadFile<T>(file: File, loadCallBack: (data: T) => Promise<void>): Promise<T>;
    downloadFile(filename: string, content: string, type: string): void;
    deleteFile(chatId: string, fileId: string): Promise<void>;
  }

export const useFile = (): FileHandler => {
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);
    const userId = activeUserInfo?.id ?? '';
    const documentDeleteService = new DocumentDeleteService(process.env.REACT_APP_BACKEND_URI as string);
    const { instance, inProgress } = useMsal();

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

    async function deleteFile(chatId: string, fileId: string): Promise<void> {
        try {

            // Call the deleteDocumentAsync method from the DocumentDeleteService
            await documentDeleteService.deleteDocumentAsync(userId, chatId, fileId,  await AuthHelper.getSKaaSAccessToken(instance, inProgress));

        } catch (error) {
            console.error('Failed to delete the file:', error);
        }
    }

    return {
        loadFile,
        downloadFile,
        deleteFile,
    };
};
