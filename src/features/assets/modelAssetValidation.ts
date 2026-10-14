export const MAX_MODEL_FILE_BYTES = 25 * 1024 * 1024

const GLB_HEADER_BYTES = 12
const GLB_MAGIC = 0x46546c67
const GLB_VERSION = 2

const readBlob = (blob: Blob) =>
  new Promise<ArrayBuffer>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as ArrayBuffer)
    reader.onerror = () => reject(reader.error)
    reader.readAsArrayBuffer(blob)
  })

export async function validateGlbFile(file: File): Promise<string | null> {
  if (!file.name.toLowerCase().endsWith('.glb')) {
    return 'Chỉ hỗ trợ file GLB.'
  }

  if (file.size > MAX_MODEL_FILE_BYTES) {
    return 'File GLB phải nhỏ hơn hoặc bằng 25 MB.'
  }

  if (file.size < GLB_HEADER_BYTES) {
    return 'File GLB không hợp lệ.'
  }

  const header = await readBlob(file.slice(0, GLB_HEADER_BYTES))
  const view = new DataView(header)
  const magic = view.getUint32(0, true)
  const version = view.getUint32(4, true)
  const declaredLength = view.getUint32(8, true)

  if (
    magic !== GLB_MAGIC ||
    version !== GLB_VERSION ||
    declaredLength !== file.size
  ) {
    return 'File không phải GLB 2.0 hợp lệ.'
  }

  return null
}

export const modelNameFromFile = (fileName: string) =>
  fileName.replace(/\.glb$/i, '').trim() || 'Vật thể đã tải'
