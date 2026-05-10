import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { ChildProcess, spawn } from "child_process";
import path from "path";

let mainWindow: BrowserWindow | null = null;
let pythonServer: ChildProcess | null = null;

const PYTHON_PORT = 8765;
const API_URL = `http://127.0.0.1:${PYTHON_PORT}`;

// ── Python server management ──────────────────────────────────────────────────

function startPythonServer(): void {
  console.log("Starting Python FastAPI server...");
  const pythonCmd = process.platform === "win32" ? "python" : "python3";
  pythonServer = spawn(pythonCmd, ["-m", "educast.server"], {
    cwd: path.resolve(__dirname, "../../"),
    env: { ...process.env },
    stdio: ["pipe", "pipe", "pipe"],
  });

  pythonServer.stdout?.on("data", (data: Buffer) => {
    console.log(`[python] ${data.toString().trim()}`);
  });

  pythonServer.stderr?.on("data", (data: Buffer) => {
    console.log(`[python:err] ${data.toString().trim()}`);
  });

  pythonServer.on("error", (err) => {
    console.error("Failed to start Python server:", err);
  });

  pythonServer.on("close", (code) => {
    console.log(`Python server exited with code ${code}`);
    pythonServer = null;
  });
}

function stopPythonServer(): void {
  if (pythonServer) {
    pythonServer.kill("SIGTERM");
    pythonServer = null;
  }
}

async function waitForServer(
  maxRetries: number = 30,
  interval: number = 1000,
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(API_URL);
      if (response.ok) return true;
    } catch {
      // Server not ready yet
    }
    await new Promise((r) => setTimeout(r, interval));
  }
  return false;
}

// ── Window creation ───────────────────────────────────────────────────────────

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: "educast",
    webPreferences: {
      preload: path.join(__dirname, "../preload/preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // In dev mode, load from Vite dev server; in prod, load built HTML
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── IPC handlers ──────────────────────────────────────────────────────────────

ipcMain.handle("select-directory", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
    title: "Select university data folder",
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("get-api-url", () => API_URL);

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  startPythonServer();

  const ready = await waitForServer();
  if (!ready) {
    console.error("Python server failed to start within timeout");
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  stopPythonServer();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopPythonServer();
});
