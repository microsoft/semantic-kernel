// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Tooltip,
} from '@fluentui/react-components';
import { ArrowUploadRegular } from '@fluentui/react-icons';
import React from 'react';
import { FileUploader } from './FileUploader';

// TODO: define the extension
const acceptedExtensions = ['sk', 'json'];

interface BotUploaderProps {
    onUpload: (file: File) => void;
}

export const BotUploader: React.FC<BotUploaderProps> = ({ onUpload }) => {
    const [open, setOpen] = React.useState(false);
    const [file, setFile] = React.useState<File | undefined>(undefined);

    const onChange = React.useCallback(
        (file: File) => {
            setFile(file);
        },
        [setFile],
    );

    return (
        <Dialog open={open} onOpenChange={(_event, data) => setOpen(data.open)}>
            <DialogTrigger disableButtonEnhancement>
                <Tooltip content="Load a bot" relationship="label">
                    <Button icon={<ArrowUploadRegular />} appearance="transparent" />
                </Tooltip>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Load a bot</DialogTitle>
                    <DialogContent>
                        <FileUploader acceptedExtensions={acceptedExtensions} onSelectedFile={onChange} />
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Close</Button>
                        </DialogTrigger>
                        <Button
                            appearance="primary"
                            onClick={() => file && (onUpload(file), setOpen(false), setFile(undefined))}
                            disabled={!file}
                        >
                            Upload
                        </Button>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
