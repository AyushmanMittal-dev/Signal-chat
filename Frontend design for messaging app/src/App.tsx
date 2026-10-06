import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";

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

type Message = { id: number; text: string; mine: boolean; time: string; status?: "sent" | "delivered" | "read"; reply?: string; reaction?: string };
type Conversation = { id: number; name: string; initials: string; preview: string; time: string; unread: number; online?: boolean; muted?: boolean; group?: boolean; archived?: boolean; color: number; messages: Message[] };

const seedConversations: Conversation[] = [
  { id: 1, name: "Maya Chen", initials: "MC", preview: "Perfect, see you then!", time: "10:42", unread: 2, online: true, color: 0, messages: [
    { id: 1, text: "Hey! Are we still on for lunch today?", mine: false, time: "10:34" },
    { id: 2, text: "Absolutely. How does 12:30 sound?", mine: true, time: "10:36", status: "read" },
    { id: 3, text: "Perfect. The little Italian place near the park?", mine: false, time: "10:38" },
    { id: 4, text: "Yes! I booked us a table by the window.", mine: true, time: "10:39", status: "read", reaction: "♥" },
    { id: 5, text: "Perfect, see you then!", mine: false, time: "10:42" },
  ]},
  { id: 2, name: "Weekend Hikers", initials: "WH", preview: "Daniel: I’ll bring extra water", time: "9:18", unread: 5, group: true, color: 1, messages: [
    { id: 1, text: "Saturday looks clear. Shall we meet at the north trailhead?", mine: false, time: "9:02" },
    { id: 2, text: "Works for me. 8am?", mine: true, time: "9:05", status: "read" },
    { id: 3, text: "I’ll bring extra water for everyone.", mine: false, time: "9:18" },
  ]},
  { id: 3, name: "Noah Williams", initials: "NW", preview: "You: Sent a photo", time: "Yesterday", unread: 0, color: 2, messages: [
    { id: 1, text: "This view is unreal.", mine: true, time: "18:11", status: "read" },
    { id: 2, text: "You made it! Send more photos when you can.", mine: false, time: "18:13" },
  ]},
  { id: 4, name: "Product team", initials: "PT", preview: "Ava: Updated the project notes", time: "Yesterday", unread: 0, muted: true, group: true, color: 3, messages: [
    { id: 1, text: "I updated the project notes with today’s decisions.", mine: false, time: "16:24" },
    { id: 2, text: "Thanks, I’ll review them this evening.", mine: true, time: "16:30", status: "delivered" },
  ]},
  { id: 5, name: "Sofia Rodriguez", initials: "SR", preview: "That sounds amazing!", time: "Mon", unread: 0, online: true, color: 4, messages: [
    { id: 1, text: "We should try the new exhibit this weekend.", mine: true, time: "14:02", status: "read" },
    { id: 2, text: "That sounds amazing!", mine: false, time: "14:07" },
  ]},
  { id: 6, name: "Note to Self", initials: "NS", preview: "Passport renewal reminder", time: "Sun", unread: 0, color: 5, messages: [
    { id: 1, text: "Passport renewal reminder — submit the form before Friday.", mine: true, time: "11:20", status: "sent" },
  ]},
];

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
  const [screen, setScreen] = useState<"app" | "welcome" | "verify" | "profile">("app");
  const [conversations, setConversations] = useState(seedConversations);
  const [activeId, setActiveId] = useState(1);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "unread" | "groups">("all");
  const [draft, setDraft] = useState("");
  const [modal, setModal] = useState<null | "new" | "group" | "settings" | "call">(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [toast, setToast] = useState("");
  const [mobileChat, setMobileChat] = useState(false);
  const [typing, setTyping] = useState(false);
  const [authValue, setAuthValue] = useState("");
  const [otp, setOtp] = useState("");
  const [profileName, setProfileName] = useState("Demo User");
  const messageEnd = useRef<HTMLDivElement>(null);

  const active = conversations.find((item) => item.id === activeId) ?? conversations[0];
  const visible = useMemo(() => conversations.filter((item) => {
    const matches = `${item.name} ${item.preview}`.toLowerCase().includes(query.toLowerCase());
    return matches && (filter === "all" || (filter === "unread" && item.unread > 0) || (filter === "groups" && item.group));
  }), [conversations, query, filter]);

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; }, [dark]);
  useEffect(() => { messageEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [activeId, conversations, typing]);
  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(""), 3500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  function selectConversation(id: number) {
    setActiveId(id);
    setMobileChat(true);
    setInfoOpen(false);
    setConversations((current) => current.map((chat) => chat.id === id ? { ...chat, unread: 0 } : chat));
  }

  function sendMessage(event?: FormEvent) {
    event?.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const now = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    setDraft("");
    setConversations((current) => current.map((chat) => chat.id === activeId ? {
      ...chat, preview: `You: ${text}`, time: "Now",
      messages: [...chat.messages, { id: Date.now(), text, mine: true, time: now, status: "sent" }],
    } : chat));
    window.setTimeout(() => setConversations((current) => current.map((chat) => chat.id === activeId ? { ...chat, messages: chat.messages.map((message) => message.text === text ? { ...message, status: "read" } : message) } : chat)), 800);
    if (active.id === 1) {
      window.setTimeout(() => setTyping(true), 900);
      window.setTimeout(() => {
        setTyping(false);
        setConversations((current) => current.map((chat) => chat.id === activeId ? {
          ...chat, preview: "Sounds good!", time: "Now",
          messages: [...chat.messages, { id: Date.now() + 1, text: "Sounds good! I’ll see you soon.", mine: false, time: now }],
        } : chat));
      }, 2700);
    }
  }

  if (screen !== "app") {
    return <Onboarding screen={screen} value={authValue} setValue={setAuthValue} otp={otp} setOtp={setOtp} profileName={profileName} setProfileName={setProfileName}
      onContinue={() => setScreen(screen === "welcome" ? "verify" : screen === "verify" ? "profile" : "app")}
      onBack={() => setScreen(screen === "profile" ? "verify" : "welcome")} onDemo={() => setScreen("app")} />;
  }

  return <main className="app-shell">
    {toast && <div className="toast"><span className="toast-icon"><Icon name="check" size={16} /></span>{toast}<IconButton icon="close" label="Dismiss" onClick={() => setToast("")} /></div>}
    <aside className={`sidebar ${mobileChat ? "mobile-hidden" : ""}`}>
      <div className="sidebar-header">
        <button className="profile-button" onClick={() => setModal("settings")}><Avatar initials="DU" size="sm" index={1} /><span>Signal</span></button>
        <div className="header-actions"><IconButton icon="compose" label="New message" onClick={() => setModal("new")} /><IconButton icon="menu" label="Settings" onClick={() => setModal("settings")} /></div>
      </div>
      <label className="search-box"><Icon name="search" size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search" /><kbd>⌘ K</kbd></label>
      <nav className="filters" aria-label="Conversation filters">
        {(["all", "unread", "groups"] as const).map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}
      </nav>
      <div className="conversation-list">
        {visible.map((chat) => <button key={chat.id} className={`conversation-row ${chat.id === activeId ? "active" : ""}`} onClick={() => selectConversation(chat.id)}>
          <Avatar initials={chat.initials} index={chat.color} online={chat.online} />
          <span className="conversation-copy">
            <span className="conversation-top"><strong>{chat.name}</strong><time>{chat.time}</time></span>
            <span className="conversation-bottom"><span>{chat.preview}</span>{chat.muted && <Icon name="mute" size={14} />}{chat.unread > 0 && <b>{chat.unread}</b>}</span>
          </span>
        </button>)}
        {visible.length === 0 && <div className="empty-list"><Icon name="search" /><strong>No conversations found</strong><span>Try another name or filter.</span></div>}
      </div>
      <button className="new-chat-fab" onClick={() => setModal("new")} aria-label="New message"><Icon name="compose" /></button>
    </aside>

    <section className={`chat ${mobileChat ? "mobile-visible" : ""}`}>
      <header className="chat-header">
        <IconButton icon="arrowLeft" label="Back to conversations" className="mobile-back" onClick={() => setMobileChat(false)} />
        <button className="chat-identity" onClick={() => setInfoOpen(true)}><Avatar initials={active.initials} index={active.color} size="sm" online={active.online} /><span><strong>{active.name}</strong><small>{typing ? "typing…" : active.group ? "5 members" : active.online ? "Online" : "Last seen recently"}</small></span></button>
        <div className="chat-actions">
          <IconButton icon="video" label="Start video call" onClick={() => setModal("call")} />
          <IconButton icon="phone" label="Start voice call" onClick={() => setModal("call")} />
          <IconButton icon="info" label="Conversation information" className={infoOpen ? "active" : ""} onClick={() => setInfoOpen(!infoOpen)} />
        </div>
      </header>
      <div className="encryption-notice"><Icon name="lock" size={13} /> Messages and calls are end-to-end encrypted. No one outside of this chat can read them.</div>
      <div className="messages">
        <div className="day-pill">Today</div>
        {active.messages.map((message, index) => {
          const previous = active.messages[index - 1];
          const clustered = previous?.mine === message.mine;
          return <div key={message.id} className={`message-row ${message.mine ? "mine" : "theirs"} ${clustered ? "clustered" : ""}`}>
            <div className="bubble">
              {message.reply && <span className="reply-preview">{message.reply}</span>}
              <span>{message.text}</span>
              <span className="message-meta"><time>{message.time}</time>{message.mine && <span className={`receipt ${message.status}`}><Icon name="check" size={12} />{message.status !== "sent" && <Icon name="check" size={12} />}</span>}</span>
              {message.reaction && <span className="reaction">{message.reaction}</span>}
              <span className="message-actions"><button title="React">♡</button><button title="Reply">↩</button><button title="More">•••</button></span>
            </div>
          </div>;
        })}
        {typing && <div className="message-row theirs"><div className="bubble typing"><i /><i /><i /></div></div>}
        <div ref={messageEnd} />
      </div>
      <form className="composer" onSubmit={sendMessage}>
        <IconButton icon="plus" label="Add attachment" onClick={() => setToast("Attachments are available in the full Signal app")} />
        <div className="composer-field"><textarea rows={1} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && window.innerWidth >= 768) { event.preventDefault(); sendMessage(); } }} placeholder="Message" /><IconButton icon="emoji" label="Choose emoji" onClick={() => setDraft((value) => `${value} 😊`)} /></div>
        {draft.trim() ? <button className="send-button" aria-label="Send message"><Icon name="send" size={19} /></button> : <IconButton icon="camera" label="Open camera" onClick={() => setToast("Camera access is not available in this demo")} />}
      </form>
    </section>

    {infoOpen && <aside className="info-panel">
      <header><span>Conversation details</span><IconButton icon="close" label="Close details" onClick={() => setInfoOpen(false)} /></header>
      <div className="info-profile"><Avatar initials={active.initials} index={active.color} size="xl" /><h2>{active.name}</h2><p>{active.group ? "5 members" : active.online ? "Online" : "Last seen recently"}</p></div>
      <div className="quick-actions"><button onClick={() => setModal("call")}><span><Icon name="phone" /></span>Audio</button><button onClick={() => setModal("call")}><span><Icon name="video" /></span>Video</button><button onClick={() => setQuery(active.name)}><span><Icon name="search" /></span>Search</button></div>
      <div className="info-list">
        <button><span><Icon name="timer" />Disappearing messages</span><small>Off</small><Icon name="chevron" size={16} /></button>
        <button><span><Icon name="bell" />Mute notifications</span><small>Off</small><Icon name="chevron" size={16} /></button>
        {active.group && <button><span><Icon name="users" />Group members</span><small>5</small><Icon name="chevron" size={16} /></button>}
        <button><span><Icon name="lock" />View safety number</span><Icon name="chevron" size={16} /></button>
      </div>
      <div className="info-list danger-list">
        <button onClick={() => setToast(`${active.name} was blocked`)}>Block</button>
        <button onClick={() => { setConversations((items) => items.filter((item) => item.id !== active.id)); setActiveId(conversations.find((item) => item.id !== active.id)?.id ?? 1); setInfoOpen(false); }}>Delete conversation</button>
      </div>
    </aside>}

    {modal === "new" && <NewConversation onClose={() => setModal(null)} onGroup={() => setModal("group")} onSelect={(name, initials, color) => {
      const existing = conversations.find((item) => item.name === name);
      if (existing) selectConversation(existing.id);
      else {
        const id = Date.now();
        setConversations((items) => [{ id, name, initials, color, preview: "New conversation", time: "Now", unread: 0, messages: [] }, ...items]);
        setActiveId(id); setMobileChat(true);
      }
      setModal(null);
    }} />}
    {modal === "group" && <GroupModal onClose={() => setModal(null)} onCreate={(name) => {
      const id = Date.now();
      setConversations((items) => [{ id, name, initials: name.split(" ").map((word) => word[0]).join("").slice(0, 2).toUpperCase(), color: 3, group: true, preview: "You created this group", time: "Now", unread: 0, messages: [{ id: 1, text: `You created “${name}”`, mine: true, time: "Now", status: "sent" }] }, ...items]);
      setActiveId(id); setMobileChat(true); setModal(null); setToast("Group created");
    }} />}
    {modal === "settings" && <Settings dark={dark} setDark={setDark} onClose={() => setModal(null)} onLogout={() => { setModal(null); setScreen("welcome"); }} />}
    {modal === "call" && <Modal title="Calls coming soon" onClose={() => setModal(null)}><div className="coming-soon"><span><Icon name="video" size={32} /></span><h3>Calling is on the way</h3><p>Voice and video calls are represented as a polished placeholder in this demo.</p><button className="primary-button" onClick={() => setModal(null)}>Got it</button></div></Modal>}
  </main>;
}

