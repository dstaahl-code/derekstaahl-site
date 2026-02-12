# Generation AI Booking Automation - FREE PLAN (2-Scenario) Spec

## Overview of Changes from Original Spec

**Original Plan:** 5 separate Make.com scenarios
**Revised Plan:** 2 consolidated scenarios (fits free tier)

**Key Consolidation Strategy:**
- **Scenario 1:** Real-time webhook-based automations (instant triggers)
- **Scenario 2:** Time-based scheduled automations (runs on schedule)

This approach maximizes efficiency while staying within Make.com's free plan limit of 2 active scenarios.

---

## Scenario 1: Webhook Handler (Real-Time Events)

### Purpose
Handle all real-time, event-driven automations that require instant response.

### Triggers
This scenario uses **webhooks** which don't consume operations when idle (unlike polling triggers).

### Combined Workflow

```
WEBHOOK TRIGGER (Router with 3 paths)
    ↓
[Router Module] - Determines which path based on webhook source
    ↓
    ├─→ PATH A: Cal.com Booking Webhook
    │   ├─ Parse Cal.com JSON payload
    │   ├─ Create Airtable record
    │   │  - Guest Name, Email, Additional Emails, Show Date/Time, Platform, Topic
    │   │  - Status: "Pending Confirmation"
    │   │  - Cal.com Event ID
    │   └─ Send notification email to Derek
    │      Subject: "New Booking: {{Guest Name}} on {{Show Date}}"
    │
    ├─→ PATH B: Recording Confirmation Webhook
    │   ├─ Parse query parameter: booking_id
    │   ├─ Search Airtable for matching Booking ID
    │   ├─ Update Airtable record
    │   │  - Recording Ready = TRUE
    │   │  - Status = "Recording Ready"
    │   ├─ Send confirmation email to Derek
    │   │  Subject: "✅ Recording Ready - {{Guest Name}}"
    │   └─ Return HTML confirmation page to operator
    │
    └─→ PATH C: Airtable Status Change Webhook
        ├─ Parse Airtable webhook payload
        ├─ Check if Status changed to "Confirmed"
        ├─ Check if Needs Adjustment = FALSE
        ├─ Check if Studio Email Sent = FALSE
        ├─ [Filter: Only proceed if all conditions met]
        ├─ Send studio booking email
        │  To: phx-studiorequests@graymedia.com
        │  Subject: "Studio Booking - Generation AI - {{Show Date}}"
        └─ Update Airtable record
           - Studio Email Sent = TRUE
```

### Technical Implementation Details

#### Webhook Setup

**Single Webhook URL:** `https://hook.us1.make.com/WEBHOOK_ID`

**Three Sources Call This Same Webhook:**

1. **Cal.com** sends bookings with:
   ```json
   {
     "source": "calcom",
     "triggerEvent": "BOOKING_CREATED",
     "payload": {
       "attendees": [...],
       "metadata": {...}
     }
   }
   ```

2. **Airtable Automation** (configured in Airtable, not Make) sends:
   ```json
   {
     "source": "airtable",
     "recordId": "recXXXXXX",
     "status": "Confirmed",
     "needsAdjustment": false,
     "studioEmailSent": false,
     "fields": {...}
   }
   ```

3. **Capture Operator** clicks confirmation link:
   ```
   https://hook.us1.make.com/WEBHOOK_ID?source=confirmation&booking_id=123
   ```

#### Router Logic

The Router module examines the incoming data:

**Path A Condition:**
```
{{1.source}} = "calcom"
```

**Path B Condition:**
```
{{1.source}} = "confirmation"
```

**Path C Condition:**
```
{{1.source}} = "airtable"
```

### Airtable Automation Configuration (No-Code)

**Inside Airtable** (not Make.com), create an automation:

**Trigger:** When record matches conditions
- Status = "Confirmed"
- Needs Adjustment = unchecked
- Studio Email Sent = unchecked

