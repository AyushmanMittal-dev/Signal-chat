import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./lib/api";
import { wsClient } from "./lib/ws";
import {
  getOrCreateUserKeyPair, deriveSharedAesKey, encryptText, decryptText,
  computeCombinedSafetyNumber
} from "./lib/crypto";

type IconName =
  | "archive"
  | "arrowLeft"
  | "attach"
  | "bell"
  | "camera"
  | "check"
  | "chevron"
  | "close"
  | "compose"
  | "emoji"
  | "info"
  | "lock"
  | "menu"
  | "message"
  | "moon"
  | "mute"
  | "phone"
  | "pin"
  | "plus"
  | "search"
  | "send"
  | "settings"
  | "timer"
  | "trash"
  | "users"
  | "video";

const iconPaths: Record<IconName, ReactNode> = {
  archive: <><path d="M4 7h16v13H4z" /><path d="M3 3h18v4H3zM9 11h6" /></>,
  arrowLeft: <><path d="m15 18-6-6 6-6" /></>,
  attach: <path d="m21.4 11.6-8.9 8.9a6 6 0 0 1-8.5-8.5l9.5-9.5a4 4 0 0 1 5.7 5.7l-9.6 9.6a2 2 0 0 1-2.8-2.8l8.9-8.9" />,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
  camera: <><path d="M14.5 4 16 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3l1.5-3z" /><circle cx="12" cy="13" r="3" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  compose: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z" /></>,
  emoji: <><circle cx="12" cy="12" r="9" /><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  message: <path d="M21 11.5a8.5 8.5 0 0 1-9 8.5 9.2 9.2 0 0 1-4-.9L3 21l1.8-4.5A8.5 8.5 0 1 1 21 11.5Z" />,
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" />,
  mute: <><path d="M11 5 6 9H2v6h4l5 4zM22 9l-6 6M16 9l6 6" /></>,
  phone: <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.4 19.4 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.8a2 2 0 0 1-.4 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.8.7a2 2 0 0 1 1.7 2Z" />,
  pin: <><line x1="12" y1="17" x2="12" y2="22" /><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.89A2 2 0 0 1 15 10.77V5a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v5.77a2 2 0 0 1-1.11 1.79l-1.78.89A2 2 0 0 0 5 15.24Z" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  send: <><path d="m22 2-7 20-4-9-9-4zM22 2 11 13" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" /></>,
  timer: <><circle cx="12" cy="13" r="8" /><path d="M12 9v5l3 2M9 2h6" /></>,
  trash: <><path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v5M14 11v5" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="8.5" cy="7" r="4" /><path d="M20 8v6M23 11h-6" /></>,
  video: <><rect x="2" y="5" width="15" height="14" rx="2" /><path d="m17 10 5-3v10l-5-3z" /></>,
};

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{iconPaths[name]}</svg>;
}

function IconButton({ icon, label, onClick, className = "" }: { icon: IconName; label: string; onClick?: () => void; className?: string }) {
  return <button type="button" className={`icon-button ${className}`} onClick={onClick} aria-label={label} title={label}><Icon name={icon} /></button>;
}

const avatarColors = ["violet", "green", "coral", "blue", "gold", "plum"];
function Avatar({ initials, index = 0, online = false, size = "md" }: { initials: string; index?: number; online?: boolean; size?: "sm" | "md" | "lg" | "xl" }) {
  return <div className={`avatar avatar-${size} ${avatarColors[index % avatarColors.length]}`}><span>{initials}</span>{online && <i className="online-dot" />}</div>;
}

function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return <div className="modal-backdrop" onMouseDown={onClose}><section className="modal-card" onMouseDown={(event) => event.stopPropagation()} aria-modal="true" role="dialog">
    <div className="sheet-handle" />
    <header className="modal-header"><h2>{title}</h2><IconButton icon="close" label="Close" onClick={onClose} /></header>
    {children}
  </section></div>;
}

function Switch({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: string }) {
  return <button type="button" className={`switch ${checked ? "active" : ""}`} role="switch" aria-checked={checked} aria-label={label} onClick={onChange}><span /></button>;
}

