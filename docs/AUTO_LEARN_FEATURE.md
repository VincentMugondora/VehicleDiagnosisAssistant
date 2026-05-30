# 🤖 Auto-Learn Feature - Dynamic Code Fetching

## What It Does

Your Vehicle Diagnosis Assistant can now **automatically learn new OBD codes** when users ask about codes not in your database!

### The Flow

```
User sends P3499
    ↓
Not in database (132 codes)
    ↓
🌐 Fetch from OBD-Codes.com
    ↓
🤖 LLM parses and structures data
    ↓
💾 Save to database (now 133 codes!)
    ↓
✉️ Send structured response to user
```

### What This Means

✅ **Self-Improving System**
- Starts with 132 verified codes
- Learns new codes from real user requests
- Database grows organically over time

✅ **Better User Experience**
- Users get detailed info even for rare codes
- No more generic "code not found" messages
- System gets smarter with each use

✅ **Cost Effective**
- Only fetches codes users actually ask about
- No need to manually add 5000+ codes upfront
- Focuses on codes that matter to YOUR users

## How It Works

### 1. Code Not Found
When a user sends a code like **P3499** that's not in your 132-code database:

```python
base = self.obd_repo.get_by_code("P3499")
# Returns None - code not in database
```

### 2. Web Fetching
The system automatically:
- Fetches from **OBD-Codes.com** (free, no API key needed)
- Scrapes the HTML page
- Extracts description, causes, symptoms, fixes

```python
raw_data = await self.web_fetcher.fetch_code("P3499")
# Returns: {
#   "description": "...",
#   "symptoms": "...",
#   "common_causes": "...",
#   "generic_fixes": "..."
# }
```

### 3. LLM Enhancement
The raw scraped data is enhanced using your AI provider:

```python
enhanced = await self.code_enhancer.enhance_code_data(raw_data, "P3499")
# LLM cleans, structures, and validates the data
# Returns proper JSON with severity, system classification, etc.
```

### 4. Database Save
The enhanced code is saved for future users:

```python
self.obd_repo.insert_code(enhanced_data)
# Uses upsert - won't create duplicates
# Now P3499 is in your database permanently
```

### 5. User Response
The user gets a detailed, structured response:

```
Code: P3499
Description: Cylinder Deactivation/Intake Valve Control Circuit High
Causes: Faulty valve control solenoid, wiring issue, ECM fault
Symptoms: Check engine light, rough idle, reduced power
Severity: Medium
Confidence: 70% (web-learned)
```

## Configuration

### Enable/Disable Auto-Learn

In your `.env` file:

```bash
# Enable automatic code learning (default: true)
AUTO_LEARN_CODES=true

# Disable if you only want your curated 132 codes
# AUTO_LEARN_CODES=false
```

### AI Provider

Auto-learn works with **both AI providers**:

```bash
# Using Cohere (recommended)
AI_PROVIDER=cohere
COHERE_API_KEY=your-key-here

# OR using Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

If no AI provider is configured:
- ✅ System still works
- ✅ Uses simpler web scraping
- ⚠️ Lower quality data (no LLM enhancement)

## Features

### Smart Source Selection
Tries multiple free sources in order:
1. **OBD-Codes.com** (best quality, 5000+ codes)
2. **Engine-Codes.com** (backup source)
3. **Fallback** (generic response if all fail)

### Quality Validation
LLM ensures data quality:
- ✅ Validates all required fields present
- ✅ Checks description length and clarity
- ✅ Determines proper severity (High/Medium/Low)
- ✅ Classifies system (Powertrain/Chassis/Body/Network)
- ✅ Structures causes and fixes as lists

### Deduplication
- Uses `upsert` - won't create duplicates
- If code already exists, updates it
- Safe to run multiple times

### Confidence Tracking
Responses show confidence level:
- **98%** - Vehicle-specific override
- **85%** - From your curated 132 codes
- **70%** - Web-learned code (new!)
- **30%** - Generic fallback

## Benefits

### For Users
- ✅ Get detailed info for **any** OBD code
- ✅ Even rare/uncommon codes are covered
- ✅ No "code not found" dead ends
- ✅ Consistent, structured responses

### For You
- ✅ Database grows automatically
- ✅ Learn which codes users care about
- ✅ No manual code entry needed
- ✅ System gets better over time
- ✅ Cost-effective (only fetch what's needed)

### For Your System
- ✅ Starts production-ready (132 codes)
- ✅ Handles edge cases gracefully
- ✅ Self-improving architecture
- ✅ Scales with user demand

## Examples

### Example 1: P3499 (Rare Code)

**User sends**: "P3499"

**System**:
1. ❌ Not in database
2. 🌐 Fetches from OBD-Codes.com
3. 🤖 LLM structures data
4. 💾 Saves to database
5. ✉️ Responds to user

**User receives**:
```
Code: P3499
Description: Cylinder Deactivation/Intake Valve Control Circuit High (Cylinder 12)
Common on: V12 engines, some V8s with Active Fuel Management