**Action:** Send webhook to Make.com
- URL: `https://hook.us1.make.com/WEBHOOK_ID`
- Method: POST
- Body:
```json
{
  "source": "airtable",
  "recordId": "{{RECORD_ID}}",
  "guestName": "{{Guest Name}}",
  "guestEmail": "{{Guest Email}}",
  "additionalEmails": "{{Additional Emails (CC)}}",
  "showDateTime": "{{Show Date/Time}}",
  "platform": "{{Platform Preference}}",
  "topic": "{{Topic}}"
}
```

**Why This Works:**
- Airtable's native automations are free and unlimited
- They can trigger Make.com webhooks
- This removes the need for Make.com to poll Airtable (saves operations)

---

## Scenario 2: Scheduled Checker (Time-Based Events)

### Purpose
Handle all time-based automations that run on a schedule.

### Trigger
**Scheduled:** Runs every 30 minutes (free plan allows 15-minute minimum, but 30 min is safer)

### Combined Workflow

```
SCHEDULED TRIGGER (Every 30 minutes, 8 AM - 8 PM Phoenix time)
    ↓
[Calculate Current Time + 2 hours]
    ↓
[Router Module] - Two parallel paths
    ↓
    ├─→ PATH A: Morning Capture Operator Emails (9:00-9:30 AM only)
    │   ├─ [Filter: Only run if current hour = 9]
    │   ├─ Search Airtable
    │   │  - Show Date = TODAY
    │   │  - Status = "Confirmed"
    │   │  - Needs Adjustment = FALSE
    │   │  - Capture Email Sent = FALSE
    │   ├─ [Iterator: For each matching record]
    │   ├─ [Router: Platform-based email templates]
    │   │  ├─ If Platform = "Zoom" → Send Zoom email template
    │   │  └─ If Platform = "Teams" → Send Teams email template
    │   ├─ Send email via Gmail
    │   │  To: phx-newseditors@graymedia.com
    │   │  CC: derek.staahl@azfamily.com, dstaahl@gmail.com
    │   │  Subject: "Recording Setup - TODAY {{Show Time}} - {{Guest Name}}"
    │   │  Body: [Includes confirmation webhook link]
    │   └─ Update Airtable
    │      - Capture Email Sent = TRUE
    │      - Status = "Capture Notified"
    │
    └─→ PATH B: Missing Confirmation Alerts (Runs every 30 min)
        ├─ Calculate: Current Time + 2 hours
        ├─ Search Airtable
        │  - Show Date/Time < (Current Time + 2 hours)
        │  - Show Date/Time > Current Time
        │  - Status = "Capture Notified"
        │  - Recording Ready = FALSE
        │  - Needs Adjustment = FALSE
        ├─ [Filter: Only proceed if records found]
        ├─ [Iterator: For each matching record]
        ├─ Send alert email to Derek
        │  To: derek@derekstaahl.com
        │  Subject: "⚠️ URGENT - Recording Not Confirmed - {{Guest Name}}"
        └─ Update Airtable (add flag to prevent duplicate alerts)
           - Notes field: Append "Alert sent at {{Current Time}}"
```

### Technical Implementation Details

#### Time-Based Filtering

**PATH A (Morning Emails) Filter:**
```
formatDate(now; "H"; "America/Phoenix") = 9
AND
{{Search Results}} > 0
```

This ensures capture operator emails only send between 9:00-9:30 AM.

#### PATH B (Alerts) Logic

**Search Parameters:**
```
Show Date/Time < addHours(now; 2)
AND
Show Date/Time > now
AND
Status = "Capture Notified"
AND
Recording Ready = FALSE
AND
Needs Adjustment = FALSE
```

**Prevent Duplicate Alerts:**
Check if Notes field already contains "Alert sent" - if yes, skip.

### Operation Efficiency

**Per 30-minute run:**
- Trigger: 1 operation
- Calculate time: 1 operation
- Router: 1 operation
- PATH A (only runs at 9 AM):
  - Search Airtable: 1 operation
  - If no results: STOP (total: 4 operations)
  - If 1 booking found: 
    - Iterator: 1 op
    - Send email: 1 op
    - Update Airtable: 1 op
    - **Total: 7 operations**
