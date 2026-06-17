# Fall Detection API

Base URL: `http://localhost:3000` (update once deployed)

## Authentication

This API has two separate auth mechanisms, depending on the client.

### App requests (Firebase JWT)
```
Authorization: Bearer <firebase_id_token>
```
Verified via `userAuth` middleware → `getAuth().verifyIdToken(token)`. On success, `req.user` is populated with the decoded token (`req.user.uid` is the Firebase user ID).

### ESP32 requests (API key)
```
x-api-key: <device_api_key>
```
Verified via `deviceAuth` middleware against the `apiKey` stored on the device's Firestore document. On success, `req.device` is populated with the device's data (including `userId`).

---

## Devices

### `GET /api/v1/devices`
Fetch all devices linked to the authenticated user.

**Auth:** App (JWT)

**Request body:** none

**Response `200`:**
```json
{
  "devices": [
    {
      "id": "esp32_001",
      "userId": "abc123",
      "registeredAt": "2026-06-01T10:00:00.000Z"
    }
  ]
}
```
> Note: `apiKey` is stripped from the response before sending.

**Errors:**
| Status | Reason |
|---|---|
| 401 | Missing or invalid JWT |
| 500 | Server/Firestore error |

---

### `POST /api/v1/devices`
ESP32 registers itself during the initial pairing flow.

**Auth:** none (this *is* the handshake)

**Request body:**
```json
{
  "deviceId": "esp32_001",
  "userEmail": "user@example.com"
}
```

**Response `201`:**
```json
{
  "registered": true,
  "apiKey": "generated_hex_string"
}
```

**Response `409`** (device already registered):
```json
{
  "error": "Device already registered",
  "apiKey": "existing_hex_string"
}
```

**Errors:**
| Status | Reason |
|---|---|
| 400 | Missing `deviceId` or `userEmail` |
| 404 | No Firebase user found for `userEmail` |
| 409 | Device already registered (returns existing key) |
| 500 | Server/Firestore error |

---

## Events

### `POST /api/v1/events`
ESP32 posts a fall detection event.

**Auth:** ESP32 (`x-api-key`)

**Request body:**
```json
{
  "deviceId": "esp32_001",
  "timestamp": 1750000000
}
```
> `timestamp` is a Unix epoch (seconds), converted server-side into a Firestore `Timestamp`.

**Response `201`:**
```json
{
  "received": true,
  "eventId": "auto_generated_id"
}
```

**Stored document shape (`events` collection):**
```json
{
  "deviceId": "esp32_001",
  "userId": "abc123",
  "espTimestamp": "Firestore Timestamp",
  "serverTimestamp": "Firestore Timestamp",
  "status": "warning"
}
```

**Errors:**
| Status | Reason |
|---|---|
| 401 | Missing/invalid `x-api-key` or `deviceId` |
| 500 | Server/Firestore error |

---

### `PATCH /api/v1/events/:eventId/confirm`
App confirms whether a detected fall was real.

**Auth:** App (JWT)

**Request body:**
```json
{ "status": "fall" }
```
Accepted values: `"fall"` | `"no_fall"`

**Response `200`:**
```json
{ "eventId": "abc123", "status": "fall" }
```

**Errors:**
| Status | Reason |
|---|---|
| 400 | Invalid `status` value |
| 403 | Event doesn't belong to requesting user |
| 404 | Event not found |
| 409 | Event already confirmed (i.e. `status` is no longer `"warning"`) |

---

## Data Models

### `devices/{deviceId}`
| Field | Type | Notes |
|---|---|---|
| `userId` | string | Firebase UID, links device to owner |
| `apiKey` | string | Secret, never returned in `GET` responses |
| `registeredAt` | Timestamp | Set at registration |

### `events/{eventId}`
| Field | Type | Notes |
|---|---|---|
| `deviceId` | string | Which ESP32 sent it |
| `userId` | string | Resolved server-side via `req.device`, never trusted from ESP32 body |
| `espTimestamp` | Timestamp | When the ESP32 says the fall happened |
| `serverTimestamp` | Timestamp | When the server received it |
| `status` | string | `"warning"` initially, updated to `"fall"` / `"no_fall"` via the confirm route |

---

## Known issues / follow-ups

1. **Timestamp validation** — no sanity check yet on the ESP32-provided `timestamp` (e.g. clock drift, missing NTP sync). Worth adding before relying on `espTimestamp` for anything user-facing.