/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */

import React from "react";
import { Title2, Label, makeStyles } from "@fluentui/react-components"; // Adjust imports based on your UI library

interface ChatHeaderProps {
    header: string;
    processId?: string;
}

const useStyles = makeStyles({
    processIdContainer: {
        display: "flex",
        flexDirection: "column",
        rowGap: "8px",
        alignItems: "flex-end",
    },
    headerContainer: {
        display: "flex",
        justifyContent: "space-between",
    },
});

const ChatHeader: React.FC<ChatHeaderProps> = ({
    header,
    processId,
}) => {
    const styles = useStyles();

    return (
        <div className={styles.headerContainer}>
            <Title2>
                {header}
            </Title2>
            <div className={styles.processIdContainer}>
                <Label>ProcessId : </Label>
                <Label>{processId ?? "-"}</Label>
            </div>
        </div>
    );
};

export default ChatHeader;