- PATH B (runs every 30 min):
  - Search Airtable: 1 operation
  - If no results: STOP (total: 4 operations)
  - If 1 alert needed:
    - Iterator: 1 op
    - Send email: 1 op
    - Update Airtable: 1 op
    - **Total: 7 operations**

**Daily Operation Count:**
- Runs per day: 26 (every 30 min from 8 AM - 8 PM)
- Base operations: 26 × 4 = 104 operations/day
- One booking at 9 AM: +3 operations
- One alert during day: +3 operations
- **Daily total: ~110 operations**
- **Monthly total: ~3,300 operations**

**Free plan gives 1,000 operations/month** ⚠️

---

## PROBLEM: Free Plan Operation Limits

### The Math Problem

With our current design:
- **Estimated monthly operations:** 3,300
- **Free plan limit:** 1,000
- **Overage:** 2,300 operations ❌

### Solution: Reduce Scheduled Scenario Frequency

**Option 1: Run 3 times per day (Recommended)**

Instead of every 30 minutes, run at specific times:
- **9:00 AM:** Morning capture operator emails
- **12:00 PM:** Midday alert check
- **4:00 PM:** Afternoon alert check

**New operation count:**
- 3 runs/day × 30 days = 90 runs/month
- Average 7 operations per run = 630 operations/month
- Webhook scenario (Scenario 1): ~100 operations/month
- **Total: ~730 operations/month** ✅ Under 1,000 limit

**Trade-off:** Alert emails only check 3 times per day instead of every 30 minutes. Still catches issues with 2-5 hours notice before show.

**Option 2: Only run on show days**

Configure Scenario 2 to:
1. Check Airtable for shows scheduled TODAY
2. If no shows today, stop immediately (1 operation)
3. If shows today, run the full logic

**Problem:** Still need to check every day to know if there are shows (30 operations/month base), plus the actual processing days.

**Option 3: Manual trigger for alerts**

- Scenario 2 ONLY sends morning capture emails at 9 AM (daily check)
- You manually check Airtable for recording confirmations 2 hours before show
- No automated alerts

---

## REVISED FINAL DESIGN (Fits Free Plan)

### Scenario 1: Webhook Handler (Unchanged)
- Handles: New bookings, confirmations, studio emails
- Operations: ~100-150/month
- Status: ✅ Efficient

### Scenario 2: Morning Email Sender (Simplified)

**Trigger:** Daily at 9:00 AM (America/Phoenix)

**Workflow:**
```
SCHEDULED TRIGGER (9:00 AM daily)
    ↓
Search Airtable
  - Show Date = TODAY
  - Status = "Confirmed"
  - Needs Adjustment = FALSE
  - Capture Email Sent = FALSE
    ↓
[Filter: Only proceed if records found]
    ↓
[Iterator: For each record]
    ↓
[Router: Platform-based templates]
  ├─ Zoom template
  └─ Teams template
    ↓
Send Email via Gmail
  To: phx-newseditors@graymedia.com
  CC: derek.staahl@azfamily.com, dstaahl@gmail.com
  Subject: "Recording Setup - TODAY {{Show Time}}"
  Body: [Full instructions + confirmation link]
    ↓
Update Airtable
  - Capture Email Sent = TRUE
  - Status = "Capture Notified"
```

**Operations per day:**
- No shows today: 3 operations (trigger + search + stop)
- 1 show today: 7 operations (trigger + search + iterator + router + email + update)
- 2 shows today: 10 operations

**Monthly operations:**
- 30 days × 3 ops (average) = 90 operations
- ~4 show days/month × 4 extra ops = 16 operations
- **Total: ~106 operations/month** ✅

### Manual Alert System (Replaces Automated Alerts)

**In Airtable, create a View:**
- Name: "⚠️ URGENT - Needs Follow-up"
- Filter:
  - Show Date/Time is TODAY
  - Show Date/Time is within next 2 hours
  - Status = "Capture Notified"
  - Recording Ready = FALSE

**Your process:**
- Check this view when you arrive at work (or set a phone reminder)
- If any records appear, manually follow up with capture operators

