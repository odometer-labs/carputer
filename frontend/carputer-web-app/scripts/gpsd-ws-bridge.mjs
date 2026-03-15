import net from "node:net";
import process from "node:process";
import { WebSocketServer } from "ws";

const GPSD_HOST = process.env.GPSD_HOST || "127.0.0.1";
const GPSD_PORT = Number(process.env.GPSD_PORT || 2947);
const WS_HOST = process.env.WS_HOST || "0.0.0.0";
const WS_PORT = Number(process.env.WS_PORT || 8765);

let gpsdSocket = null;
let reconnectTimer = null;
let lineBuffer = "";

const wsServer = new WebSocketServer({ host: WS_HOST, port: WS_PORT });

function broadcast(payload) {
  const message = JSON.stringify(payload);
  for (const client of wsServer.clients) {
    if (client.readyState === 1) {
      client.send(message);
    }
  }
}

function normalizeGpsdTpv(tpv) {
  if (typeof tpv.lat !== "number" || typeof tpv.lon !== "number") {
    return null;
  }

  return {
    lat: tpv.lat,
    lon: tpv.lon,
    latitude: tpv.lat,
    longitude: tpv.lon,
    altitude: typeof tpv.altHAE === "number" ? tpv.altHAE : tpv.alt,
    speed: tpv.speed,
    heading: typeof tpv.track === "number" ? tpv.track : tpv.heading,
    bearing: typeof tpv.track === "number" ? tpv.track : tpv.heading,
    timestamp: tpv.time ? Date.parse(tpv.time) : Date.now(),
    source: "gpsd",
  };
}

function handleGpsdLine(line) {
  let packet;
  try {
    packet = JSON.parse(line);
  } catch {
    return;
  }

  if (packet.class !== "TPV") {
    return;
  }

  const normalized = normalizeGpsdTpv(packet);
  if (!normalized) {
    return;
  }

  broadcast(normalized);
}

function scheduleReconnect() {
  if (reconnectTimer) {
    return;
  }

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectGpsd();
  }, 1000);
}

function connectGpsd() {
  if (gpsdSocket) {
    gpsdSocket.destroy();
    gpsdSocket = null;
  }

  const socket = net.createConnection(
    { host: GPSD_HOST, port: GPSD_PORT },
    () => {
      console.log(
        `[gps-bridge] Connected to gpsd at ${GPSD_HOST}:${GPSD_PORT}`,
      );
      socket.write('?WATCH={"enable":true,"json":true};\n');
    },
  );

  socket.setEncoding("utf8");

  socket.on("data", (chunk) => {
    lineBuffer += chunk;
    const lines = lineBuffer.split("\n");
    lineBuffer = lines.pop() || "";

    for (const line of lines) {
      if (line.trim().length > 0) {
        handleGpsdLine(line.trim());
      }
    }
  });

  socket.on("error", (error) => {
    console.error(`[gps-bridge] gpsd socket error: ${error.message}`);
  });

  socket.on("close", () => {
    console.warn("[gps-bridge] Disconnected from gpsd, retrying...");
    scheduleReconnect();
  });

  gpsdSocket = socket;
}

wsServer.on("listening", () => {
  console.log(`[gps-bridge] WebSocket listening on ws://${WS_HOST}:${WS_PORT}`);
  connectGpsd();
});

wsServer.on("connection", () => {
  console.log(
    `[gps-bridge] Frontend client connected (${wsServer.clients.size} total)`,
  );
});

wsServer.on("error", (error) => {
  console.error(`[gps-bridge] WebSocket server error: ${error.message}`);
});

function shutdown() {
  console.log("[gps-bridge] Shutting down...");
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (gpsdSocket) {
    gpsdSocket.destroy();
    gpsdSocket = null;
  }
  wsServer.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
