// Copyright (c) Microsoft. All rights reserved.

import {
    Table,
    TableBody,
    TableCell,
    TableCellLayout,
    TableHeader,
    TableHeaderCell,
    TableRow,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { DocumentPdfRegular, DocumentTextRegular } from '@fluentui/react-icons';
import * as React from 'react';
import { ChatMemorySource } from '../../libs/models/ChatMemorySource';
import { useChat } from '../../libs/useChat';
import { timestampToDateString } from '../utils/TextUtils';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    table: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: tokens.fontSizeBase600,
    },
});

interface ChatResourceListProps {
    chatId: string;
}

export const ChatResourceList: React.FC<ChatResourceListProps> = ({ chatId }) => {
    const classes = useClasses();
    const chat = useChat();
    const [resources, setResources] = React.useState<ChatMemorySource[]>([]);

    React.useEffect(() => {
        chat.getChatMemorySources(chatId).then((sources) => {
            setResources(sources);
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [chatId]);

    const items = resources.map((item) => ({
        name: {
            label: item.name,
            icon: getFileIconByFileExtension(item.name),
            url: item.hyperlink,
        },
        createdOn: {
            label: timestampToDateString(item.createdOn),
            timestamp: item.createdOn,
        },
    }));

    const columns = [
        { columnKey: 'name', label: 'Name' },
        { columnKey: 'createdOn', label: 'Created on' },
    ];

    return (
        <div className={classes.root}>
            <Table aria-label="External resource table" className={classes.table}>
                <TableHeader>
                    <TableRow>
                        {columns.map((column) => (
                            <TableHeaderCell key={column.columnKey}>
                                <span className={classes.tableHeader}>{column.label}</span>
                            </TableHeaderCell>
                        ))}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {items
                        .sort((a, b) => a.createdOn.timestamp - b.createdOn.timestamp)
                        .map((item) => (
                            <TableRow key={item.name.label}>
                                <TableCell>
                                    <TableCellLayout media={item.name.icon}>
                                        <a href={item.name.url}>{item.name.label}</a>
                                    </TableCellLayout>
                                </TableCell>
                                <TableCell title={new Date(item.createdOn.timestamp).toLocaleString()}>
                                    {item.createdOn.label}
                                </TableCell>
                            </TableRow>
                        ))}
                </TableBody>
            </Table>
        </div>
    );
};

function getFileIconByFileExtension(fileName: string) {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.') + 1);
    if (extension === 'pdf') {
        return <DocumentPdfRegular />;
    }
    return <DocumentTextRegular />;
}
