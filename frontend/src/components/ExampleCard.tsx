import React from 'react'

export default function ExampleCard({ children }: { children?: React.ReactNode }) {
  return <div className="p-4 border rounded">{children}</div>
}
