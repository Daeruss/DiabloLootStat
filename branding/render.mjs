import sharp from "sharp";
import { readFileSync } from "fs";

const svg = readFileSync("bot-icon.svg");

await sharp(svg, { density: 384 })
  .resize(512, 512)
  .png()
  .toFile("bot-icon.png");

console.log("bot-icon.png готов (512x512)");
