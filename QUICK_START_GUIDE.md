# Quick Start Guide 🚀

**Vehicle Diagnosis Assistant** - Production Ready Setup

---

## ⚡ Start the Backend

```bash
.\start_backend.bat
```

Backend runs on: `http://localhost:8001`

---

## 🧪 Test Commands

### AI Diagnostics
```
Send: P0420
Expected: Diagnosis with causes and checks ✅

Send: explain further
Expected: Detailed AI explanation ✅
```

### Payment Commands
```
Send: STATUS
Expected: Shows free tier usage (X/5) ✅

Send: SUBSCRIBE john@example.com 0771234567
Expected: Payment initiation message 
(Will work fully when Paynow keys added)

Send: CANCEL
Expected: Cancellation confirmation ✅

Send: RENEW john@example.com 0771234567
Expected: Renewal initiation message
```

---

## 📋 Available Commands

| Command | Format | What It Does |
|---------|--------|--------------|
| **Diagnosis** | `P0420` | Get OBD code diagnosis |
| **Followup** | `explain further` | Ask about last diagnosis |
| **Status** | `STATUS` | Check subscription/usage |
| **Subscribe** | `SUBSCRIBE <email> <phone>` | Start subscription |
| **Cancel** | `CANCEL` | Stop auto-renewal |
| **Renew** | `RENEW <email> <phone>` | Restart subscription |

---

## ✅ What's Working

- ✅ AI-powered diagnostics (Cohere + Gemini backup)
- ✅ Followup questions with context
- ✅ Free tier tracking (5/week)
- ✅ Payment commands (all 4)
- ✅ Database (all tables)
- ✅ WhatsApp webhooks

---

## ⚠️ What Needs Configuration

### For Payments
Add to `.env`:
```bash
PAYNOW_INTEGRATION_ID=your-id-here
PAYNOW_INTEGRATION_KEY=your-key-here
```

---

## 📊 System Status Check

```bash
# Test AI system
python test_ai_fallback.py

# Test payment commands
python test_payment_commands.py

# Test production readiness
python test_production_ready.py
```

All should show: **PASSED** ✅

---

## 🔍 Monitor Logs

Watch for:
```
✅ ai_client_initialized provider=cohere
✅ ai_backup_initialized backup_provider=gemini
✅ supabase_connected
✅ Application startup complete
```

---

## 🆘 Quick Troubleshooting

### Backend won't start
- Check `.env` file exists
- Verify Supabase credentials
- Check port 8001 is free

### Commands not working
- Restart backend
- Check webhook connection
- Verify WhatsApp integration

### Database errors
- Run: `migrations/add_payments_tables.sql` in Supabase
- Verify all 3 tables exist

---

## 📚 Full Documentation

- **Setup**: `SETUP_COMPLETE.md`
- **AI System**: `docs/AI_FALLBACK_SETUP.md`
- **Payment Flow**: `PAYMENT_COMMANDS_COMPLETE.md`
- **Complete Summary**: `IMPLEMENTATION_SUMMARY.md`

---

## 🎯 Production Checklist

- [x] AI providers configured
- [x] Database tables created
- [x] All commands implemented
- [x] Tests passing
- [ ] Paynow credentials added
- [ ] Public webhook URL configured
- [ ] Production WhatsApp number connected

---

**Status**: 🎉 Ready to use!  
**Support**: See documentation files  
**Version**: July 3, 2026