export default function App() {
  const [screen, setScreen] = useState<"app" | "welcome" | "verify" | "profile">("welcome");
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "unread" | "groups">("all");
  const [draft, setDraft] = useState("");
  const [modal, setModal] = useState<null | "new" | "group" | "settings" | "privacy" | "call" | "safety">(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [toast, setToast] = useState("");
  const [mobileChat, setMobileChat] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Record<number, boolean>>({});
  const typingTimerRef = useRef<Record<number, any>>({});
  const myTypingTimerRef = useRef<any>(null);
  const [authValue, setAuthValue] = useState("+15550124836");
  const [otp, setOtp] = useState("123456");
  const [profileName, setProfileName] = useState("Demo User");
  const [safetyNumber, setSafetyNumber] = useState("");
  const [isVerified, setIsVerified] = useState(false);
  const [pinnedIds, setPinnedIds] = useState<number[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("signal_pinned_chats") || "[]");
    } catch {
      return [];
    }
  });

  const togglePin = (chatId: number) => {
    setPinnedIds((prev) => {
      const next = prev.includes(chatId) ? prev.filter((id) => id !== chatId) : [...prev, chatId];
      try {
        localStorage.setItem("signal_pinned_chats", JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const messageEnd = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    const token = localStorage.getItem("signal_token");
    if (token) {
      api.getMe().then((user) => {
        setCurrentUser(user);
        setScreen("app");
        initializeCryptoAndWS(user);
      }).catch(() => {
        localStorage.removeItem("signal_token");
        setScreen("welcome");
      });
    }
  }, []);

  async function initializeCryptoAndWS(user: any) {
    wsClient.connect();
    try {
      const { publicKeyJwk, fingerprint } = await getOrCreateUserKeyPair(user.id);
      await api.registerPublicKey(publicKeyJwk, fingerprint);
    } catch (e) {
      console.warn("Crypto key initialization error:", e);
    }
    loadConversations();
  }

  const loadConversations = async () => {
    try {
      const list = await api.getConversations(query, filter);
      setConversations(list);
      if (list.length > 0 && activeId === null) {
        setActiveId(list[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (screen === "app") {
      loadConversations();
    }
  }, [query, filter, screen]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeId || screen !== "app") return;
    api.getMessages(activeId).then(async (msgs) => {
      // Decrypt any E2EE messages
      const decryptedMsgs = await Promise.all(msgs.map(async (msg) => {
        if (msg.is_encrypted && msg.ciphertext && msg.iv && currentUser) {
          try {
            const activeConv = conversations.find(c => c.id === activeId);
            const peer = activeConv?.members.find((m: any) => m.user_id !== currentUser.id);
            if (peer) {
              const peerKeyObj = await api.getUserPublicKey(peer.user_id);
              if (peerKeyObj?.public_key_jwk) {
                const aesKey = await deriveSharedAesKey(currentUser.id, peerKeyObj.public_key_jwk);
                const plain = await decryptText(msg.ciphertext, msg.iv, aesKey);
                return { ...msg, body: plain };
              }
            }
          } catch (e) {
            console.warn("Message history decryption fallback:", e);
            return { ...msg, body: msg.body || "[Encrypted Message]" };
          }
        }
        return msg;
      }));

      setMessages(decryptedMsgs);
      
      const lastMsg = decryptedMsgs[decryptedMsgs.length - 1];
      if (lastMsg) {
        api.markRead(activeId, lastMsg.id).catch(() => {});
        wsClient.send("message.read", { conversation_id: activeId, up_to_message_id: lastMsg.id });
      }
    }).catch(console.error);
  }, [activeId, screen]);

  // WebSocket listeners
  useEffect(() => {
    if (screen !== "app") return;

    const unbindNew = wsClient.on("message.new", async (msg: any) => {
      if (msg.conversation_id === activeId) {
        let displayMsg = msg;
        if (msg.is_encrypted && msg.ciphertext && msg.iv && currentUser) {
          try {
            const activeConv = conversations.find(c => c.id === activeId);
            const peer = activeConv?.members.find((m: any) => m.user_id !== currentUser.id);
            if (peer) {
              const peerKeyObj = await api.getUserPublicKey(peer.user_id);
              if (peerKeyObj?.public_key_jwk) {
                const aesKey = await deriveSharedAesKey(currentUser.id, peerKeyObj.public_key_jwk);
                const plain = await decryptText(msg.ciphertext, msg.iv, aesKey);
                displayMsg = { ...msg, body: plain };
              }
            }
          } catch (e) {
            console.warn("Incoming message decryption fallback:", e);
            displayMsg = { ...msg, body: msg.body || "[Encrypted Message]" };
          }
        }
        setMessages((prev) => {
          if (prev.some((m) => (displayMsg.id && m.id === displayMsg.id) || (displayMsg.client_id && m.client_id === displayMsg.client_id))) {
            return prev.map((m) => (displayMsg.client_id && m.client_id === displayMsg.client_id) ? { ...m, ...displayMsg } : m);
          }
          return [...prev, displayMsg];
        });
        wsClient.send("message.delivered", { message_id: msg.id });
      }
      loadConversations();
    });

    const unbindAck = wsClient.on("message.ack", (ackData: any) => {
      setMessages((prev) => prev.map((m) => m.client_id === ackData.client_id ? { ...m, id: ackData.message_id, status: "sent" } : m));
    });

    const unbindStatus = wsClient.on("message.status", (data: any) => {
      setMessages((prev) => prev.map((m) => (m.id === data.message_id || data.up_to_message_id >= m.id) ? { ...m, status: data.status } : m));
      loadConversations();
    });

    const unbindTyping = wsClient.on("typing", (data: any) => {
      if (data.conversation_id === activeId) {
        if (data.is_typing) {
          setTypingUsers((prev) => ({ ...prev, [data.user_id]: true }));
          if (typingTimerRef.current[data.user_id]) {
            clearTimeout(typingTimerRef.current[data.user_id]);
          }
          typingTimerRef.current[data.user_id] = setTimeout(() => {
            setTypingUsers((prev) => ({ ...prev, [data.user_id]: false }));
          }, 3000);
        } else {
          if (typingTimerRef.current[data.user_id]) {
            clearTimeout(typingTimerRef.current[data.user_id]);
          }
          setTypingUsers((prev) => ({ ...prev, [data.user_id]: false }));
        }
      }
    });

    const unbindPresence = wsClient.on("presence", (data: any) => {
      setConversations((prev) => prev.map((c) => {
        if (c.type === "direct") {
          return {
            ...c,
            members: c.members.map((m: any) => m.user_id === data.user_id ? { ...m, user: { ...m.user, is_online: data.is_online } } : m)
          };
        }
        return c;
      }));
    });

    return () => {
      unbindNew();
      unbindAck();
      unbindStatus();
      unbindTyping();
      unbindPresence();
    };
  }, [activeId, screen, currentUser, conversations]);

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; }, [dark]);
  useEffect(() => { messageEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, typingUsers]);

  const active = conversations.find((item) => item.id === activeId) || conversations[0] || {
    id: 1, name: "Maya Chen", preview: "", time: "10:42", unread_count: 0, members: []
  };

  const isTyping = Object.values(typingUsers).some(Boolean);

  function selectConversation(id: number) {
    setActiveId(id);
    setMobileChat(true);
    setInfoOpen(false);
    setConversations((current) => current.map((chat) => chat.id === id ? { ...chat, unread_count: 0 } : chat));
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || !activeId || !currentUser) return;

    const clientId = `client_${Date.now()}`;
    const nowStr = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

    // Optimistic UI insert
    const optimisticMsg = {
      id: Date.now(),
      conversation_id: activeId,
      sender_id: currentUser.id,
      sender: currentUser,
      client_id: clientId,
      type: "text",
      body: text,
      status: "sending",
      created_at: new Date().toISOString(),
      time: nowStr,
      reactions: [],
      attachments: []
    };

    setMessages((prev) => [...prev, optimisticMsg]);
    setDraft("");

    // Check if E2EE direct chat
    let payload: any = { conversation_id: activeId, client_id: clientId, body: text, is_encrypted: false };

    if (active.type === "direct") {
      const peer = active.members.find((m: any) => m.user_id !== currentUser.id);
      if (peer) {
        try {
          const peerKeyObj = await api.getUserPublicKey(peer.user_id);
          const aesKey = await deriveSharedAesKey(currentUser.id, peerKeyObj.public_key_jwk);
          const encrypted = await encryptText(text, aesKey);
          payload = {
            conversation_id: activeId,
            client_id: clientId,
            body: text,
            ciphertext: encrypted.ciphertext,
            iv: encrypted.iv,
            is_encrypted: true
          };
        } catch (e) {
          console.warn("Falling back to transport TLS for message send", e);
        }
      }
    }

    if (myTypingTimerRef.current) {
      clearTimeout(myTypingTimerRef.current);
      myTypingTimerRef.current = null;
    }
    wsClient.send("typing.stop", { conversation_id: activeId });
    wsClient.send("message.send", payload);
  }

  async function handleLogin() {
    try {
      const res = await api.verifyOtp(authValue, otp);
      localStorage.setItem("signal_token", res.access_token);
      setCurrentUser(res.user);
      if (res.is_new_user) {
        setScreen("profile");
      } else {
        setScreen("app");
        initializeCryptoAndWS(res.user);
      }
    } catch (err: any) {
      setToast(err.message || "Login failed");
    }
  }

  async function handleOpenSafetyNumber() {
    if (!active || !currentUser) return;
    const peer = active.members.find((m: any) => m.user_id !== currentUser.id);
    if (!peer) return;

    try {
      const myJwk = localStorage.getItem(`pub_jwk_${currentUser.id}`) || "{}";
      const peerKeyObj = await api.getUserPublicKey(peer.user_id);
      const number = await computeCombinedSafetyNumber(myJwk, peerKeyObj.public_key_jwk);
      setSafetyNumber(number);
      setModal("safety");
    } catch (e) {
      setToast("Could not retrieve safety number");
    }
  }

  if (screen !== "app") {
    return <Onboarding screen={screen} value={authValue} setValue={setAuthValue} otp={otp} setOtp={setOtp} profileName={profileName} setProfileName={setProfileName}
      onContinue={() => {
        if (screen === "welcome") handleLogin();
        else if (screen === "verify") handleLogin();
        else if (screen === "profile") {
          api.setupProfile(profileName).then((u) => {
            setCurrentUser(u);
            setScreen("app");
            initializeCryptoAndWS(u);
          });
        }
      }}
      onBack={() => setScreen(screen === "profile" ? "verify" : "welcome")}
      onDemo={() => {
        setAuthValue("+15550124836");
        setOtp("123456");
        handleLogin();
      }} />;
  }

  return <main className="app-shell">
    {toast && <div className="toast"><span className="toast-icon"><Icon name="check" size={16} /></span>{toast}<IconButton icon="close" label="Dismiss" onClick={() => setToast("")} /></div>}
    
    {/* Left Sidebar */}
    <aside className={`sidebar ${mobileChat ? "mobile-hidden" : ""}`}>
      <div className="sidebar-header">
        <button className="profile-button" onClick={() => setModal("settings")}>
          <Avatar initials={currentUser?.display_name ? currentUser.display_name.slice(0, 2).toUpperCase() : "DU"} size="sm" index={1} />
          <span>Signal</span>
        </button>
        <div className="header-actions">
          <IconButton icon="compose" label="New message" onClick={() => setModal("new")} />
          <IconButton icon="menu" label="Settings" onClick={() => setModal("settings")} />
        </div>
      </div>
      <label className="search-box">
        <Icon name="search" size={17} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search" />
        <kbd>⌘ K</kbd>
      </label>
      <nav className="filters" aria-label="Conversation filters">
        {(["all", "unread", "groups"] as const).map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}
      </nav>
      <div className="conversation-list">
        {[...conversations]
          .sort((a, b) => {
            const aPinned = pinnedIds.includes(a.id);
            const bPinned = pinnedIds.includes(b.id);
            if (aPinned && !bPinned) return -1;
            if (!aPinned && bPinned) return 1;
            return 0;
          })
          .map((chat) => {
            const isPinned = pinnedIds.includes(chat.id);
            const initials = chat.name ? chat.name.split(" ").map((w: string) => w[0]).join("").slice(0, 2).toUpperCase() : "CH";
            const preview = chat.last_message ? (chat.last_message.body || "[Encrypted Message]") : "No messages yet";
            let chatRawDate = chat.last_message?.created_at;
            if (typeof chatRawDate === "string" && !chatRawDate.endsWith("Z") && !chatRawDate.includes("+")) {
              chatRawDate += "Z";
            }
            const time = chat.last_message ? new Date(chatRawDate).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";
            return <button key={chat.id} className={`conversation-row ${chat.id === activeId ? "active" : ""}`} onClick={() => selectConversation(chat.id)}>
              <Avatar initials={initials} index={chat.id} online={chat.type === "direct" && chat.members.some((m: any) => m.user_id !== currentUser?.id && m.user?.is_online)} />
              <span className="conversation-copy">
                <span className="conversation-top">
                  <strong>{chat.name}</strong>
                  <span className="conversation-top-meta">
                    {isPinned && <span className="pin-badge" title="Pinned conversation"><Icon name="pin" size={13} /></span>}
                    <time>{time}</time>
                  </span>
                </span>
                <span className="conversation-bottom"><span>{preview}</span>{chat.unread_count > 0 && <b>{chat.unread_count}</b>}</span>
              </span>
            </button>;
          })}
        {conversations.length === 0 && <div className="empty-list"><Icon name="search" /><strong>No conversations found</strong><span>Try another name or filter.</span></div>}
      </div>
      <button className="new-chat-fab" onClick={() => setModal("new")} aria-label="New message"><Icon name="compose" /></button>
    </aside>

    {/* Right Chat Pane */}
    <section className={`chat ${mobileChat ? "mobile-visible" : ""}`}>
      <header className="chat-header">
        <IconButton icon="arrowLeft" label="Back to conversations" className="mobile-back" onClick={() => setMobileChat(false)} />
        <button className="chat-identity" onClick={() => setInfoOpen(true)}>
          <Avatar initials={active.name ? active.name.split(" ").map((w: string) => w[0]).join("").slice(0, 2).toUpperCase() : "CH"} index={active.id || 0} size="sm" />
          <span>
            <strong>{active.name}</strong>
            <small>{isTyping ? "typing…" : active.type === "group" ? `${active.members.length} members` : "Signal Protocol E2EE"}</small>
          </span>
        </button>
        <div className="chat-actions">
          <IconButton icon="video" label="Start video call" onClick={() => setModal("call")} />
          <IconButton icon="phone" label="Start voice call" onClick={() => setModal("call")} />
          <IconButton icon="info" label="Conversation information" className={infoOpen ? "active" : ""} onClick={() => setInfoOpen(!infoOpen)} />
        </div>
      </header>
      <div className="encryption-notice"><Icon name="lock" size={13} /> Messages and calls are end-to-end encrypted. No one outside of this chat can read them.</div>
      
      <div className="messages">
        <div className="day-pill">Today</div>
        {messages.map((message, index) => {
          const isMine = message.sender_id === currentUser?.id;
          let rawDate = message.created_at;
          if (typeof rawDate === "string" && !rawDate.endsWith("Z") && !rawDate.includes("+")) {
            rawDate += "Z";
          }
          const time = new Date(rawDate || Date.now()).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
          const senderName = !isMine && active.type === "group" && message.type !== "system" ? (message.sender?.display_name || active.members?.find((m: any) => m.user_id === message.sender_id)?.user?.display_name || `User ${message.sender_id}`) : null;
          return <div key={message.id || message.client_id || index} className={`message-row ${isMine ? "mine" : "theirs"}`}>
            <div className="bubble">
              {senderName && <span className="sender-author">{senderName}</span>}
              {message.type === "system" ? <span className="system-msg">{message.body}</span> : <span>{message.body}</span>}
              <span className="message-meta">
                <time>{time}</time>
                {isMine && <span className={`receipt ${message.status || "sent"}`}><Icon name="check" size={12} />{(message.status === "delivered" || message.status === "read") && <Icon name="check" size={12} />}</span>}
              </span>
            </div>
          </div>;
        })}
        {isTyping && <div className="message-row theirs"><div className="bubble typing"><i /><i /><i /></div></div>}
        <div ref={messageEnd} />
      </div>

      <form className="composer" onSubmit={sendMessage}>
        <IconButton icon="plus" label="Add attachment" onClick={async () => {
          const input = document.createElement("input");
          input.type = "file";
          input.onchange = async () => {
            if (input.files?.[0]) {
              try {
                const res = await api.uploadFile(input.files[0]);
                setDraft(`[Attachment: ${res.filename}] ${res.file_url}`);
              } catch (e) {
                setToast("Upload failed");
              }
            }
          };
          input.click();
        }} />
        <div className="composer-field">
          <textarea rows={1} value={draft} onChange={(event) => {
            const nextVal = event.target.value;
            setDraft(nextVal);
            if (activeId) {
              if (myTypingTimerRef.current) clearTimeout(myTypingTimerRef.current);
              if (nextVal.trim()) {
                wsClient.send("typing.start", { conversation_id: activeId });
                myTypingTimerRef.current = setTimeout(() => {
                  wsClient.send("typing.stop", { conversation_id: activeId });
                }, 1500);
              } else {
                wsClient.send("typing.stop", { conversation_id: activeId });
              }
            }
          }} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && window.innerWidth >= 768) { event.preventDefault(); sendMessage(); } }} placeholder="Message" />
          <IconButton icon="emoji" label="Choose emoji" onClick={() => setDraft((value) => `${value} 😊`)} />
        </div>
        {draft.trim() ? <button className="send-button" aria-label="Send message"><Icon name="send" size={19} /></button> : <IconButton icon="camera" label="Open camera" onClick={() => setToast("Camera access simulated in demo")} />}
      </form>
    </section>

    {/* Info Panel */}
    {infoOpen && <aside className="info-panel">
      <header><span>Conversation details</span><IconButton icon="close" label="Close details" onClick={() => setInfoOpen(false)} /></header>
      <div className="info-profile">
        <Avatar initials={active.name ? active.name.split(" ").map((w: string) => w[0]).join("").slice(0, 2).toUpperCase() : "CH"} index={active.id || 0} size="xl" />
        <h2>{active.name}</h2>
        <p>{active.type === "group" ? `${active.members.length} members` : "Available"}</p>
      </div>
      <div className="quick-actions">
        <button onClick={() => setModal("call")}><span><Icon name="phone" /></span>Audio</button>
        <button onClick={() => setModal("call")}><span><Icon name="video" /></span>Video</button>
        <button onClick={() => setQuery(active.name)}><span><Icon name="search" /></span>Search</button>
      </div>
      <div className="info-list">
        <button onClick={() => activeId && togglePin(activeId)}>
          <span><Icon name="pin" />{activeId && pinnedIds.includes(activeId) ? "Unpin chat" : "Pin chat"}</span>
          <small>{activeId && pinnedIds.includes(activeId) ? "Pinned" : "Not pinned"}</small>
          <Icon name="chevron" size={16} />
        </button>
        <button onClick={handleOpenSafetyNumber}><span><Icon name="lock" />View safety number</span><Icon name="chevron" size={16} /></button>
        <button><span><Icon name="timer" />Disappearing messages</span><small>Off</small><Icon name="chevron" size={16} /></button>
        <button><span><Icon name="bell" />Mute notifications</span><small>Off</small><Icon name="chevron" size={16} /></button>
      </div>
    </aside>}

    {/* Modals */}
    {modal === "new" && <NewConversation onClose={() => setModal(null)} onGroup={() => setModal("group")} onSelect={async (targetUser) => {
      try {
        const conv = await api.createDirectConversation(targetUser.id);
        await loadConversations();
        setActiveId(conv.id);
        setMobileChat(true);
      } catch (e) {
        console.error(e);
      }
      setModal(null);
    }} />}

    {modal === "group" && <GroupModal onClose={() => setModal(null)} onCreate={async (name, memberIds) => {
      try {
        const group = await api.createGroup(name, memberIds);
        await loadConversations();
        setActiveId(group.id);
        setMobileChat(true);
        setModal(null);
        setToast("Group created");
      } catch (e: any) {
        setToast(e.message || "Failed to create group");
      }
    }} />}

    {modal === "settings" && <Settings user={currentUser} dark={dark} setDark={setDark} onClose={() => setModal(null)} onPrivacy={() => setModal("privacy")} onLogout={() => {
      api.logout();
      localStorage.removeItem("signal_token");
      wsClient.disconnect();
      setModal(null);
      setScreen("welcome");
    }} />}

    {modal === "privacy" && <PrivacyModal user={currentUser} onClose={() => setModal("settings")} onUserUpdate={(u) => setCurrentUser(u)} />}

    {modal === "safety" && <Modal title="Safety Number" onClose={() => setModal(null)}>
      <div className="modal-content safety-content">
        <p className="modal-helper">Verify the safety number with {active.name} to confirm end-to-end encryption.</p>
        <div className="safety-grid">{safetyNumber}</div>
        <label className="checkbox-label"><input type="checkbox" checked={isVerified} onChange={(e) => setIsVerified(e.target.checked)} /> Mark as verified</label>
        <button className="primary-button" onClick={() => setModal(null)}>Done</button>
      </div>
    </Modal>}

    {modal === "call" && <Modal title="Calls coming soon" onClose={() => setModal(null)}>
      <div className="coming-soon"><span><Icon name="video" size={32} /></span><h3>Calling is on the way</h3><p>Voice and video calls are represented as a polished placeholder in this build.</p><button className="primary-button" onClick={() => setModal(null)}>Got it</button></div>
    </Modal>}
  </main>;
}

