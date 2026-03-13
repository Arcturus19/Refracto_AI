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
        <div className="bg-white rounded-2xl premium-shadow overflow-hidden animate-fade-in">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                            {columns.map((col, index) => (
                                <th key={index} className="px-6 py-4 font-semibold text-slate-700 uppercase tracking-wider text-xs">
                                    {col.header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 bg-white">
                        {data.length > 0 ? (
                            data.map((row, rowIndex) => (
                                <tr
                                    key={rowIndex}
                                    onClick={() => onRowClick && onRowClick(row)}
                                    className={`
                    transition-all duration-200 group
                    ${onRowClick ? 'cursor-pointer hover:bg-slate-50/80 hover:shadow-sm relative z-0 hover:z-10' : 'hover:bg-slate-50/50'}
                  `}
                                >
                                    {columns.map((col, colIndex) => (
                                        <td key={colIndex} className="px-6 py-4 text-slate-600 transition-colors group-hover:text-slate-800">
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
