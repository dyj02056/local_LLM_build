// README용 데모 GIF와 스크린샷을 실제 실행 화면에서 녹화한다.
//
//   node scripts/record-demo.mjs [http://localhost:8000]
//
// 설치된 Chrome/Edge를 자동 조작한다 (브라우저를 새로 받지 않음).
// 모델이 SQL을 쓰는 동안의 대기 시간은 GIF에서 압축한다. 나머지는 실제 속도.
// 결과: ../docs/demo.gif, ../docs/screenshot-counter.png, ../docs/screenshot-report.png

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import gifenc from "gifenc";
import pngjs from "pngjs";
import puppeteer from "puppeteer-core";

const { GIFEncoder, applyPalette, quantize } = gifenc;
const { PNG } = pngjs;

const URL = process.argv[2] ?? "http://localhost:8000";
const OUT = new globalThis.URL("../../docs/", import.meta.url);
const W = 1200;
const H = 720;
const BROWSERS = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const frames = []; // { png: Buffer, delay: ms }

async function grab(page, delay) {
  frames.push({ png: await page.screenshot({ type: "png" }), delay });
}

/** 실제 시간 그대로 ms 동안 fps로 찍는다 */
async function film(page, ms, fps = 8) {
  const step = 1000 / fps;
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const t = Date.now();
    await grab(page, step);
    await sleep(Math.max(0, step - (Date.now() - t)));
  }
}

const busy = (page) =>
  page.evaluate(() => [...document.querySelectorAll("article")].some((a) => a.getAttribute("aria-busy") === "true"));

/** 인쇄가 끝날 때까지 기다리며, 대기 구간은 2초마다 한 장만 남겨 0.35초로 보여 준다 */
async function filmUntilPrinted(page) {
  let lastKept = 0;
  while (await busy(page)) {
    const t = Date.now();
    if (t - lastKept >= 2000) {
      await grab(page, 350);
      lastKept = t;
    }
    await sleep(150);
  }
}

async function smoothScroll(page, toY, ms = 1400) {
  const fromY = await page.evaluate(() => scrollY);
  const n = Math.round((ms / 1000) * 10);
  for (let i = 1; i <= n; i++) {
    const p = 1 - Math.pow(1 - i / n, 3);
    await page.evaluate((y) => window.scrollTo(0, y), fromY + (toY - fromY) * p);
    await grab(page, 100);
  }
}

function encodeGif(path) {
  const gif = GIFEncoder();
  for (const f of frames) {
    const { data, width, height } = PNG.sync.read(f.png);
    const palette = quantize(data, 256);
    gif.writeFrame(applyPalette(data, palette), width, height, { palette, delay: Math.round(f.delay) });
  }
  gif.finish();
  writeFileSync(path, gif.bytes());
}

const exe = BROWSERS.find((p) => existsSync(p));
if (!exe) throw new Error("Chrome 또는 Edge를 찾지 못했습니다.");
mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({ executablePath: exe, headless: true, defaultViewport: { width: W, height: H } });
try {
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: "networkidle0" });
  await page.waitForFunction(() => document.querySelector("header [role=status]")?.textContent?.includes("2/2"), {
    timeout: 20000,
  });

  // 1) 빈 계산대
  await film(page, 1200, 4);

  // 2) 22번 문제 선택, 둘 다 비교, 자동수정 켜기
  await page.click('[aria-label^="22번"]');
  await film(page, 600);
  await page.click('input[value="compare"] + span');
  await film(page, 500);
  await page.click('[role="switch"]');
  await film(page, 700);

  // 3) 인쇄: 대기 구간은 압축, 영수증이 찍히는 구간은 실제 속도
  await page.click('button[type="submit"]');
  await film(page, 1000);
  await filmUntilPrinted(page);
  await film(page, 1500);

  // 4) 파인튜닝 영수증의 VOID 줄과 합계까지 내려 보기
  const voidY = await page.evaluate(() => {
    const el = [...document.querySelectorAll("article")][1];
    return el ? el.getBoundingClientRect().top + scrollY + 260 : 0;
  });
  await smoothScroll(page, voidY);
  await film(page, 2200, 4);
  await page.screenshot({ path: new globalThis.URL("screenshot-counter.png", OUT), type: "png" });
  await smoothScroll(page, 0, 900);

  // 5) 정산 리포트
  await page.click('nav button:nth-of-type(2)');
  await film(page, 1600, 4);
  await page.screenshot({ path: new globalThis.URL("screenshot-report.png", OUT), type: "png" });
  const koreanY = await page.evaluate(() => {
    const h = [...document.querySelectorAll("h2")].find((x) => x.textContent?.includes("한국어"));
    return h ? h.getBoundingClientRect().top + scrollY - 90 : 0;
  });
  await smoothScroll(page, koreanY, 1800);
  await film(page, 2600, 4);

  encodeGif(new globalThis.URL("demo.gif", OUT));
  console.log(`frames ${frames.length}, length ${(frames.reduce((a, f) => a + f.delay, 0) / 1000).toFixed(1)}s -> docs/demo.gif`);
} finally {
  await browser.close();
}