function NewConversation({ onClose, onGroup, onSelect }: { onClose: () => void; onGroup: () => void; onSelect: (name: string, initials: string, color: number) => void }) {
  const [search, setSearch] = useState("");
  const contacts = [
    ["Maya Chen", "MC"], ["Noah Williams", "NW"], ["Sofia Rodriguez", "SR"], ["Ava Thompson", "AT"], ["Daniel Kim", "DK"], ["Leila Hassan", "LH"],
  ];
  return <Modal title="New message" onClose={onClose}>
    <div className="modal-content">
      <label className="search-box modal-search"><Icon name="search" size={17} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name or username" /></label>
      <button className="action-row" onClick={onGroup}><span className="action-icon"><Icon name="users" /></span><span><strong>New group</strong><small>Start a conversation with several people</small></span><Icon name="chevron" size={17} /></button>
      <button className="action-row" onClick={() => onSelect(search || "New Contact", (search || "NC").slice(0, 2).toUpperCase(), 4)}><span className="action-icon"><Icon name="plus" /></span><span><strong>Add contact</strong><small>Connect using a Signal username</small></span><Icon name="chevron" size={17} /></button>
      <p className="section-label">Contacts</p>
      <div className="contact-list">{contacts.filter(([name]) => name.toLowerCase().includes(search.toLowerCase())).map(([name, initials], index) => <button key={name} onClick={() => onSelect(name, initials, index)}><Avatar initials={initials} index={index} size="sm" /><span><strong>{name}</strong><small>@{name.toLowerCase().replace(" ", ".")}</small></span></button>)}</div>
    </div>
  </Modal>;
}