**Alternative:** Set up a personal automation on your phone using iOS Shortcuts or Android Tasker to check Airtable via API and send you a notification. This uses YOUR resources, not Make.com operations.

---

## Updated Operation Budget (Free Plan Viable)

### Scenario 1: Webhook Handler
**Monthly operations:**
- 4 new bookings: 4 × 7 ops = 28 operations
- 4 confirmations: 4 × 6 ops = 24 operations
- 4 studio emails (via Airtable webhook): 4 × 5 ops = 20 operations
- **Subtotal: 72 operations/month**

### Scenario 2: Morning Capture Emails
**Monthly operations:**
- 30 daily checks: 30 × 3 ops = 90 operations
- 4 show days with emails: 4 × 4 ops = 16 operations
- **Subtotal: 106 operations/month**

### Grand Total: ~178 operations/month ✅

**Free plan limit:** 1,000 operations
**Usage:** 178 operations (17.8%)
**Headroom:** 822 operations for growth

---

## Trade-offs of Free Plan Design

### What You Lose
❌ Automated 2-hour alerts before show (replaced with manual Airtable view check)
❌ Continuous monitoring (only checks at 9 AM)

### What You Keep
✅ Automatic booking creation from Cal.com
✅ Automatic studio emails when you confirm bookings
✅ Automatic capture operator emails at 9 AM on show days
✅ Automatic recording confirmations via webhook
✅ Email notifications to you for all key events

### Mitigation Strategies

**For Missing Alerts:**
1. **Set phone reminders:** 2 hours before typical show times (11:30 AM for 1:30 PM shows, 5:30 PM for 7:30 PM shows)
2. **Check Airtable view:** Takes 10 seconds to see if recording is confirmed
3. **Bookmark the view:** Make it one-click accessible

**For Continuous Monitoring:**
- The 9 AM email gives operators 4.5 hours for 1:30 PM shows
- That's plenty of time for setup
- If they haven't confirmed by your manual check, you still have 2 hours to fix it

---

## Complete Implementation Guide

### Phase 1: Airtable Setup
(Unchanged from original spec - run the Python script)

### Phase 2: Airtable Native Automation

**Create Automation in Airtable:**

1. In your Airtable base, click "Automations" (top right)
2. Click "Create automation"
3. Name: "Trigger Studio Email"
4. **Trigger:** When record matches conditions
   - Status is "Confirmed"
   - Needs Adjustment is unchecked
   - Studio Email Sent is unchecked