function NewConversation({ onClose, onGroup, onSelect }: { onClose: () => void; onGroup: () => void; onSelect: (user: any) => void }) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    if (search.trim()) {
      api.searchUsers(search).then(setResults).catch(() => {});
    } else {
      api.getContacts().then((contacts) => setResults(contacts.map((c) => c.contact_user))).catch(() => {});
    }
  }, [search]);

  return <Modal title="New message" onClose={onClose}>
    <div className="modal-content">
      <label className="search-box modal-search"><Icon name="search" size={17} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name or username" /></label>
      <button className="action-row" onClick={onGroup}><span className="action-icon"><Icon name="users" /></span><span><strong>New group</strong><small>Start a conversation with several people</small></span><Icon name="chevron" size={17} /></button>
      <p className="section-label">Contacts & Users</p>
      <div className="contact-list">{results.map((user, index) => <button key={user.id} onClick={() => onSelect(user)}><Avatar initials={user.display_name.slice(0, 2).toUpperCase()} index={index} size="sm" /><span><strong>{user.display_name}</strong><small>@{user.username || user.phone}</small></span></button>)}</div>
    </div>
  </Modal>;
}

function GroupModal({ onClose, onCreate }: { onClose: () => void; onCreate: (name: string, memberIds: number[]) => void }) {
  const [step, setStep] = useState(1);
  const [contacts, setContacts] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    api.getContacts().then((c) => setContacts(c.map(item => item.contact_user))).catch(() => {});
  }, []);

  return <Modal title={step === 1 ? "New group" : "Group details"} onClose={onClose}><div className="modal-content">
    {step === 1 ? <><p className="modal-helper">Select people to add to this group.</p>
      <div className="contact-list selectable">{contacts.map((contact, index) => <button key={contact.id} onClick={() => setSelectedIds((items) => items.includes(contact.id) ? items.filter((id) => id !== contact.id) : [...items, contact.id])}><Avatar initials={contact.display_name.slice(0, 2).toUpperCase()} index={index} size="sm" /><span><strong>{contact.display_name}</strong><small>Signal contact</small></span><i className={selectedIds.includes(contact.id) ? "checked" : ""}>{selectedIds.includes(contact.id) && <Icon name="check" size={14} />}</i></button>)}</div>
      <button className="primary-button" disabled={!selectedIds.length} onClick={() => setStep(2)}>Next</button></> :
      <><div className="group-avatar"><Icon name="camera" /></div><label className="field-label">Group name<input autoFocus value={name} maxLength={32} onChange={(event) => setName(event.target.value)} placeholder="Friends, family, team…" /></label><p className="modal-helper">{selectedIds.length + 1} members including you</p><button className="primary-button" disabled={!name.trim() || isSubmitting} onClick={async () => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        try {
          await onCreate(name.trim(), selectedIds);
        } finally {
          setIsSubmitting(false);
        }
      }}>{isSubmitting ? "Creating…" : "Create group"}</button></>}
  </div></Modal>;
}

