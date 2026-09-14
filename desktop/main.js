const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const { spawn } = require("node:child_process");

// desktop/ vive dentro do repo, ao lado de backend/ — resolvido sempre
// de forma relativa, nunca por caminho fixo, para não quebrar se o
// repo for movido.
const BACKEND_DIR = path.resolve(__dirname, "..", "backend");
const PYTHONW = path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe");
const APP_PORT = process.env.APP_PORT || "8000";
const APP_URL = `http://127.0.0.1:${APP_PORT}`;
const HEALTH_URL = `${APP_URL}/api/system/health`;

let backendProcess = null;
let startedByUs = false;

async function isBackendUp() {
  try {
    const response = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(1000) });
    return response.ok;
  } catch {
    return false;
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitUntilReady(timeoutMs = 40000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isBackendUp()) return true;
    await sleep(500);
  }
  return false;
}

function spawnBackend() {
  backendProcess = spawn(PYTHONW, ["run.py"], {
    cwd: BACKEND_DIR,
    windowsHide: true,
    detached: false,
    // força modo produção (sem hot-reload do uvicorn) independente do
    // .env — o reloader vigiaria backend/.venv inteira (dezenas de
    // milhares de arquivos) o tempo todo, deixando a máquina lenta.
    env: { ...process.env, APP_ENV: "production" },
  });
  startedByUs = true;
  backendProcess.on("error", (err) => {
    console.error("Falha ao iniciar o backend do TickeTess:", err);
  });
}

function stopBackendIfOwned() {
  if (startedByUs && backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: path.join(__dirname, "build", "icon.ico"),
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  await win.loadFile(path.join(__dirname, "loading.html"));
  win.show();

  const alreadyRunning = await isBackendUp();
  if (!alreadyRunning) {
    spawnBackend();
  }

  const ready = await waitUntilReady();
  if (!ready) {
    console.error("O backend do TickeTess não respondeu a tempo.");
    return;
  }

  await win.loadURL(APP_URL);
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  stopBackendIfOwned();
  app.quit();
});

app.on("before-quit", () => {
  stopBackendIfOwned();
});
