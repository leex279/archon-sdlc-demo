#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { parseChapters, renderChapters } from "./chapters.ts";

const file = process.argv[2];
const input = file ? readFileSync(file, "utf8") : readFileSync(0, "utf8");
console.log(renderChapters(parseChapters(input)));