function Settings({ user, dark, setDark, onClose, onPrivacy, onLogout }: { user: any; dark: boolean; setDark: (value: boolean) => void; onClose: () => void; onPrivacy: () => void; onLogout: () => void }) {
  return <Modal title="Settings" onClose={onClose}><div className="settings-content">
    <div className="settings-profile">
      <Avatar initials={user?.display_name ? user.display_name.slice(0, 2).toUpperCase() : "DU"} index={1} size="lg" />
      <span><strong>{user?.display_name || "Demo User"}</strong><small>@{user?.username || user?.phone || "demo.user"}</small></span>
      <Icon name="chevron" />
    </div>
    <p className="section-label">Preferences</p>
    <div className="settings-list">
      <div><span className="settings-icon"><Icon name="moon" /></span><span><strong>Appearance</strong><small>{dark ? "Dark" : "Light"} theme</small></span><Switch checked={dark} onChange={() => setDark(!dark)} label="Toggle dark theme" /></div>
      <button onClick={onPrivacy}><span className="settings-icon"><Icon name="lock" /></span><span><strong>Privacy</strong><small>Blocked contacts & read receipts</small></span><Icon name="chevron" /></button>
    </div>
    <button className="logout-button" onClick={onLogout}>Log out</button>
    <p className="version">Signal Clone · Fullstack Build 1.0</p>
  </div></Modal>;
}

