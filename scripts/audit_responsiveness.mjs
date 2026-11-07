import { spawn } from 'child_process';
import http from 'http';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const CDP_PORT = 9222;

const PAGES = [
  "/",
  "/assess-device",
  "/batch",
  "/locator",
  "/pathways",
  "/how-it-works",
  "/philosophy",
  "/about",
  "/dashboard",
  "/passport/demo-01-healthy",
];

const VIEWPORTS = [
  { name: "Small mobile", width: 320, height: 640 },
  { name: "Mobile", width: 375, height: 812 },
  { name: "Large mobile", width: 430, height: 932 },
  { name: "Tablet", width: 768, height: 1024 },
  { name: "Small laptop", width: 1024, height: 768 },
  { name: "Laptop", width: 1366, height: 768 },
  { name: "Desktop", width: 1920, height: 1080 },
  { name: "Large desktop", width: 2560, height: 1440 },
];

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

function delay(ms) {
  return new Promise(res => setTimeout(res, ms));
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.msgId = 1;
    this.pending = new Map();
  }

  init() {
    return new Promise((resolve, reject) => {
      this.ws.onopen = () => resolve();
      this.ws.onerror = reject;
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.id && this.pending.has(data.id)) {
          const { resolve, reject } = this.pending.get(data.id);
          this.pending.delete(data.id);
          if (data.error) reject(data.error);
          else resolve(data.result);
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.msgId++;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    this.ws.close();
  }
}

async function run() {
  console.log("Launching headless Chrome...");
  const chrome = spawn(CHROME_PATH, [
    "--headless=new",
    `--remote-debugging-port=${CDP_PORT}`,
    "--disable-gpu",
    "--no-sandbox",
    "--disable-extensions",
    "about:blank"
  ]);

  await delay(2000);

  try {
    const targets = await fetchJson(`http://127.0.0.1:${CDP_PORT}/json`);
    const pageTarget = targets.find(t => t.type === 'page');
    if (!pageTarget) throw new Error("No page target found");

    const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.init();
    await client.send("Page.enable");
    await client.send("DOM.enable");

    console.log("\n=======================================================");
    console.log("          RELOOP AI RESPONSIVENESS & OVERFLOW AUDIT     ");
    console.log("=======================================================\n");

    const overflowReports = [];

    for (const pagePath of PAGES) {
      const pageUrl = `http://localhost:3000${pagePath}`;
      console.log(`\nAuditing Page: ${pagePath}`);
      await client.send("Page.navigate", { url: pageUrl });
      await delay(1500); // allow hydration & layout

      // Toggle dark mode on second pass or evaluate dark mode responsiveness
      await client.send("Runtime.evaluate", {
        expression: `
          document.documentElement.classList.add('dark');
          document.documentElement.setAttribute('data-theme', 'dark');
        `
      });

      for (const vp of VIEWPORTS) {
        // Set device metrics override
        await client.send("Emulation.setDeviceMetricsOverride", {
          width: vp.width,
          height: vp.height,
          deviceScaleFactor: 1,
          mobile: vp.width < 768,
        });

        await delay(300);

        // Test exact requirement: document.documentElement.scrollWidth <= document.documentElement.clientWidth
        const evalRes = await client.send("Runtime.evaluate", {
          expression: `
            (() => {
              const sw = document.documentElement.scrollWidth;
              const cw = document.documentElement.clientWidth;
              const winW = window.innerWidth;
              const hasScroll = sw > cw;
              
              // Also test attempting to scroll horizontally
              window.scrollTo(100, 0);
              const scrolledX = window.scrollX;
              window.scrollTo(0, 0);

              let overflowingElements = [];
              if (hasScroll || scrolledX > 0) {
                const all = Array.from(document.querySelectorAll('*'));
                for (const el of all) {
                  if (['script', 'style', 'head', 'meta', 'link'].includes(el.tagName.toLowerCase())) continue;
                  const rect = el.getBoundingClientRect();
                  if (rect.right > winW + 1.5 || rect.left < -1.5) {
                    if (rect.width > 0 && rect.height > 0) {
                      overflowingElements.push({
                        tag: el.tagName.toLowerCase(),
                        cls: (el.className || '').toString().slice(0, 80),
                        id: el.id || '',
                        width: Math.round(rect.width),
                        right: Math.round(rect.right),
                        left: Math.round(rect.left),
                        diff: Math.round(rect.right - winW)
                      });
                    }
                  }
                }
              }

              return {
                scrollWidth: sw,
                clientWidth: cw,
                windowWidth: winW,
                overflow: hasScroll || scrolledX > 0,
                diff: sw - cw,
                scrolledX,
                elements: overflowingElements.slice(0, 5)
              };
            })()
          `,
          returnByValue: true
        });

        const res = evalRes.result.value;
        const status = res.overflow ? `FAIL (+${res.diff}px)` : "PASS";
        const mark = res.overflow ? "❌" : "✅";
        console.log(`  ${mark} [${vp.name.padEnd(13)} ${vp.width}x${vp.height}]: ${status} (sw=${res.scrollWidth}, cw=${res.clientWidth})`);

        if (res.overflow) {
          overflowReports.push({
            page: pagePath,
            viewport: vp.name,
            size: `${vp.width}x${vp.height}`,
            diff: res.diff,
            elements: res.elements
          });
          for (const el of res.elements) {
            console.log(`       -> <${el.tag} class="${el.cls}"> width=${el.width}px right=${el.right}px (+${el.diff}px)`);
          }
        }
      }
    }

    client.close();
    chrome.kill();

    console.log("\n=======================================================");
    console.log(`Audit Complete. Total Overflows Found: ${overflowReports.length}`);
    console.log("=======================================================\n");

  } catch (err) {
    console.error("Error during audit:", err);
    chrome.kill();
  }
}

run();