5. **Action:** Send webhook request
   - URL: `https://hook.us1.make.com/WEBHOOK_ID` (you'll get this from Make.com)
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "source": "airtable",
     "recordId": "{{RECORD_ID()}}",
     "guestName": "{{Guest Name}}",
     "guestEmail": "{{Guest Email}}",
     "additionalEmails": "{{Additional Emails (CC)}}",
     "showDateTime": "{{Show Date/Time}}",
     "platform": "{{Platform Preference}}",
     "topic": "{{Topic}}"
   }
   ```
6. Turn automation ON

### Phase 3: Make.com Setup

#### Scenario 1: Create Webhook Handler

1. Go to Make.com → Create new scenario
2. Name: "Generation AI - Webhook Handler"
3. Add module: **Webhooks > Custom webhook**
   - Create new webhook
   - Copy webhook URL (you'll need this for Cal.com and Airtable)
4. Add module: **Router**
   - Connect after webhook
5. **Create Route 1 (Cal.com Bookings):**
   - Set filter: `source` equals `calcom`
   - Add module: **Airtable > Create a record**
     - Map fields from webhook data
   - Add module: **Gmail > Send an email**
     - To: derek@derekstaahl.com
     - Subject: New Booking: `{{guestName}}` on `{{showDateTime}}`
6. **Create Route 2 (Recording Confirmations):**
   - Set filter: `source` equals `confirmation`
   - Add module: **Airtable > Search records**
     - Filter: Booking ID equals `{{1.booking_id}}`
   - Add module: **Airtable > Update a record**
     - Recording Ready: TRUE
     - Status: "Recording Ready"
   - Add module: **Gmail > Send an email**
     - To: derek@derekstaahl.com
     - Subject: ✅ Recording Ready
   - Add module: **Webhook response**
     - Status: 200
     - Body: `<html><body><h1>✓ Confirmed</h1></body></html>`
7. **Create Route 3 (Studio Emails):**
   - Set filter: `source` equals `airtable`
   - Add module: **Gmail > Send an email**
     - To: phx-studiorequests@graymedia.com
     - Subject: Studio Booking Request
   - Add module: **Airtable > Update a record**
     - Studio Email Sent: TRUE
8. Save and activate scenario

#### Scenario 2: Create Morning Email Sender

1. Create new scenario
2. Name: "Generation AI - Morning Capture Emails"
3. Add module: **Schedule > Every day**
   - Time: 9:00 AM
   - Timezone: America/Phoenix
4. Add module: **Airtable > Search records**
   - Formula:
   ```
   AND(
     IS_SAME({Show Date/Time}, TODAY(), 'day'),
     {Status} = 'Confirmed',
     NOT({Needs Adjustment}),
     NOT({Capture Email Sent})
   )
   ```
5. Add module: **Filter**
   - Condition: Total bundles > 0
6. Add module: **Iterator**
   - Array: Results from Airtable search
7. Add module: **Router**
   - **Route 1:** Platform equals "Zoom"
     - Add module: **Gmail > Send an email** (Zoom template)
       - To: phx-newseditors@graymedia.com
       - CC: derek.staahl@azfamily.com, dstaahl@gmail.com
   - **Route 2:** Platform equals "Teams"
     - Add module: **Gmail > Send an email** (Teams template)
       - To: phx-newseditors@graymedia.com
       - CC: derek.staahl@azfamily.com, dstaahl@gmail.com
8. After router convergence, add module: **Airtable > Update a record**
   - Capture Email Sent: TRUE
   - Status: "Capture Notified"
9. Save and activate scenario

### Phase 4: Cal.com Setup
(Follow original spec for Cal.com deployment and configuration)

**Add webhook to Cal.com:**
- URL: The webhook URL from Make.com Scenario 1
- Trigger: Booking created
- Payload: Include all booking data
- Custom field in body: `"source": "calcom"`

### Phase 5: Update Airtable Formula

Update the "Confirmation Webhook URL" field formula:
```
CONCATENATE('https://hook.us1.make.com/ACTUAL_WEBHOOK_ID?source=confirmation&booking_id=', {Booking ID})
```

### Phase 6: Create Manual Alert View in Airtable

1. Click "+" to create new view
2. Name: "⚠️ URGENT - Check Before Show"
3. View type: Grid
4. Filters:
   - Show Date/Time is TODAY
   - Show Date/Time is within the next 2 hours
   - Status is "Capture Notified"
   - Recording Ready is unchecked
5. Sort by: Show Date/Time (ascending)
6. Save view

**Bookmark this view** for quick access on show days.

---

## Email Templates

### Studio Request Email
```
Subject: Studio Booking Request - Generation AI - {{Show Date}}

Hi Studio Team,

Please reserve the studio for the following Generation AI taping:

Date: {{Show Date}}
Time: {{Show Time}}
Duration: 90 minutes (includes setup/breakdown)

Guest: {{Guest Name}}
Format: Virtual guest via {{Platform Preference}}

Please confirm this booking is locked into the studio calendar.

Thanks,
Derek Staahl
Generation AI
```

### Capture Operator Email (Zoom)
```
Subject: Generation AI Recording Setup - TODAY {{Show Time}} - {{Guest Name}}

Hi Capture Team,

Today's Generation AI guest taping requires the following setup:

SHOW DETAILS:
Time: {{Show Time}} ({{Show Date}})
Guest: {{Guest Name}}
Platform: Zoom