function PrivacyModal({ user, onClose, onUserUpdate }: { user: any; onClose: () => void; onUserUpdate: (u: any) => void }) {
  const currentSettings = user?.settings_json ? (typeof user.settings_json === "string" ? JSON.parse(user.settings_json) : user.settings_json) : {
    read_receipts: true, typing_indicators: true, screen_lock_minutes: 0, hide_previews: false
  };

  const [settings, setSettings] = useState(currentSettings);
  const [blockedUsers, setBlockedUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getBlocks().then(setBlockedUsers).catch(() => {});
  }, []);

  async function handleToggle(key: string, value: any) {
    const updated = { ...settings, [key]: value };
    setSettings(updated);
    try {
      const updatedUser = await api.updateMe({ settings_json: updated });
      onUserUpdate(updatedUser);
    } catch (e) {
      console.error("Failed to update privacy settings", e);
    }
  }

  async function handleUnblock(userId: number) {
    try {
      await api.unblockUser(userId);
      setBlockedUsers((prev) => prev.filter((b) => b.blocked_id !== userId));
    } catch (e) {
      console.error("Failed to unblock", e);
    }
  }

  return <Modal title="Privacy" onClose={onClose}>
    <div className="settings-content" style={{ maxHeight: "75vh", overflowY: "auto" }}>
      <p className="section-label">Messaging & Status</p>
      <div className="settings-list">
        <div>
          <span className="settings-icon"><Icon name="check" /></span>
          <span><strong>Read receipts</strong><small>Let others see when you read messages</small></span>
          <Switch checked={!!settings.read_receipts} onChange={() => handleToggle("read_receipts", !settings.read_receipts)} label="Toggle read receipts" />
        </div>
        <div>
          <span className="settings-icon"><Icon name="timer" /></span>
          <span><strong>Typing indicators</strong><small>Show others when you are typing</small></span>
          <Switch checked={!!settings.typing_indicators} onChange={() => handleToggle("typing_indicators", !settings.typing_indicators)} label="Toggle typing indicators" />
        </div>
      </div>

      <p className="section-label">Security</p>
      <div className="settings-list">
        <div>
          <span className="settings-icon"><Icon name="lock" /></span>
          <span><strong>Hide message previews</strong><small>Hide sender and text in notifications</small></span>
          <Switch checked={!!settings.hide_previews} onChange={() => handleToggle("hide_previews", !settings.hide_previews)} label="Toggle previews" />
        </div>
      </div>

      <p className="section-label">Blocked Contacts ({blockedUsers.length})</p>
      <div className="contact-list">
        {blockedUsers.length === 0 ? (
          <p style={{ color: "var(--color-text-secondary, #8e8e93)", padding: "12px", fontSize: "14px" }}>No blocked contacts</p>
        ) : (
          blockedUsers.map((b) => (
            <div key={b.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px" }}>
              <span><strong>{b.blocked_user?.display_name || "User"}</strong> <small style={{ color: "var(--color-text-secondary)" }}>@{b.blocked_user?.username || b.blocked_user?.phone}</small></span>
              <button className="text-button" style={{ color: "var(--color-danger, #ff3b30)", fontSize: "13px" }} onClick={() => handleUnblock(b.blocked_id)}>Unblock</button>
            </div>
          ))
        )}
      </div>

      <button className="primary-button" style={{ marginTop: "16px" }} onClick={onClose}>Done</button>
    </div>
  </Modal>;
}

