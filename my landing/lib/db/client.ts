import { mkdirSync } from "node:fs";
import { dirname, isAbsolute, join } from "node:path";

import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";

import * as schema from "@/lib/db/schema";

function resolveDatabaseUrl() {
  const configured = process.env.DATABASE_URL;

  if (configured) {
    if (configured.startsWith("file:")) {
      const rawPath = configured.slice(5);
      const absolutePath = isAbsolute(rawPath) ? rawPath : join(process.cwd(), rawPath);
      mkdirSync(dirname(absolutePath), { recursive: true });
      return `file:${absolutePath.replace(/\\/g, "/")}`;
    }

    return configured;
  }

  const defaultPath = join(process.cwd(), "data", "leads.db");
  mkdirSync(dirname(defaultPath), { recursive: true });
  return `file:${defaultPath.replace(/\\/g, "/")}`;
}

const client = createClient({
  url: resolveDatabaseUrl(),
});

export const db = drizzle(client, { schema });
