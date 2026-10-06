const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

function getHeaders(): Record<string, string> {
  const token = localStorage.getItem("signal_token");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(),
      ...(options.headers || {})
    }
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data?.detail?.message || data?.detail || data?.message || "An error occurred";
    throw new Error(errorMsg);
  }

  return data as T;
}

export const api = {
  // Auth
  requestOtp: (phone?: string, username?: string) =>
    request<{ success: boolean; message: string }>("/auth/request-otp", {
      method: "POST",
      body: JSON.stringify({ phone, username })
    }),

  verifyOtp: (identifier: string, otp: string) =>
    request<{ access_token: string; is_new_user: boolean; user: any }>("/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ identifier, otp })
    }),

  setupProfile: (displayName: string, avatarUrl?: string, about?: string) =>
    request<any>("/auth/profile", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName, avatar_url: avatarUrl, about })
    }),

  logout: () => request<{ success: boolean }>("/auth/logout", { method: "POST" }),

  // Users
  getMe: () => request<any>("/users/me"),
  updateMe: (data: { display_name?: string; about?: string; avatar_url?: string; settings_json?: any }) =>
    request<any>("/users/me", { method: "PATCH", body: JSON.stringify(data) }),
  searchUsers: (query: string) => request<any[]>(`/users/search?q=${encodeURIComponent(query)}`),

  // Contacts
  getContacts: () => request<any[]>("/contacts"),
  addContact: (identifier: string, nickname?: string) =>
    request<any>("/contacts", { method: "POST", body: JSON.stringify({ identifier, nickname }) }),
  removeContact: (id: number) => request<{ success: boolean }>(`/contacts/${id}`, { method: "DELETE" }),

  // Conversations
  getConversations: (query = "", filter = "all") =>
    request<any[]>(`/conversations?q=${encodeURIComponent(query)}&filter=${encodeURIComponent(filter)}`),
  createDirectConversation: (userId: number) =>
    request<any>("/conversations", { method: "POST", body: JSON.stringify({ user_id: userId }) }),
  createNoteToSelf: () => request<any>("/conversations/note-to-self", { method: "POST" }),
  getConversation: (id: number) => request<any>(`/conversations/${id}`),
  getMessages: (conversationId: number, before?: number, limit = 50) => {
    let url = `/conversations/${conversationId}/messages?limit=${limit}`;
    if (before) url += `&before=${before}`;
    return request<any[]>(url);
  },
  sendMessageRest: (conversationId: number, data: { body?: string; client_id?: string; type?: string; ciphertext?: string; iv?: string; is_encrypted?: boolean; reply_to_id?: number }) =>
    request<any>(`/conversations/${conversationId}/messages`, { method: "POST", body: JSON.stringify(data) }),
  markRead: (conversationId: number, upToMessageId: number) =>
    request<{ success: boolean }>(`/conversations/${conversationId}/read?up_to_message_id=${upToMessageId}`, { method: "POST" }),
  updateSettings: (conversationId: number, data: { is_muted?: boolean; is_archived?: boolean; disappearing_seconds?: number }) =>
    request<{ success: boolean }>(`/conversations/${conversationId}/settings`, { method: "PATCH", body: JSON.stringify(data) }),

  // Groups
  createGroup: (name: string, memberIds: number[], avatarUrl?: string) =>
    request<any>("/groups", { method: "POST", body: JSON.stringify({ name, member_ids: memberIds, avatar_url: avatarUrl }) }),
  getGroupMembers: (id: number) => request<any[]>(`/groups/${id}/members`),
  addGroupMembers: (id: number, userIds: number[]) =>
    request<any>(`/groups/${id}/members`, { method: "POST", body: JSON.stringify({ user_ids: userIds }) }),
  removeGroupMember: (id: number, userId: number) =>
    request<any>(`/groups/${id}/members/${userId}`, { method: "DELETE" }),
  updateGroup: (id: number, data: { name?: string; avatar_url?: string }) =>
    request<any>(`/groups/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  updateMemberRole: (id: number, userId: number, role: string) =>
    request<any>(`/groups/${id}/members/${userId}/role`, { method: "PATCH", body: JSON.stringify({ role }) }),

  // Messages
  deleteMessage: (id: number) => request<any>(`/messages/${id}`, { method: "DELETE" }),
  setReaction: (id: number, emoji: string) => request<any>(`/messages/${id}/reaction`, { method: "PUT", body: JSON.stringify({ emoji }) }),
  removeReaction: (id: number) => request<any>(`/messages/${id}/reaction`, { method: "DELETE" }),
  getMessageInfo: (id: number) => request<any>(`/messages/${id}/info`),

  // USP Keys & Safety Number
  registerPublicKey: (publicKeyJwk: string, fingerprint: string) =>
    request<any>("/keys/me", { method: "PUT", body: JSON.stringify({ public_key_jwk: publicKeyJwk, fingerprint }) }),
  getUserPublicKey: (userId: number) => request<any>(`/keys/${userId}`),
  verifySafetyNumber: (contactId: number, verifiedFingerprint: string) =>
    request<any>(`/contacts/${contactId}/verify`, { method: "POST", body: JSON.stringify({ verified_fingerprint: verifiedFingerprint }) }),
  clearSafetyNumber: (contactId: number) => request<any>(`/contacts/${contactId}/verify`, { method: "DELETE" }),

  // Blocks
  getBlocks: () => request<any[]>("/blocks"),
  blockUser: (blockedId: number) => request<any>("/blocks", { method: "POST", body: JSON.stringify({ blocked_id: blockedId }) }),
  unblockUser: (userId: number) => request<any>(`/blocks/${userId}`, { method: "DELETE" }),

  // Uploads
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("signal_token");
    const response = await fetch(`${API_BASE}/uploads`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData
    });
    if (!response.ok) throw new Error("File upload failed");
    return await response.json();
  }
};
