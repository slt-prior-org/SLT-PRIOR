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

