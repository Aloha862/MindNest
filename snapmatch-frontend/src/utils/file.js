export function isImage(file) {
  return ['image/jpeg', 'image/jpg', 'image/png'].includes(file?.type)
}

export function fileSizeText(size) {
  if (!size) return '0 KB'
  return size > 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(2)} MB` : `${(size / 1024).toFixed(1)} KB`
}
