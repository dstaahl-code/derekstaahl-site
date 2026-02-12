# Generation AI Guest Booking System - Complete Technical Specification

**Version:** 1.0
**Last Updated:** January 26, 2026
**Purpose:** Documentation for developers building a UI dashboard on top of this system

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Airtable Schema](#airtable-schema)
3. [Cal.com Integration](#calcom-integration)
4. [Make.com Automation Scenarios](#makecom-automation-scenarios)
5. [Airtable Automations](#airtable-automations)
6. [Email Templates](#email-templates)
7. [Workflow & Status Lifecycle](#workflow--status-lifecycle)
8. [API Credentials & Endpoints](#api-credentials--endpoints)
9. [Dashboard Requirements](#dashboard-requirements)

---

## System Overview

**Generation AI** is a 30-minute pre-taped weekly digital show about artificial intelligence, hosted by Derek Staahl at Arizona's Family (3TV/CBS5) in Phoenix.

### Core Components

| Component | Purpose |
|-----------|---------|
| **Cal.com** | Guest self-scheduling via booking link |
| **Airtable** | Central database for guest records, status tracking |
| **Make.com** | Automation orchestration (webhooks, emails, record updates) |
| **Airtable Automations** | Check-in emails (4 days before show) |
| **Gmail** | Email delivery for notifications |

### Data Flow

```
Cal.com Booking → Make.com Webhook → Airtable Record Created
                                          ↓
                         Status: "Pending Confirmation"
                                          ↓
                    (Host confirms in Airtable or via dashboard)
                                          ↓
                         Status: "Confirmed"
                                          ↓
              Airtable Automation sends check-in email (4 days out)
                                          ↓
              Make.com sends capture team email (day of show, 9 AM)
                                          ↓
                         Status: "Capture Notified"
                                          ↓
              Recording confirmed via webhook → Status: "Recording Ready"
                                          ↓
                         Status: "Complete"
```

---

## Airtable Schema

### Base Information

| Property | Value |
|----------|-------|
| **Base Name** | Generation AI |
| **Table Name** | Guests (primary table) |
| **Base ID** | `appXXXXXXXXXXXXXX` (obtain from Airtable API docs) |
| **Table ID** | `tblXXXXXXXXXXXXXX` (obtain from Airtable API docs) |

### Fields

| Field Name | Type | Options/Formula | Description |
|------------|------|-----------------|-------------|
| **Guest Name** | Single line text | — | Full name of guest |
| **Guest Email** | Email | — | Primary contact email |
| **Additional Emails** | Single line text | — | CC recipients (comma-separated) |
| **Show Date/Time** | Date & Time | Include time | Scheduled appearance date/time |
| **Platform Preference** | Single select | `Zoom`, `In-Person`, `Phone` | Guest's preferred platform (legacy) |
| **Guest Type** | Single select | `Virtual (via Zoom)`, `In studio` | Determines email template variant |
| **Topic** | Single line text | — | Discussion topic/segment focus |
| **Status** | Single select | See [Status Values](#status-values) | Current booking state |
| **Needs Adjustment** | Checkbox | — | Flag for bookings requiring host review |
| **Studio Email Sent** | Checkbox | — | Tracks if front desk was notified (in-studio) |
| **Capture Email Sent** | Checkbox | — | Tracks if capture team was notified |
| **Check-in Email Sent** | Checkbox | — | Tracks if 4-day check-in email was sent |
| **Recording Ready** | Checkbox | — | Confirmed recording is available |
| **Booking ID** | Single line text | — | Unique identifier from Cal.com |
| **Notes** | Long text | — | Internal notes about the booking |
| **Confirmation Webhook URL** | URL | — | Webhook to trigger on status change |
| **Cal.com Event ID** | Single line text | — | Cal.com's internal event identifier |
| **First Name** | Formula | See below | Extracted first name for email personalization |
| **Day of Week** | Formula | See below | Day name (e.g., "Tuesday") for emails |

### Formula Fields

**First Name:**
```
IF(FIND(' ', {Guest Name}), LEFT({Guest Name}, FIND(' ', {Guest Name}) - 1), {Guest Name})
```

**Day of Week:**
```
DATETIME_FORMAT({Show Date/Time}, 'dddd')
```

### Status Values

| Status | Description | Triggered By |
|--------|-------------|--------------|
| `Pending Confirmation` | Guest booked, awaiting host approval | Cal.com webhook |
| `Confirmed` | Host approved the booking | Manual or dashboard action |
| `Capture Notified` | Capture team email sent | Make.com Scenario 2 |
| `Recording Ready` | Recording confirmed available | Recording webhook |
| `Complete` | Segment finished/aired | Manual or dashboard action |
| `Cancelled` | Booking cancelled | Manual or Cal.com cancellation |

---

## Cal.com Integration

### Booking Link

Guests book via a Cal.com scheduling link. When a booking is created:

1. Cal.com sends webhook payload to Make.com
2. Make.com creates Airtable record with status `Pending Confirmation`
3. Host receives notification of new booking

### Webhook Payload (Cal.com → Make.com)

Key fields from Cal.com webhook:

```json
{
  "triggerEvent": "BOOKING_CREATED",
  "payload": {
    "uid": "abc123...",
    "title": "Generation AI Interview",
    "startTime": "2026-02-01T14:00:00Z",
    "endTime": "2026-02-01T15:00:00Z",
    "attendees": [
      {
        "name": "Jane Doe",
        "email": "jane@example.com"
      }
    ],
    "responses": {
      "topic": "AI in Healthcare",
      "platform": "Zoom"
    }
  }
}
```

---

## Make.com Automation Scenarios

### Scenario 1: Webhook Handler (Multi-Path Router)

**Trigger:** Webhook receives incoming request
**Webhook URL:** `https://hook.us2.make.com/[YOUR_WEBHOOK_ID]`

#### Router Paths

| Path | Condition | Action |
|------|-----------|--------|
| **Path 1: Cal.com Booking** | `triggerEvent` = `BOOKING_CREATED` | Create Airtable record, set Status = "Pending Confirmation" |
| **Path 2: Recording Confirmation** | `type` = `recording_ready` | Find record by Booking ID, set Recording Ready = TRUE, update Status |
| **Path 3: Status Change** | `source` = `airtable_status_change` | Process status-triggered workflows |

### Scenario 2: Daily Capture Team Notification

**Trigger:** Scheduled daily at 9:00 AM Arizona time
**Purpose:** Notify capture team and front desk about same-day guests

#### Flow

```
Schedule (9 AM AZ)
    → Search Airtable: Show Date = TODAY, Status = "Confirmed", Capture Email Sent = FALSE
    → Filter: Records found (Record ID exists)
    → Router
        ├── Path 1: Virtual guests → Send capture team email
        └── Path 2: In-studio guests → Send capture email + front desk notification
    → Update record: Capture Email Sent = TRUE, Status = "Capture Notified"
```

#### Email Recipients

| Recipient | Email | Purpose |
|-----------|-------|---------|
| Capture Team | `phx-studiorequests@graymedia.com` | Zoom link coordination |
| News Editors (Front Desk) | `phx-newseditors@graymedia.com` | In-studio guest arrival |
| Derek Staahl (Work) | `derek.staahl@azfamily.com` | CC on notifications |
| Derek Staahl (Personal) | `dstaahl@gmail.com` | Testing/backup |

---

## Airtable Automations

Two native Airtable automations handle guest check-in emails 4 days before their appearance.

### Automation #1: Virtual Guest Check-in Email

**Trigger Type:** When record matches conditions (scheduled check)

**Conditions:**
- Show Date/Time = exactly 4 days from today
- Status = `Confirmed`
- Guest Type = `Virtual (via Zoom)`
- Check-in Email Sent = FALSE (unchecked)
- Needs Adjustment = FALSE (unchecked)

**Actions:**
1. Send email (see [Virtual Guest Email Template](#virtual-guest-email))
2. Update record: Check-in Email Sent = TRUE

### Automation #2: In-Studio Guest Check-in Email

**Trigger Type:** When record matches conditions (scheduled check)

**Conditions:**
- Show Date/Time = exactly 4 days from today
- Status = `Confirmed`
- Guest Type = `In studio`
- Check-in Email Sent = FALSE (unchecked)
- Needs Adjustment = FALSE (unchecked)

**Actions:**
1. Send email (see [In-Studio Guest Email Template](#in-studio-guest-email))
2. Update record: Check-in Email Sent = TRUE

---

## Email Templates

### Capture Team Email (Day-of)

**To:** `phx-studiorequests@graymedia.com`
**CC:** `derek.staahl@azfamily.com`
**Subject:** `Generation AI Zoom Guest - {Guest Name} - {Show Date formatted}`

```
Hi Capture Team,

We have a virtual guest scheduled for Generation AI today.

GUEST DETAILS
Name: {Guest Name}
Email: {Guest Email}
Topic: {Topic}
Time: {Show Date/Time formatted}

Please send the Zoom link to the guest before 11 AM Arizona time.

Thank you,
Derek Staahl
```

### Front Desk Notification (In-Studio Guests)

**To:** `phx-newseditors@graymedia.com`
**CC:** `derek.staahl@azfamily.com`
**Subject:** `IN-STUDIO GUEST TODAY - {Guest Name} for Generation AI`

```
Hi,

We have an in-studio guest arriving today for Generation AI.

GUEST: {Guest Name}
EXPECTED ARRIVAL: {Show Date/Time formatted}
PURPOSE: Generation AI interview

Please direct them to the lobby - I'll meet them there.

Thanks,
Derek Staahl
```

### Virtual Guest Email (4 Days Before) {#virtual-guest-email}

**To:** `{Guest Email}` (currently `dstaahl@gmail.com` for testing)
**Subject:** `Looking forward to Generation AI on {Show Date/Time formatted}`

```
Hi {First Name},

We're excited to have you on Generation AI this {Day of Week}!

A few quick logistics:

BEFORE YOUR SEGMENT
On the morning of your segment, you'll receive an email from our capture team with a Zoom link. This email should arrive before 11 AM Arizona time. If you don't see it by then, please let me know.

SHOW FORMAT
Generation AI is a 30-minute show that's pre-taped and streamed later. Segment length varies, but please budget about one hour total for setup and any technical checks.

OPTIONAL: VISUALS
Since we're always looking for ways to make the show more visually engaging, feel free to send along any video clips, images, or product demos that might help illustrate your story—particularly if you're representing a business with an AI-related product. No pressure if this doesn't apply to you!

Looking forward to the conversation.

Best,
Derek Staahl
```

### In-Studio Guest Email (4 Days Before) {#in-studio-guest-email}

**To:** `{Guest Email}` (currently `dstaahl@gmail.com` for testing)
**Subject:** `Looking forward to Generation AI on {Show Date/Time formatted}`

```
Hi {First Name},

We're excited to have you on Generation AI this {Day of Week}!

A few quick logistics:

STUDIO LOCATION
Arizona's Family Studios
5555 N. 7th Avenue
Phoenix, AZ 85013

PARKING & ARRIVAL
Please park in the front parking lot, near the flagpole and large glass doors. Our security staff (usually a nice guy named Paul) will be expecting you, but feel free to mention you're here for an interview with Derek Staahl on Generation AI. I'll meet you in the lobby.

If you encounter any issues, feel free to call or text my cell: [YOUR CELL NUMBER]

SHOW FORMAT
Generation AI is a 30-minute show that's pre-taped and streamed later. Segment length varies, but please budget about one hour total for setup and any technical checks.

OPTIONAL: VISUALS
Since we're always looking for ways to make the show more visually engaging, feel free to send along any video clips, images, or product demos that might help illustrate your story—particularly if you're representing a business with an AI-related product. No pressure if this doesn't apply to you!

Looking forward to meeting you in person.

Best,
Derek Staahl
```

---

## Workflow & Status Lifecycle

### Complete Guest Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                        BOOKING PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Guest visits Cal.com booking link                           │
│  2. Selects date/time, enters name, email, topic                │
│  3. Cal.com sends webhook → Make.com Scenario 1                 │
│  4. Airtable record created: Status = "Pending Confirmation"    │
│  5. Host reviews in Airtable or dashboard                       │
│  6. Host sets Status = "Confirmed" (or "Cancelled")             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CHECK-IN PHASE (4 days before)             │
├─────────────────────────────────────────────────────────────────┤
│  7. Airtable Automation triggers                                │
│  8. Check-in email sent based on Guest Type                     │
│  9. Check-in Email Sent = TRUE                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DAY-OF PHASE (9 AM)                        │
├─────────────────────────────────────────────────────────────────┤
│  10. Make.com Scenario 2 runs at 9 AM                           │
│  11. Searches for today's confirmed guests                      │
│  12. Sends capture team email (all guests)                      │
│  13. Sends front desk notification (in-studio only)             │
│  14. Capture Email Sent = TRUE, Status = "Capture Notified"     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      POST-RECORDING PHASE                       │
├─────────────────────────────────────────────────────────────────┤
│  15. Recording webhook triggers Make.com Scenario 1 (Path 2)    │
│  16. Recording Ready = TRUE, Status = "Recording Ready"         │
│  17. Host marks Status = "Complete" after airing                │
└─────────────────────────────────────────────────────────────────┘
```

### Status Transition Rules

| From Status | To Status | Triggered By |
|-------------|-----------|--------------|
| — | Pending Confirmation | Cal.com booking webhook |
| Pending Confirmation | Confirmed | Host approval |
| Pending Confirmation | Cancelled | Host or guest cancellation |
| Confirmed | Capture Notified | Make.com Scenario 2 (day-of) |
| Confirmed | Cancelled | Host or guest cancellation |
| Capture Notified | Recording Ready | Recording confirmation webhook |
| Recording Ready | Complete | Host marks complete |

---

## API Credentials & Endpoints

### Airtable API

| Property | Value |
|----------|-------|
| API Base URL | `https://api.airtable.com/v0/{baseId}/{tableName}` |
| Authentication | Bearer token (Personal Access Token) |
| Base ID | Obtain from Airtable API documentation |
| Table Name | `Guests` |

**Required Scopes:**
- `data.records:read`
- `data.records:write`
- `schema.bases:read`

### Make.com Webhook

| Property | Value |
|----------|-------|
| Primary Webhook URL | `https://hook.us2.make.com/[YOUR_WEBHOOK_ID]` |
| Method | POST |
| Content-Type | application/json |

### Cal.com

Cal.com is configured to send webhooks to Make.com on booking events. No direct API access is currently used.

---

## Dashboard Requirements

### Core Features for Dashboard

1. **Guest List View**
   - Display all records from Airtable Guests table
   - Sort by Show Date/Time (upcoming first)
   - Filter by Status
   - Search by Guest Name or Email

2. **Guest Detail View**
   - Show all fields for a single record
   - Edit capability for: Status, Guest Type, Topic, Notes, Needs Adjustment
   - Read-only display for: formula fields, checkbox tracking fields

3. **Status Management**
   - Dropdown to change Status
   - When changing to "Confirmed", validate Guest Type is set
   - Color-code status badges

4. **Calendar View**
   - Display guests on a calendar by Show Date/Time
   - Click to open Guest Detail View

5. **Notifications Panel**
   - Show upcoming check-in emails (guests 4-5 days out, not yet sent)
   - Show today's capture notifications
   - Flag records where Needs Adjustment = TRUE

### API Operations Needed

| Operation | Airtable API Endpoint | Method |
|-----------|----------------------|--------|
| List all guests | `/Guests` | GET |
| Get single guest | `/Guests/{recordId}` | GET |
| Update guest | `/Guests/{recordId}` | PATCH |
| Create guest (manual add) | `/Guests` | POST |
| Delete guest | `/Guests/{recordId}` | DELETE |

### Filtering Examples

**Upcoming confirmed guests:**
```
filterByFormula: AND({Status}='Confirmed', {Show Date/Time}>=TODAY())
```

**Today's guests:**
```
filterByFormula: IS_SAME({Show Date/Time}, TODAY(), 'day')
```

**Guests needing attention:**
```
filterByFormula: {Needs Adjustment}=TRUE()
```

### Webhook Integration (Optional)

If the dashboard needs real-time updates, configure an Airtable automation to send a webhook to the dashboard when records change.

---

## Notes for Developers

1. **Testing Mode:** Check-in emails currently route to `dstaahl@gmail.com` instead of guest emails. Update Airtable automations when ready for production.

2. **Cell Phone Placeholder:** The in-studio email template contains `[YOUR CELL NUMBER]` - this needs to be replaced with the actual number in the Airtable automation.

3. **Timezone:** All times are in Arizona time (MST, no daylight saving). The studio operates on Mountain Standard Time year-round.

4. **Make.com Free Tier:** Current setup uses ~60-100 operations/month. Make.com free tier allows 1,000 operations/month. Check-in emails use Airtable Automations (free) to preserve Make.com headroom.

5. **Checkbox Fields:** Never manually set `Capture Email Sent`, `Studio Email Sent`, or `Check-in Email Sent` to TRUE unless bypassing the automation intentionally. These track automation state.

6. **Guest Type Required:** For check-in emails to work, `Guest Type` must be set to either "Virtual (via Zoom)" or "In studio" before the 4-day window.

---

## Contact

**System Owner:** Derek Staahl
**Email:** derek.staahl@azfamily.com
**Personal:** dstaahl@gmail.com
