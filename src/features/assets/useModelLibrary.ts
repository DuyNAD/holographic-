import { useCallback, useEffect, useState } from 'react'
import {
  deleteModelAsset,
  listModelAssets,
  type ModelAssetRecord,
} from './modelAssetStore'
import { importModelFile } from './modelLibrary'

export type ModelLibraryItem = Omit<ModelAssetRecord, 'blob'>

const toItem = ({ id, name, size, createdAt }: ModelAssetRecord) => ({
  id,
  name,
  size,
  createdAt,
})

export function useModelLibrary() {
  const [items, setItems] = useState<ModelLibraryItem[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('GLB tối đa 25 MB · lưu trên thiết bị.')
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    let cancelled = false

    listModelAssets()
      .then((assets) => {
        if (!cancelled) setItems(assets.map(toItem))
      })
      .catch(() => {
        if (cancelled) return
        setHasError(true)
        setMessage('Không thể mở kho vật thể trên thiết bị này.')
      })

    return () => {
      cancelled = true
    }
  }, [])

  const importFile = useCallback(async (file: File) => {
    setBusy(true)
    setHasError(false)
    setMessage('Đang kiểm tra và lưu vật thể…')

    try {
      const result = await importModelFile(file)
      if (!result.ok) {
        setHasError(true)
        setMessage(result.message)
        return null
      }

      setItems((current) => [toItem(result.asset), ...current])
      setMessage(`Đã lưu “${result.asset.name}” vào kho.`)
      return toItem(result.asset)
    } finally {
      setBusy(false)
    }
  }, [])

  const removeItem = useCallback(async (item: ModelLibraryItem) => {
    try {
      await deleteModelAsset(item.id)
      setItems((current) => current.filter(({ id }) => id !== item.id))
      setHasError(false)
      setMessage(`Đã xóa “${item.name}” khỏi kho.`)
    } catch {
      setHasError(true)
      setMessage('Không thể xóa vật thể khỏi kho.')
    }
  }, [])

  const report = useCallback((text: string, isError = false) => {
    setHasError(isError)
    setMessage(text)
  }, [])

  return { items, busy, message, hasError, importFile, removeItem, report }
}

export type ModelLibrary = ReturnType<typeof useModelLibrary>
