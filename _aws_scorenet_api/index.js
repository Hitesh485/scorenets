"use strict";

require("dotenv").config();

const path = require("path");
const express = require("express");
const session = require("express-session");
const MongoStore = require("connect-mongo");
const passport = require("passport");
const mongoose = require("mongoose");

const config = require("./config");
const { configurePassport } = require("./passport");
const { ensureAdminAccount } = require("./adminAuth");
const authRoutes = require("./routes/auth");
const adminRoutes = require("./routes/admin");
const tvRoutes = require("./routes/tv");
const snPredictionsRoutes = require("./routes/snPredictions");
const { mountXfeedProxies } = require("./routes/xfeedProxy");

const app = express();

app.set("trust proxy", 1);

// Sports TV RTS — must be before express.json (raw POST body, swastik parity)
mountXfeedProxies(app);

app.use(express.json());
app.use(express.urlencoded({ extended: false }));

function mount(pathSuffix, router) {
  // nginx strips /backend/ → Express sees /auth/... ; also support /backend for direct hits
  app.use(pathSuffix, router);
  app.use(`/backend${pathSuffix}`, router);
}

function healthPayload() {
  return {
    ok: true,
    service: "scorenet-api",
    ts: new Date().toISOString(),
    mode: "express_mongo_auth",
    mongo: mongoose.connection.readyState === 1 ? "up" : "down",
    googleConfigured: Boolean(config.google.clientId && config.google.clientSecret),
  };
}

app.get(["/health", "/backend/health"], (_req, res) => {
  res.json(healthPayload());
});

app.get(["/", "/backend"], (_req, res) => {
  res.json({
    name: "ScoreNet",
    health: "/backend/health",
    auth: {
      google: "/backend/auth/google",
      me: "/backend/auth/me",
      logout: "POST /backend/auth/logout",
    },
    admin: "/admin",
    tv: {
      health: "/backend/tv/health",
      stream: "/backend/tv/stream?gmid=",
      page: "/live-tv/",
    },
  });
});

// Old URL → new admin path
app.get(["/backend/admin", "/backend/admin/"], (_req, res) => {
  res.redirect(301, "/admin");
});

async function start() {
  configurePassport();

  await mongoose.connect(config.mongoUri);
  console.log("[scorenet-api] mongo connected");
  await ensureAdminAccount();

  app.use(
    session({
      name: "scorenet.sid",
      secret: config.sessionSecret,
      resave: false,
      saveUninitialized: false,
      store: MongoStore.create({
        mongoUrl: config.mongoUri,
        ttl: 60 * 60 * 24 * 14,
        touchAfter: 24 * 3600,
      }),
      cookie: {
        httpOnly: true,
        secure: config.cookieSecure,
        sameSite: "lax",
        maxAge: 1000 * 60 * 60 * 24 * 14,
        path: "/",
      },
    })
  );

  app.use(passport.initialize());
  app.use(passport.session());

  mount("/auth", authRoutes);
  mount("/admin", adminRoutes);
  mount("/tv", tvRoutes);
  mount("/sn-predictions", snPredictionsRoutes);

  app.use("/admin/static", express.static(path.join(__dirname, "../public/admin")));
  app.use("/backend/admin/static", express.static(path.join(__dirname, "../public/admin")));

  app.use((err, _req, res, _next) => {
    console.error("[scorenet-api] error", err);
    res.status(500).json({ ok: false, error: "server_error" });
  });

  app.listen(config.port, "127.0.0.1", () => {
    console.log(`[scorenet-api] listening on 127.0.0.1:${config.port}`);
  });
}

start().catch((err) => {
  console.error("[scorenet-api] failed to start", err);
  process.exit(1);
});
