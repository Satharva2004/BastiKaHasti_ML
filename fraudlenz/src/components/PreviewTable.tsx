import type { PreviewRow } from '../types/api'

type PreviewTableProps = {
  columns: string[]
  rows: PreviewRow[]
}

function renderCellValue(value: PreviewRow[string]) {
  if (value === null || value === undefined) {
    return '-'
  }

  return String(value)
}

export function PreviewTable({ columns, rows }: PreviewTableProps) {
  return (
    <div className="preview-table-wrap reveal is-visible" data-reveal>
      <table className="preview-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${row.transaction_id ?? 'row'}-${rowIndex}`}>
              {columns.map((column) => (
                <td key={`${rowIndex}-${column}`}>{renderCellValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