function GroupModal({ onClose, onCreate }: { onClose: () => void; onCreate: (name: string) => void }) {
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState(["Maya Chen", "Noah Williams"]);
  const [name, setName] = useState("");
  const contacts = ["Maya Chen", "Noah Williams", "Sofia Rodriguez", "Ava Thompson"];
  return <Modal title={step === 1 ? "New group" : "Group details"} onClose={onClose}><div className="modal-content">
    {step === 1 ? <><p className="modal-helper">Select people to add to this group.</p><div className="selected-chips">{selected.map((item) => <button key={item} onClick={() => setSelected((items) => items.filter((value) => value !== item))}>{item}<Icon name="close" size={13} /></button>)}</div><div className="contact-list selectable">{contacts.map((contact, index) => <button key={contact} onClick={() => setSelected((items) => items.includes(contact) ? items.filter((item) => item !== contact) : [...items, contact])}><Avatar initials={contact.split(" ").map((item) => item[0]).join("")} index={index} size="sm" /><span><strong>{contact}</strong><small>Signal contact</small></span><i className={selected.includes(contact) ? "checked" : ""}>{selected.includes(contact) && <Icon name="check" size={14} />}</i></button>)}</div><button className="primary-button" disabled={!selected.length} onClick={() => setStep(2)}>Next</button></> :
      <><div className="group-avatar"><Icon name="camera" /></div><label className="field-label">Group name<input autoFocus value={name} maxLength={32} onChange={(event) => setName(event.target.value)} placeholder="Friends, family, team…" /></label><p className="modal-helper">{selected.length + 1} members including you</p><button className="primary-button" disabled={!name.trim()} onClick={() => onCreate(name.trim())}>Create group</button></>}
  </div></Modal>;
}

