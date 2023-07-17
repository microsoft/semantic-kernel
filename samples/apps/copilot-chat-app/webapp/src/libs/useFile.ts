// Copyright (c) Microsoft. All rights reserved.

export const useFile = () => {
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

    return {
        loadFile,
        downloadFile,
    };
};
