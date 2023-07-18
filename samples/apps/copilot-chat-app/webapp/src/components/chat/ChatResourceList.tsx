// Copyright (c) Microsoft. All rights reserved.

import {
    Table,
    TableBody,
    TableCell,
    TableCellLayout,
    TableColumnDefinition,
    TableColumnId,
    TableHeader,
    TableHeaderCell,
    TableHeaderCellProps,
    TableRow,
    createTableColumn,
    makeStyles,
    shorthands,
    tokens,
    useTableFeatures,
    useTableSort,
} from '@fluentui/react-components';
import { DocumentPdfRegular, DocumentTextRegular, FluentIconsProps } from '@fluentui/react-icons';
import * as React from 'react';
import { ChatMemorySource } from '../../libs/models/ChatMemorySource';
import { useChat } from '../../libs/useChat';
import { SharedStyles } from '../../styles';
import { timestampToDateString } from '../utils/TextUtils';

const EmptyGuid = '00000000-0000-0000-0000-000000000000';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...SharedStyles.scroll,
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

interface TableItem {
    id: string;
    chatId: string;
    name: {
        label: string;
        icon: JSX.Element;
        url?: string;
    };
    createdOn: {
        label: string;
        timestamp: number;
    };
}

export const ChatResourceList: React.FC<ChatResourceListProps> = ({ chatId }) => {
    const classes = useClasses();
    const chat = useChat();
    const [resources, setResources] = React.useState<ChatMemorySource[]>([]);

    React.useEffect(() => {
        void chat.getChatMemorySources(chatId).then((sources) => {
            setResources(sources);
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [chatId]);

    const { columns, rows } = useTable(resources);
    return (
        <div className={classes.root}>
            <Table aria-label="External resource table" className={classes.table}>
                <TableHeader>
                    <TableRow>{columns.map((column) => column.renderHeaderCell())}</TableRow>
                </TableHeader>
                <TableBody>
                    {rows.map((item) => (
                        <TableRow key={item.id}>{columns.map((column) => column.renderCell(item))}</TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

function useTable(resources: ChatMemorySource[]) {
    const headerSortProps = (columnId: TableColumnId): TableHeaderCellProps => ({
        onClick: (e: React.MouseEvent) => {
            toggleColumnSort(e, columnId);
        },
        sortDirection: getSortDirection(columnId),
    });

    const columns: Array<TableColumnDefinition<TableItem>> = [
        createTableColumn<TableItem>({
            columnId: 'name',
            renderHeaderCell: () => (
                <TableHeaderCell key="name" {...headerSortProps('name')}>
                    Name
                </TableHeaderCell>
            ),
            renderCell: (item) => (
                <TableCell key={item.id}>
                    <TableCellLayout media={item.name.icon}>
                        <a href={item.name.url}>{item.name.label}</a>
                    </TableCellLayout>
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.name.label.localeCompare(b.name.label);
                return getSortDirection('name') === 'ascending' ? comparison : comparison * -1;
            },
        }),
        createTableColumn<TableItem>({
            columnId: 'createdOn',
            renderHeaderCell: () => (
                <TableHeaderCell key="createdOn" {...headerSortProps('createdOn')}>
                    Created on
                </TableHeaderCell>
            ),
            renderCell: (item) => (
                <TableCell key={item.createdOn.timestamp} title={new Date(item.createdOn.timestamp).toLocaleString()}>
                    {item.createdOn.label}
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.createdOn.timestamp > b.createdOn.timestamp ? 1 : -1;
                return getSortDirection('createdOn') === 'ascending' ? comparison : comparison * -1;
            },
        }),
        createTableColumn<TableItem>({
            columnId: 'access',
            renderHeaderCell: () => (
                <TableHeaderCell key="access" {...headerSortProps('access')}>
                    Access
                </TableHeaderCell>
            ),
            renderCell: (item) => (
                <TableCell key={`${item.id} ${item.name.label}`}>{getAccessString(item.chatId)}</TableCell>
            ),
            compare: (a, b) => {
                const aAccess = getAccessString(a.chatId);
                const bAccess = getAccessString(b.chatId);
                const comparison = aAccess.localeCompare(bAccess);
                return getSortDirection('access') === 'ascending' ? comparison : comparison * -1;
            },
        }),
    ];

    const items = resources.map((item) => ({
        id: item.id,
        chatId: item.chatId,
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

    const {
        sort: { getSortDirection, toggleColumnSort, sortColumn },
    } = useTableFeatures(
        {
            columns,
            items,
        },
        [
            useTableSort({
                defaultSortState: { sortColumn: 'name', sortDirection: 'ascending' },
            }),
        ],
    );

    if (sortColumn) {
        items.sort((a, b) => {
            const compare = columns.find((column) => column.columnId === sortColumn)?.compare;
            return compare?.(a, b) ?? 0;
        });
    }

    return { columns, rows: items };
}

function getAccessString(chatId: string) {
    return chatId === EmptyGuid ? 'Global' : 'This chat';
}

export function getFileIconByFileExtension(fileName: string, props: FluentIconsProps = {}) {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.') + 1);
    if (extension === 'pdf') {
        return <DocumentPdfRegular {...props} />;
    }
    return <DocumentTextRegular {...props} />;
}