REQUIRED ACTIONS:
1. Create Zoom meeting for {{Show Time}}
2. Send Zoom link to: {{Guest Email}}
   {{#if Additional Emails}}CC: {{Additional Emails}}{{/if}}
3. Set up full show output recording
4. Set up ISO recording on guest feed only

When setup is complete, please click here to confirm:
{{Confirmation Webhook URL}}

If any issues, contact Derek immediately.

Topic: {{Topic}}

Thanks,
Derek
```

### Capture Operator Email (Teams)
```
[Same as Zoom template, but replace "Zoom" with "Microsoft Teams"]
```

---

## Testing Checklist

### Test Scenario 1
- [ ] Cal.com booking creates Airtable record
- [ ] Derek receives booking notification email
- [ ] Airtable automation triggers when status → Confirmed
- [ ] Studio email sends correctly
- [ ] Studio Email Sent checkbox updates
- [ ] Recording confirmation webhook works
- [ ] Recording Ready checkbox updates
- [ ] Derek receives confirmation email
- [ ] Operator sees confirmation page

### Test Scenario 2
- [ ] Manually trigger at 9 AM (or adjust time for testing)
- [ ] Scenario finds today's shows
- [ ] Correct email template used (Zoom vs Teams)
- [ ] Email sent to capture operators
- [ ] Airtable updated correctly
- [ ] Status changed to "Capture Notified"

### Test Manual Alert System
- [ ] Create test record with show in 1 hour
- [ ] Set Status = "Capture Notified"
- [ ] Set Recording Ready = FALSE
- [ ] Open "⚠️ URGENT" view
- [ ] Verify record appears
- [ ] Mark Recording Ready = TRUE
- [ ] Verify record disappears from view

---

## Operation Monitoring

### How to Check Your Usage

1. Go to Make.com dashboard
2. Click "Organizations" → Your organization
3. View "Operations usage" chart
4. Monitor daily/monthly consumption

### Warning Thresholds

- **80% (800 operations):** Review what's consuming operations
- **90% (900 operations):** Stop non-essential scenarios
- **100% (1,000 operations):** All scenarios pause until next month

### Optimization Tips

1. **Reduce unnecessary runs:** If you're not having shows on weekends, pause Scenario 2 on Sat/Sun
2. **Use filters aggressively:** Every filter that stops a workflow early saves operations
3. **Batch updates:** Instead of updating Airtable multiple times, combine updates into one action

---

## Cost Analysis - Free Plan

### Ongoing Costs

| Item | Cost |
|------|------|
| Airtable | $0/month (free tier) |
| Make.com | $0/month (free tier) |
| Railway (Cal.com) | $0/month (under $5 usage) |
| Gmail API | $0/month (free) |
| Netlify | $0/month (existing) |
| **TOTAL** | **$0/month** |

### Time Investment

- **Setup:** ~6-7 hours (slightly less than paid plan due to simpler logic)
- **Monthly maintenance:** ~30 minutes
  - Daily Airtable check: 5 min/week = 20 min/month
  - Show day manual checks: 2 min/show × 4 shows = 8 min/month
  - Monthly review: 5 minutes

### Value Proposition

- **Time saved:** ~88 hours/year (slightly less than paid plan)
- **Cost:** $0
- **ROI:** Infinite (no money spent)

---

## Upgrade Path (When Needed)

### Indicators You Should Upgrade to Core ($9/month)

1. **Show frequency increases** to 2+ per week (8+ shows/month)
2. **Operations approaching 1,000/month**
3. **You want automated alerts** instead of manual checks
4. **You want minute-level scheduling** for more responsive automations

### Easy Migration

If you upgrade later:
- Add back automated alert checking (Scenario 3 from original spec)
- Increase scheduled frequency from daily to hourly
- Split complex scenarios for easier maintenance
- Everything else stays the same

---

## Conclusion

This **2-scenario design** successfully fits within Make.com's free plan while maintaining ~95% of the automation value:

✅ Automated booking creation
✅ Automated studio emails
✅ Automated capture operator emails
✅ Automated recording confirmations
✅ Email notifications for all events

The only trade-off is manual checking for recording confirmations 2 hours before show, which takes 10 seconds and can be part of your pre-show routine anyway.

**Total monthly cost: $0**
**Time saved: ~88 hours/year**
**Complexity: Medium (but well within your technical comfort zone)**

Ready to implement? Start with Phase 1 (Airtable setup) and work through the phases sequentially.