function Settings({ dark, setDark, onClose, onLogout }: { dark: boolean; setDark: (value: boolean) => void; onClose: () => void; onLogout: () => void }) {
  const [notifications, setNotifications] = useState(true);
  return <Modal title="Settings" onClose={onClose}><div className="settings-content">
    <div className="settings-profile"><Avatar initials="DU" index={1} size="lg" /><span><strong>Demo User</strong><small>@demo.user</small></span><Icon name="chevron" /></div>
    <p className="section-label">Preferences</p>
    <div className="settings-list">
      <div><span className="settings-icon"><Icon name="moon" /></span><span><strong>Appearance</strong><small>{dark ? "Dark" : "Light"} theme</small></span><Switch checked={dark} onChange={() => setDark(!dark)} label="Toggle dark theme" /></div>
      <div><span className="settings-icon"><Icon name="bell" /></span><span><strong>Notifications</strong><small>Message and call alerts</small></span><Switch checked={notifications} onChange={() => setNotifications(!notifications)} label="Toggle notifications" /></div>
      <button onClick={() => { onClose(); }}><span className="settings-icon"><Icon name="lock" /></span><span><strong>Privacy</strong><small>Blocked contacts and read receipts</small></span><Icon name="chevron" /></button>
      <button onClick={() => { onClose(); }}><span className="settings-icon"><Icon name="archive" /></span><span><strong>Linked devices</strong><small>Coming soon</small></span><Icon name="chevron" /></button>
    </div>
    <button className="logout-button" onClick={onLogout}>Log out</button><p className="version">Signal Clone · Demo build 1.0</p>
  </div></Modal>;
}

