const DATABASE_NAME = 'holographic-studio-assets'
const DATABASE_VERSION = 1
const STORE_NAME = 'models'

export interface ModelAssetRecord {
  id: string
  name: string
  blob: Blob
  size: number
  createdAt: number
}

const requestResult = <T>(request: IDBRequest<T>) =>
  new Promise<T>((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })

const openDatabase = () =>
  new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION)

    request.onupgradeneeded = () => {
      const database = request.result
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })

export async function saveModelAsset(asset: ModelAssetRecord) {
  const database = await openDatabase()

  try {
    const transaction = database.transaction(STORE_NAME, 'readwrite')
    await requestResult(transaction.objectStore(STORE_NAME).put(asset))
  } finally {
    database.close()
  }
}

export async function loadModelAsset(id: string) {
  const database = await openDatabase()

  try {
    const transaction = database.transaction(STORE_NAME, 'readonly')
    return (
      (await requestResult(
        transaction.objectStore(STORE_NAME).get(id),
      )) as ModelAssetRecord | undefined
    ) ?? null
  } finally {
    database.close()
  }
}
