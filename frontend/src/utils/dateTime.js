const TIMEZONE_SUFFIX_PATTERN = /(Z|[+-]\d{2}:?\d{2})$/i
const HAS_TIME_PATTERN = /[T ]\d{2}:\d{2}/

export function parseBackendDate(value) {
  if (!value) return null
  if (value instanceof Date) return value

  if (typeof value === "string" && HAS_TIME_PATTERN.test(value) && !TIMEZONE_SUFFIX_PATTERN.test(value)) {
    return new Date(`${value}Z`)
  }

  return new Date(value)
}

export function formatMessageTime(value) {
  const date = parseBackendDate(value)
  if (!date) return ""
  
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  
  return `${hours}:${minutes}`
}

