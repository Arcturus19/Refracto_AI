import { useState } from 'react'

export default function useExample() {
  const [value, setValue] = useState(0)
  return { value, setValue }
}
