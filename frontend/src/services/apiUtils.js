export function unwrapApi(payload, fallback = null) {
  if (payload == null) return fallback;
  if (payload instanceof Blob) return payload;
  if (payload.data !== undefined && payload.success !== undefined) return payload.data ?? fallback;
  if (payload.data?.data !== undefined) return payload.data.data ?? fallback;
  if (payload.data !== undefined && payload.message !== undefined) return payload.data ?? fallback;
  return payload;
}

export function asArray(payload) {
  const data = unwrapApi(payload, []);
  return Array.isArray(data) ? data : [];
}

export function apiErrorMessage(error, fallback = 'Request failed') {
  return error?.message || error?.raw?.message || fallback;
}

export function notify(message, type = 'info') {
  window.dispatchEvent(new CustomEvent('defectai:toast', { detail: { message, type } }));
}
