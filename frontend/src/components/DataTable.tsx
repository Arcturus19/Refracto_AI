import React from 'react'

interface Column {
    header: string
    accessor: string
    render?: (row: any) => React.ReactNode
}

interface DataTableProps {
    columns: Column[]
    data: any[]
    onRowClick?: (row: any) => void
}

export default function DataTable({ columns, data, onRowClick }: DataTableProps) {
    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden animate-fade-in">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                            {columns.map((col, index) => (
                                <th key={index} className="px-6 py-4 font-semibold text-slate-700 uppercase tracking-wider text-xs">
                                    {col.header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {data.length > 0 ? (
                            data.map((row, rowIndex) => (
                                <tr
                                    key={rowIndex}
                                    onClick={() => onRowClick && onRowClick(row)}
                                    className={`
                    transition-colors
                    ${onRowClick ? 'cursor-pointer hover:bg-sky-50/50' : 'hover:bg-slate-50/50'}
                  `}
                                >
                                    {columns.map((col, colIndex) => (
                                        <td key={colIndex} className="px-6 py-4 text-slate-600">
                                            {col.render ? col.render(row) : row[col.accessor]}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={columns.length} className="px-6 py-12 text-center text-slate-400">
                                    No data available
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
