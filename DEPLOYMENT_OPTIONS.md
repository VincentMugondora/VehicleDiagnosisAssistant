# Deployment & WhatsApp Connection Options

**Date:** 2026-08-12  
**Status:** Planning

---

## 1. Phone Number (Always Online for WhatsApp)

The Baileys server needs a WhatsApp-registered number with an active session. Once the QR code is scanned and the session is stored on the server, the physical phone can be off — Baileys maintains the connection via stored credentials.

| Option | Cost/Month | Pros | Cons |
|--------|-----------|------|------|
| **Dedicated Econet/NetOne SIM** (recommended for ZW) | ~$1-3 | Cheap, full control, reliable for WhatsApp | Need physical SIM for initial verification; re-scan if session drops |
| **Dedicated SIM on old Android** (backup) | ~$1-3 + phone | Fallback if server session fails | Power/internet dependency |
| **Virtual number (TextNow, Hushed, JMP.chat)** | $0-5 | No physical SIM | WhatsApp frequently blocks VoIP numbers |
| **eSIM (Airalo, Holafly)** | $3-10 | Works internationally | Still need device for initial verification |
| **WhatsApp Business API (official, via BSP)** | Per-conversation fees ($0.005-0.08) | No bans, no session drops, 99.9% uptime | Requires business verification, ongoing costs |

**Recommendation:** Dedicated Econet or NetOne SIM (~$2/month). Use it exclusively for the bot. Session invalidation (requiring re-scan) is rare — typically weeks to months apart.

---

## 2. WhatsApp Connection Method

| | Baileys (current) | WhatsApp Business API (official) |
|--|--|--|
| **Cost** | Free (no per-message fees) | ~$0.005-0.08 per conversation (24h window) |
| **Reliability** | Session can drop; possible bans | 99.9% uptime, no bans |
| **Setup** | QR scan | Business verification (days to weeks) |
| **Rate limits** | Aggressive — WhatsApp can ban for bot-like behavior | Official, clearly documented limits |
| **Media support** | Works but can be fragile | Fully supported |
| **Ban risk** | Moderate (mitigated by rate limiting) | None |

**Recommendation:** Stay with Baileys for now (free, already implemented). Mitigate ban risk with:
- Rate limiting (already in place via `express-rate-limit`)
- Natural delays between messages
- Keep message volume reasonable (<100 users/day is safe)
- Dedicated number (not personal) so a ban doesn't affect personal WhatsApp

**When to upgrade to official API:** If the bot gets banned repeatedly, or user volume exceeds ~500/day.

---

## 3. Render Deployment Costs

The project has 2 services:

| Service | Stack | Render Plan | Monthly Cost | Notes |
|---------|-------|-------------|-------------|-------|
| **FastAPI backend** | Python, Docker | Free tier | $0 | Can tolerate cold starts (15 min inactivity spin-down) |
| **Baileys server** | Node.js | **Starter (minimum)** | **$7/month** | Must stay alive for WhatsApp session |

### Why Baileys can't use Render Free Tier
- Free tier spins down after 15 min of inactivity
- Spin-down kills the WhatsApp WebSocket connection
- Even with keep-alive pings, cold starts lose the session auth
- Result: constant QR re-scans, unreliable bot

### Total on Render
| Item | Cost |
|------|------|
| FastAPI backend (Free) | $0 |
| Baileys server (Starter) | $7 |
| **Total** | **$7/month** |

---

## 4. Alternative Hosting Platforms

| Platform | Cost/Month | Always-on? | Notes |
|----------|-----------|------------|-------|
| **Render Starter** | $7 | Yes | Simple, current setup |
| **Railway.app** | $5 | Yes | Hobby plan, good DX |
| **Fly.io** | $0-5 | Yes (free tier: 3 shared VMs, 256MB) | Can run both services |
| **Oracle Cloud free tier** | $0 (forever) | Yes (2 ARM VMs) | Most setup work, but truly free |
| **Hetzner VPS** | ~$3-5 | Yes | Full control, EU-based |
| **Contabo VPS** | ~$3-5 | Yes | Full control, cheap |
| **DigitalOcean** | $4-6 | Yes | Droplet or App Platform |

---

## 5. Recommended Setup (Budget-Optimized)

| Item | Choice | Cost/Month |
|------|--------|-----------|
| Phone number | Dedicated Econet/NetOne SIM | ~$2 |
| WhatsApp connection | Baileys (free) | $0 |
| Hosting (Baileys) | Render Starter | $7 |
| Hosting (FastAPI) | Render Free | $0 |
| **Total** | | **~$9/month** |

### Ultra-Budget Alternative (~$2-3/month)
- Oracle Cloud free tier for hosting (both services) — $0
- Dedicated SIM — $2/month
- Trade-off: More DevOps setup, less managed infrastructure

---

## 6. Session Persistence Strategy

To minimize QR re-scans on Render:

1. **Store Baileys auth state in Supabase** (not just local filesystem)
   - Survives redeploys and restarts
   - Already using Supabase for the main DB
2. **Keep-alive endpoint** (already implemented — commit `00b52c3`)
   - Pings the Baileys server to prevent idle timeout
3. **Health monitoring** — alert if session disconnects so you can re-scan quickly

---

## Next Steps

- [ ] Purchase dedicated SIM for the bot
- [ ] Deploy Baileys server on Render Starter plan
- [ ] Configure auth state persistence (Supabase or Render disk)
- [ ] Set up health monitoring/alerts for session drops
- [ ] Test end-to-end: SIM → QR scan → bot responds
