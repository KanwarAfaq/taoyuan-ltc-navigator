const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Fetches day care facilities matching a district from the FastAPI backend.
 * Throws a descriptive error on network failure (e.g. backend not running)
 * vs. an HTTP error (e.g. backend running but returned a bad status), so
 * the UI can show the right message for each case.
 */
export async function matchFacilities(district) {
  let response;
  try {
    const url = new URL('/match', API_BASE_URL);
    if (district) url.searchParams.set('district', district);
    response = await fetch(url);
  } catch (err) {
    throw new Error('NETWORK_ERROR');
  }

  if (!response.ok) {
    throw new Error(`HTTP_ERROR_${response.status}`);
  }

  return response.json();
}

/**
 * Facility self-update ("anyone with this link can edit this one
 * facility's vacancy status") -- no login, just a long random token in
 * the URL. Distinguishes NOT_FOUND (invalid/unknown token) from other
 * HTTP errors so the UI can show the right message.
 */
export async function getFacilityByToken(token) {
  const url = new URL(`/facilities/by-token/${token}`, API_BASE_URL);
  const response = await fetch(url);
  if (response.status === 404) throw new Error('NOT_FOUND');
  if (!response.ok) throw new Error(`HTTP_ERROR_${response.status}`);
  return response.json();
}

export async function updateVacancyByToken(token, vacancyStatus) {
  const url = new URL(`/facilities/by-token/${token}`, API_BASE_URL);
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vacancy_status: vacancyStatus }),
  });
  if (response.status === 404) throw new Error('NOT_FOUND');
  if (!response.ok) throw new Error(`HTTP_ERROR_${response.status}`);
  return response.json();
}
