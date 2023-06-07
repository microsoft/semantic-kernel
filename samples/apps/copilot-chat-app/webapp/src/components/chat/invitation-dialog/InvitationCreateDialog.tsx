// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle, Label, makeStyles, tokens } from "@fluentui/react-components";
import React from "react";

const useStyles = makeStyles({
    content: {
        display: "flex",
        flexDirection: "column",
        rowGap: tokens.spacingVerticalMNudge,
    },
});

interface InvitationCreateDialogProps {
    onCancel: () => void;
    chatId: string;
}

export const InvitationCreateDialog: React.FC<InvitationCreateDialogProps> = ({ onCancel, chatId }) => {
    const [isIdCopied, setIsIdCopied] = React.useState<boolean>(false);

    const classes = useStyles();

    const copyId = () => {
        navigator.clipboard.writeText(chatId);
        setIsIdCopied(true);
    };

    return (
        <div>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Invite others to your Bot</DialogTitle>
                    <DialogContent className={classes.content}>
                        <Label>
                            Please provide the following Chat ID to your friends so they can join the chat.
                        </Label>
                        <Label weight="semibold">{ chatId }</Label>
                    </DialogContent>
                    <DialogActions>
                        <Button appearance="secondary" onClick={onCancel}>Close</Button>
                        <Button appearance="primary" onClick={copyId}>{isIdCopied ? "Copied" : "Copy"}</Button>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </div>
    );
};