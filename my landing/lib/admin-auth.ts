import { headers } from "next/headers";

function decodeBasicAuth(authHeader: string) {
  if (!authHeader.startsWith("Basic ")) {
    return null;
  }

  const encoded = authHeader.slice(6);
  const decoded = Buffer.from(encoded, "base64").toString("utf8");
  const separatorIndex = decoded.indexOf(":");

  if (separatorIndex === -1) {
    return null;
  }

  return {
    username: decoded.slice(0, separatorIndex),
    password: decoded.slice(separatorIndex + 1),
  };
}

export async function isAdminAuthorized() {
  const headerStore = await headers();
  const authHeader = headerStore.get("authorization");
  const creds = authHeader ? decodeBasicAuth(authHeader) : null;

  const expectedUser = process.env.ADMIN_USERNAME;
  const expectedPassword = process.env.ADMIN_PASSWORD;

  if (!expectedUser || !expectedPassword || !creds) {
    return false;
  }

  return creds.username === expectedUser && creds.password === expectedPassword;
}