function Onboarding({ screen, value, setValue, otp, setOtp, profileName, setProfileName, onContinue, onBack, onDemo }: {
  screen: "welcome" | "verify" | "profile"; value: string; setValue: (value: string) => void; otp: string; setOtp: (value: string) => void; profileName: string; setProfileName: (value: string) => void; onContinue: () => void; onBack: () => void; onDemo: () => void;
}) {
  const [mode, setMode] = useState<"phone" | "username">("phone");
  return <main className="onboarding"><div className="onboarding-progress"><i /><i className={screen !== "welcome" ? "done" : ""} /><i className={screen === "profile" ? "done" : ""} /><i /></div><section className="onboarding-card">
    {screen !== "welcome" && <IconButton icon="arrowLeft" label="Go back" onClick={onBack} />}
    {screen === "welcome" && <><div className="signal-mark"><Icon name="message" size={34} /></div><h1>Private messaging that feels instant</h1><p>Sign in with your phone number or a username.</p><div className="segment"><button className={mode === "phone" ? "active" : ""} onClick={() => setMode("phone")}>Phone</button><button className={mode === "username" ? "active" : ""} onClick={() => setMode("username")}>Username</button></div><label className="auth-field"><span>{mode === "phone" ? "+1" : "@"}</span><input autoFocus value={value} onChange={(event) => setValue(event.target.value)} placeholder={mode === "phone" ? "555 012 4836" : "your.username"} /></label><small className="auth-help">We never send a real text. Use the demo code on the next screen.</small><button className="primary-button" disabled={value.length < 3} onClick={onContinue}>Continue</button><button className="text-button" onClick={onDemo}>Use demo account</button></>}
    {screen === "verify" && <><h1>Enter your code</h1><p>We sent a code to {value || "+1 555 012 4836"}.</p><div className="otp-boxes">{Array.from({ length: 6 }, (_, index) => <span key={index}>{otp[index] ?? ""}</span>)}<input autoFocus inputMode="numeric" value={otp} maxLength={6} onChange={(event) => { const next = event.target.value.replace(/\D/g, ""); setOtp(next); if (next === "123456") window.setTimeout(onContinue, 250); }} /></div><small className="resend">Resend code in 0:24</small><div className="demo-code"><Icon name="info" size={15} /> Demo build: the code is <strong>123456</strong></div><button className="primary-button" disabled={otp.length !== 6} onClick={onContinue}>Verify</button></>}
    {screen === "profile" && <><h1>Set up your profile</h1><p>This is how people will see you.</p><div className="profile-avatar"><Avatar initials={profileName.split(" ").map((word) => word[0]).join("").slice(0, 2).toUpperCase() || "DU"} index={1} size="xl" /><button><Icon name="camera" size={17} /></button></div><label className="field-label">Display name<input value={profileName} onChange={(event) => setProfileName(event.target.value)} /></label><label className="field-label">About <span>(optional)</span><input placeholder="Available" /></label><button className="primary-button" disabled={!profileName.trim()} onClick={onContinue}>Start messaging</button></>}
  </section></main>;
}
