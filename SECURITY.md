# Security Architecture & Threat Model

## Overview
This document outlines the security model, cryptographic design, data protections, and explicit security boundaries of the **Signal Clone Platform**.

---

## 1. End-to-End Encryption (E2EE) Architecture (Direct 1:1 Chats)

Direct one-on-one chats implement a client-side End-to-End Encryption scheme utilizing the standard browser **Web Crypto API** (`window.crypto.subtle`):

### Key Generation & Storage
- **Algorithm**: Elliptic Curve Diffie-Hellman (ECDH) over Curve P-256 (`P-256`).
- **Private Key**: Generated directly inside the client browser. Marked non-extractable (`extractable: false`) and persisted securely in **IndexedDB** (`signal_crypto_db`).
- **Public Key**: Exported as JSON Web Key (JWK) and uploaded to the server public key registry (`PUT /api/v1/keys/me`).

### Key Exchange & Message Encryption
- When User A sends a message to User B:
  1. Client A fetches User B's public key JWK from `GET /api/v1/keys/{user2_id}`.
  2. Client A derives a 256-bit symmetric key (`AES-GCM`, 256-bit) using ECDH shared secret derivation.
  3. Client A encrypts the plaintext message with `AES-GCM` using a unique 12-byte initialization vector (`iv`).
  4. Client A sends `{ ciphertext, iv, is_encrypted: true }` over WebSocket to the backend. `body` is set to `null`.
- **Server Privacy**: The backend database stores only `ciphertext` and `iv` for direct messages. The server has **zero access** to the plaintext message content or private keys.

### Safety Number & Fingerprint Verification
- A 30-digit numeric safety number fingerprint is derived from both public keys using SHA-256.
- Users can compare safety numbers or mark a contact as verified (`POST /api/v1/contacts/{id}/verify`).
- If a contact logs in from a new browser or rotates their key pair, the server emits a `key.changed` event, notifying the user to re-verify safety numbers.

---

## 2. Group Messaging Security

> [!IMPORTANT]
> **Group Chat Limitation Notice**:
> In accordance with **FR-USP-5**, group messages in this build use **Transport Layer Security (TLS/WSS)** in transit and are stored encrypted/plaintext at rest on the server. Full Signal Sender Keys / Signal Protocol pairwise group encryption is out of scope for this version.

---

## 3. Threat Model & Boundaries

| Threat | Protected? | Mitigation |
| :--- | :--- | :--- |
| **Passive Network Eavesdropping** | ✅ YES | All transport uses TLS/HTTPS/WSS; 1:1 payloads are AES-GCM encrypted |
| **Rogue / Compromised Server** | ✅ YES | Server sees only ciphertext and IV for 1:1 direct chats |
| **MITM Public Key Substitution** | ⚠️ MITIGATED | Out-of-band Safety Number fingerprint verification |
| **Group Chat Server Interception** | ❌ NO | Groups rely on server-side fanout (TLS only) |
| **Physical Device Compromise** | ❌ NO | Extractable browser state or local DB access can compromise session |

---

## 4. API & Backend Hardening

1. **Authentication**: JWT Bearer Tokens (HS256) signed with server secret (`SECRET_KEY`). Short validity (24 hours).
2. **Object-Level Authorization (IDOR Prevention)**:
   - Every REST endpoint and WebSocket handler verifies that `current_user` has active membership (`left_at IS NULL`) in the target conversation.
   - Non-admins attempting admin actions on groups (adding/removing members, changing roles) receive HTTP `403 Forbidden`.
3. **Input Validation**: All payloads validated server-side using Pydantic v2 schemas and strict body limits (4000 char text limit, 5MB file upload limit).
4. **WebSocket Authentication**: WebSockets authenticate on connection via `?token=JWT`. Unauthenticated or invalid token connections are immediately rejected (`4001` / `4002`).
