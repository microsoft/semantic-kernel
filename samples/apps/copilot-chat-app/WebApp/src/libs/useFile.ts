// Copyright (c) Microsoft. All rights reserved.
// import { useAppDispatch } from '../redux/app/hooks';

export const useFile = () => {
    // const dispatch = useAppDispatch();

    const downloadFile = (filename: string, content: string, type: string) => {
        const data: BlobPart[] = [content];
        let file: File | null = new File(data, filename, { type });

        const link = document.createElement('a');
        link.href = URL.createObjectURL(file);
        link.download = filename;

        link.click();
        URL.revokeObjectURL(link.href);
        link.remove();
        file = null;
    };

    return {
        downloadFile,
    };
};