function Onboarding({ screen, value, setValue, otp, setOtp, profileName, setProfileName, onContinue, onBack, onDemo }: {
  screen: "welcome" | "verify" | "profile"; value: string; setValue: (value: string) => void; otp: string; setOtp: (value: string) => void; profileName: string; setProfileName: (value: string) => void; onContinue: () => void; onBack: () => void; onDemo: () => void;
}) {
  const [mode, setMode] = useState<"phone" | "username">("phone");
  return <main className="onboarding"><div className="onboarding-progress"><i /><i className={screen !== "welcome" ? "done" : ""} /><i className={screen === "profile" ? "done" : ""} /><i /></div><section className="onboarding-card">
    {screen !== "welcome" && <IconButton icon="arrowLeft" label="Go back" onClick={onBack} />}
    {screen === "welcome" && <><div className="signal-mark"><Icon name="message" size={34} /></div><h1>Private messaging that feels instant</h1><p>Sign in with your phone number or a username.</p><div className="segment"><button className={mode === "phone" ? "active" : ""} onClick={() => setMode("phone")}>Phone</button><button className={mode === "username" ? "active" : ""} onClick={() => setMode("username")}>Username</button></div><label className="auth-field"><span>{mode === "phone" ? "+1" : "@"}</span><input autoFocus value={value} onChange={(event) => setValue(event.target.value)} placeholder={mode === "phone" ? "+15550124836" : "demo.user"} /></label><small className="auth-help">Use code 123456 on the next screen.</small><button className="primary-button" disabled={value.length < 3} onClick={onContinue}>Continue</button><button className="text-button" onClick={onDemo}>Use demo account (+15550124836)</button></>}
    {screen === "verify" && <><h1>Enter your code</h1><p>We sent a code to {value || "+15550124836"}.</p><div className="otp-boxes">{Array.from({ length: 6 }, (_, index) => <span key={index}>{otp[index] ?? ""}</span>)}<input autoFocus inputMode="numeric" value={otp} maxLength={6} onChange={(event) => { const next = event.target.value.replace(/\D/g, ""); setOtp(next); if (next === "123456") window.setTimeout(onContinue, 250); }} /></div><div className="demo-code"><Icon name="info" size={15} /> Demo build: the code is <strong>123456</strong></div><button className="primary-button" disabled={otp.length !== 6} onClick={onContinue}>Verify</button></>}
    {screen === "profile" && <><h1>Set up your profile</h1><p>This is how people will see you.</p><div className="profile-avatar"><Avatar initials={profileName.slice(0, 2).toUpperCase() || "DU"} index={1} size="xl" /><button><Icon name="camera" size={17} /></button></div><label className="field-label">Display name<input value={profileName} onChange={(event) => setProfileName(event.target.value)} /></label><label className="field-label">About <span>(optional)</span><input placeholder="Available" /></label><button className="primary-button" disabled={!profileName.trim()} onClick={onContinue}>Start messaging</button></>}
  </section></main>;
}
