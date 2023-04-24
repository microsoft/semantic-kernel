// Copyright (c) Microsoft. All rights reserved.

export const useFile = () => {
    function loadFile<T>(file: File, loadCallBack: (bot: T) => Promise<void>) {
        const fileReader = new FileReader();
        fileReader.onload = async (event: ProgressEvent<FileReader>) => {
            const content = event?.target?.result as string;
            const parsedData = JSON.parse(content) as T;

            return await loadCallBack(parsedData);
        };
        fileReader.readAsText(file);
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

    return {
        loadFile,
        downloadFile,
    };
};
