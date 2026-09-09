"use strict";

require("dotenv").config();

function required(name, fallback) {
  const v = process.env[name] || fallback;
  if (!v) {
    console.warn(`[scorenet-api] missing env ${name}`);
  }
  return v || "";
}

function applePrivateKey() {
  const raw = process.env.APPLE_PRIVATE_KEY || "";
  if (!raw) return "";
  return raw.replace(/\\n/g, "\n");
}

module.exports = {
  port: Number(process.env.PORT || 8787),
  nodeEnv: process.env.NODE_ENV || "development",
  mongoUri: required("MONGODB_URI", "mongodb://127.0.0.1:27017/scorenet"),
  sessionSecret: required("SESSION_SECRET", "dev-scorenet-session-secret-change-me"),
  google: {
    clientId: required("GOOGLE_CLIENT_ID"),
    clientSecret: required("GOOGLE_CLIENT_SECRET"),
    callbackUrl: required(
      "GOOGLE_CALLBACK_URL",
      "https://scorenets.com/backend/auth/google/callback"
    ),
  },
  facebook: {
    appId: required("FACEBOOK_APP_ID"),
    appSecret: required("FACEBOOK_APP_SECRET"),
    callbackUrl: required(
      "FACEBOOK_CALLBACK_URL",
      "https://scorenets.com/backend/auth/facebook/callback"
    ),
  },
  apple: {
    clientId: required("APPLE_CLIENT_ID"),
    teamId: required("APPLE_TEAM_ID"),
    keyId: required("APPLE_KEY_ID"),
    privateKey: applePrivateKey(),
    callbackUrl: required(
      "APPLE_CALLBACK_URL",
      "https://scorenets.com/backend/auth/apple/callback"
    ),
  },
  adminBootstrapEmail: (process.env.ADMIN_BOOTSTRAP_EMAIL || "").trim().toLowerCase(),
  adminUsername: (process.env.ADMIN_USERNAME || "admin").trim(),
  adminPassword: process.env.ADMIN_PASSWORD || "",
  adminPasswordSync: process.env.ADMIN_PASSWORD_SYNC === "true",
  cookieSecure:
    process.env.COOKIE_SECURE === "true" ||
    (process.env.COOKIE_SECURE !== "false" && process.env.NODE_ENV === "production"),
};
