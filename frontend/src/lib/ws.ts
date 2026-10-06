type EventCallback = (data: any) => void;

class SignalWebSocket {
  private socket: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectTimer: number | null = null;
  private reconnectInterval = 1000;
  private isIntentionalClose = false;

  public connect() {
    const token = localStorage.getItem("signal_token");
    if (!token) return;

    this.isIntentionalClose = false;
    const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws`;
    const fullUrl = `${wsUrl}?token=${encodeURIComponent(token)}`;

    this.socket = new WebSocket(fullUrl);

    this.socket.onopen = () => {
      console.log("[WS] Connected to Signal server");
      this.reconnectInterval = 1000;
    };

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { type, data } = payload;
        if (type) {
          this.emit(type, data);
        }
      } catch (err) {
        console.error("[WS] Error parsing message", err);
      }
    };

    this.socket.onclose = () => {
      console.log("[WS] Disconnected from server");
      if (!this.isIntentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = (err) => {
      console.error("[WS] Error", err);
      this.socket?.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectInterval = Math.min(this.reconnectInterval * 1.5, 10000);
      this.connect();
    }, this.reconnectInterval);
  }

  public disconnect() {
    this.isIntentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }

  public send(type: string, data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, data }));
    } else {
      console.warn("[WS] Socket not open. Message queued or dropped.", type);
    }
  }

  public on(event: string, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.off(event, callback);
  }

  public off(event: string, callback: EventCallback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach((cb) => cb(data));
    }
  }
}

export const wsClient = new SignalWebSocket();