Symptoms:
• Check engine light
• Rough idle
• Reduced power
• Poor fuel economy

Likely causes:
• Faulty valve control solenoid
• Wiring issue in valve circuit
• ECM software fault
• Mechanical valve failure

Next steps:
1. Scan for related codes
2. Check wiring to cylinder 12 valve
3. Test valve solenoid operation
4. Inspect mechanical valve components

Severity: Medium
Source: Web-learned
Confidence: 70%
```

**Next user** who asks about P3499 gets instant response from database (85% confidence)!

### Example 2: P2177 (Modern Emissions Code)

**First user**: Asks about P2177
- System fetches, learns, saves
- User gets detailed response

**All future users**: Get instant lookup
- No fetching needed
- Full confidence
- Fast response

## Monitoring

### Check Auto-Learned Codes

Query your database:

```sql
SELECT code, description, created_at
FROM obd_codes
WHERE created_at > '2026-05-30'  -- codes added today
ORDER BY created_at DESC;
```

### Logs

Watch for these log entries:

```
dynamic_fetch_started - code=P3499
web_fetch_success - code=P3499, source=OBD-Codes.com
llm_enhancement_started - code=P3499
llm_enhancement_success - code=P3499
auto_save_success - code=P3499
```

### Success Rate

Monitor how often auto-learn succeeds:

```python
# Success indicators in logs:
auto_save_success  # Code learned and saved
web_fetch_failed   # Web scraping failed
llm_enhancement_failed  # AI parsing failed
```

## Cost Considerations

### API Costs
- **Web Scraping**: Free (no API key needed)
- **AI Enhancement**: Uses your existing AI provider
  - Cohere: ~$0.0005 per code learned
  - Gemini: ~$0.00002 per code learned
  - Only charged when learning NEW codes

### Savings
- **Don't need to**:
  - Pre-load 5000+ codes manually
  - Pay for premium OBD API access
  - Maintain huge database of unused codes
- **Only learn**:
  - Codes users actually ask about
  - Organic growth based on demand

## Limitations

### What It Can Do
✅ Learn any generic OBD-II code (P0000-P3999, C0000-C3999, etc.)
✅ Extract description, causes, symptoms, fixes
✅ Classify severity and system
✅ Save permanently to database

### What It Can't Do
❌ Access manufacturer-specific proprietary info
❌ Provide vehicle-specific wiring diagrams
❌ Give exact pricing for repairs
❌ Diagnose the actual problem (still need scanner)

### Web Scraping Caveats
- Depends on external websites staying online
- HTML structure changes can break parsers
- Falls back to generic response if scraping fails
- Quality varies by source

## Troubleshooting

### Code Not Being Learned

**Check logs for**:
```
web_fetch_failed - source unavailable or blocked
llm_enhancement_failed - AI parsing error
auto_save_failed - database write error
```

**Solutions**:
1. Check internet connectivity
2. Verify AI provider configured
3. Check database permissions
4. Try disabling/re-enabling feature

### Low Quality Data

If learned codes have poor descriptions:

1. **Check AI provider** - Cohere gives better results
2. **Check website source** - Some sources better than others
3. **Manual fix** - Edit the database entry directly

### Too Many API Calls

If costs are high:

1. **Disable auto-learn** temporarily
2. **Pre-load common codes** manually
3. **Monitor which codes** users ask about most
4. **Batch import** those codes from scripts

## Best Practices

### 1. Start Small
- ✅ Begin with 132 curated codes
- ✅ Let auto-learn handle edge cases
- ✅ Monitor what codes users ask about
- ✅ Batch-add popular ones manually (higher quality)

### 2. Quality Over Quantity
- ✅ 132 verified codes + auto-learn is better than 5000 mediocre codes
- ✅ Auto-learned codes still get reviewed by LLM
- ✅ Users get good responses even for rare codes

### 3. Monitor and Tune
- ✅ Check logs daily for learned codes
- ✅ Review quality of auto-learned entries
- ✅ Manually improve popular codes
- ✅ Disable if not useful for your use case

## Future Enhancements

### Possible Additions
- [ ] Multiple LLM validation (consensus)
- [ ] Community voting on quality
- [ ] Automatic code categorization
- [ ] Learn from multiple sources simultaneously
- [ ] Cache failed lookups (don't retry immediately)
- [ ] Admin dashboard to review learned codes
- [ ] Export learned codes to scripts

## Summary

**The auto-learn feature makes your system**:
- 🎯 **Comprehensive** - Handles any OBD code
- 🧠 **Smart** - Learns from real usage
- 💰 **Cost-effective** - Only fetches what's needed
- 🚀 **Self-improving** - Gets better over time
- ✅ **Production-ready** - Works out of the box

**Your users get**:
- Detailed responses for rare codes
- No dead ends or "code not found"
- Consistent, structured information
- Better experience overall

**You get**:
- Self-maintaining database
- Insights into user needs
- Reduced maintenance burden
- Scalable architecture

**Enable it and watch your system learn! 🤖**
