# Personal OS: Financial Safety Rules

**Document Version**: 1.0.0  
**Last Updated**: 2024-10-04  
**Purpose**: Enforce strict safeguards for autonomous financial operations in the Purchases subsystem

---

## 1. Core Principle: Zero Autonomous Financial Commitment

**RULE**: No automated agent, workflow, or background process may commit funds, authorize payments, or finalize financial transactions without explicit interactive human approval.

### Prohibited Autonomous Actions
- Executing payment to any merchant or service
- Authorizing recurring subscription charges
- Purchasing goods or services (digital or physical)
- Transferring funds between accounts
- Modifying payment methods or billing information
- Closing or canceling accounts with outstanding balances
- Accepting refund settlements below dispute amounts

### Permitted Autonomous Actions (Informational Only)
- Parsing receipt images via OCR
- Logging expense records to local ledger
- Calculating budget status and spending trends
- Detecting recurring subscription patterns
- Generating alerts for upcoming renewals or budget overages
- Aggregating transaction history from read-only bank/credit card APIs

---

## 2. Human-in-the-Loop (HITL) Financial Approval Queue

### Approval Workflow

All financial operations requiring user authorization are queued in:
```
user/hitl/financial_authorization_queue.md
```

#### Queue Entry Format
```markdown
## Financial Authorization Request #FA-20241004-001

**Request ID**: `fa_a3f9c8d2e1b4`
**Timestamp**: 2024-10-04 14:32:18 UTC
**Requesting Agent**: `agent_finance_tracker`
**Operation**: Purchase Authorization
**Vendor**: Stripe (Monthly Subscription)
**Amount**: $29.00 USD
**Category**: Software/SaaS
**Recurring**: Yes (Monthly)
**Next Charge Date**: 2024-11-04

### Details
- Service: GitHub Copilot Pro Subscription
- Account: lakhwinder@example.com
- Payment Method: Visa ending in 4242

### Risk Assessment
- ✅ Vendor recognized in transaction history
- ✅ Amount matches expected monthly charge
- ⚠️  New payment method detected (added 2024-10-03)

### Actions
- [ ] **APPROVE** - Authorize this transaction
- [ ] **DENY** - Block this transaction
- [ ] **DEFER** - Ask me again in 24 hours
- [ ] **POLICY** - Create auto-approval rule for future identical charges

**Timeout**: This request expires in 48 hours. After timeout, transaction is automatically DENIED.
```

### Approval Mechanisms
1. **CLI Approval**: `pos hitl approve fa_a3f9c8d2e1b4 --reason "Authorized GitHub Copilot renewal"`
2. **Web Dashboard**: Click "Approve" button in pending approvals panel
3. **Voice Confirmation**: (Future) "Kiro, approve financial request FA-001"

---

## 3. Tiered Authorization Thresholds

Different transaction amounts require different approval workflows:

| Amount (USD) | Approval Required | Timeout | Auto-Deny After |
|--------------|-------------------|---------|-----------------|
| $0.01 - $10.00 | Single confirmation | 24 hours | 72 hours |
| $10.01 - $100.00 | Confirmation + reason | 48 hours | 7 days |
| $100.01 - $500.00 | Confirmation + reason + budget check | 72 hours | 7 days |
| $500.01+ | Confirmation + two-factor auth | No timeout | Manual only |

### Policy-Based Auto-Approval
Users can create standing authorization policies:
```yaml
# user/inputs/financial_policies.yaml
auto_approve_rules:
  - name: "Monthly SaaS Subscriptions"
    conditions:
      vendor_matches: ["GitHub", "OpenAI", "Anthropic", "Vercel"]
      transaction_type: "recurring_subscription"
      amount_max_cents: 5000  # $50.00
      frequency: "monthly"
    action: "auto_approve"
    requires_notification: true

  - name: "Micro-transactions"
    conditions:
      amount_max_cents: 100  # $1.00
      category: "digital_content"
    action: "auto_approve"
    requires_notification: false
```

---

## 4. Receipt Validation & Fraud Detection

### Automated Receipt Validation
When a receipt is ingested via OCR:

1. **Extract Structured Data**:
   - Vendor name and address
   - Transaction date and time
   - Line items with quantities and prices
   - Subtotal, tax, tip, total
   - Payment method (last 4 digits)

2. **Cross-Reference with Bank Statements**:
   - Match receipt total against imported bank transactions
   - Flag discrepancies (e.g., receipt shows $45.99 but bank charged $49.99)

3. **Fraud Detection Heuristics**:
   - ⚠️ **Duplicate Charge**: Same vendor, amount, and date as existing record
   - ⚠️ **Unusual Amount**: 3σ above typical spending for category
   - ⚠️ **Unrecognized Vendor**: No prior transaction history
   - ⚠️ **Off-Hours Transaction**: Purchase at 3:00 AM when user typically inactive
   - 🚨 **Suspicious Vendor Name**: Contains known scam keywords ("VERIFY ACCOUNT", "URGENT PAYMENT")

### Quarantine & Review
Flagged transactions move to:
```
user/hitl/suspicious_transactions_review.md
```

---

## 5. Subscription Lifecycle Management

### Subscription Detection
The system automatically detects recurring subscriptions by analyzing:
- Transaction patterns (same vendor + similar amount + regular interval)
- Merchant category codes (MCCs) indicating subscription services
- Vendor names containing "SUBSCRIPTION", "MEMBERSHIP", "MONTHLY"

### Renewal Alerts
**7 days before renewal**:
```
📅 Upcoming Renewal: Notion Pro ($10/month)
Next charge: 2024-10-11
Annual cost: $120.00

Actions:
- [ ] Keep subscription
- [ ] Cancel before renewal
- [ ] Downgrade to free tier
- [ ] Snooze reminder for 3 months
```

### Forgotten Subscription Detection
If a subscription has not been actively used (no app launches, no API calls, no related files accessed) for 60 days:
```
⚠️  Potentially Unused Subscription Detected

Service: Adobe Creative Cloud ($52.99/month)
Last known usage: 2024-06-15
Total charged (unused period): $158.97

Recommendation: Consider canceling to save $635.88/year
```

---

## 6. Budget Envelope System

Users define budget envelopes (categories with spending limits):

```yaml
# user/inputs/budget_envelopes.yaml
envelopes:
  - category: "Dining & Restaurants"
    monthly_limit_cents: 40000  # $400/month
    rollover: true
    alert_threshold: 0.8  # Alert at 80% spent

  - category: "Software & Subscriptions"
    monthly_limit_cents: 15000  # $150/month
    rollover: false
    alert_threshold: 0.9

  - category: "Travel & Transportation"
    monthly_limit_cents: 30000  # $300/month
    rollover: true
    alert_threshold: 1.0  # Alert only when exceeded
```

### Real-Time Budget Enforcement
Before approving a transaction:
```
🟡 Budget Alert: Software & Subscriptions

Current spend: $135.00 / $150.00 (90%)
Pending transaction: $29.00 (OpenAI API)
New total: $164.00 (109% of budget)

⚠️  This transaction will exceed your monthly budget by $14.00.

Actions:
- [ ] Approve anyway
- [ ] Deny (stay within budget)
- [ ] Increase budget to $200 for this month
- [ ] Defer until next billing cycle (6 days)
```

---

## 7. Transaction Audit Trail

Every financial operation (approved, denied, or expired) is logged to:
```
.nb/context/ledger/context_ledger.yaml
```

### Audit Entry Format
```yaml
- entry_id: "ledger_purchase_fa_a3f9c8d2e1b4"
  timestamp: "2024-10-04T14:35:42Z"
  operation: "purchase_approved"
  agent_id: "agent_finance_tracker"
  resource: "purchase:stripe_github_copilot"
  approval:
    user_id: "lakhwinder"
    approved_at: "2024-10-04T14:35:40Z"
    approval_method: "cli"
    reason: "Authorized GitHub Copilot renewal"
  transaction:
    vendor: "Stripe (GitHub)"
    amount_cents: 2900
    currency: "USD"
    category: "Software/SaaS"
    receipt_hash: "blake3:7a8b9c0d..."
  previous_hash: "sha256:1f2e3d4c..."
  current_hash: "sha256:9a8b7c6d..."
```

### Immutability Guarantee
Financial ledger entries are cryptographically chained. Any modification invalidates the Merkle chain and triggers an alert.

---

## 8. Export & Tax Reporting

### Quarterly Export
```bash
pos purchases export --quarter Q4-2024 --format csv
pos purchases export --year 2024 --format json --tax-categories
```

### Output Format (CSV)
```csv
Date,Vendor,Category,Amount,Tax,Payment Method,Receipt URL,Notes
2024-10-04,GitHub,Software/SaaS,29.00,0.00,Visa-4242,file://receipts/blake3-abc123,Copilot Pro
2024-10-05,Whole Foods,Groceries,87.34,7.24,Debit-8901,file://receipts/blake3-def456,
```

### Tax Category Mapping
```yaml
tax_categories:
  business_expenses:
    - "Software/SaaS" (if used for work)
    - "Office Supplies"
    - "Professional Development"
  charitable_donations:
    - "Donations/Charity"
  medical_expenses:
    - "Healthcare/Medical"
```

---

## 9. Refund & Dispute Tracking

### Dispute Workflow
When a transaction is disputed:
```bash
pos purchases dispute purchase_fa_xyz789 --reason "Unauthorized charge" --expected-refund 45.99
```

Creates dispute record:
```yaml
dispute_id: "dispute_001"
original_purchase_id: "purchase_fa_xyz789"
disputed_at: "2024-10-04T16:00:00Z"
reason: "Unauthorized charge"
expected_refund_cents: 4599
status: "pending_bank_review"
resolution_deadline: "2024-11-03"
```

### Automatic Refund Reconciliation
When a refund transaction is detected:
- Match against open disputes by amount and vendor
- Update dispute status to "resolved"
- Log to audit trail
- Notify user if refund amount differs from expected

---

## 10. Privacy & Data Minimization

### What Is Stored
- Transaction date, vendor, amount, category
- Receipt image BLAKE3 hash (not the image itself, unless user opts in)
- Last 4 digits of payment method
- Budget allocations and spending trends

### What Is NOT Stored (Unless Encrypted in Vault)
- Full credit card numbers
- CVV codes
- Bank account numbers
- PINs or passwords

### Data Retention
- **Active Subscriptions**: Retained until 90 days after cancellation
- **One-Time Purchases**: Retained for 7 years (tax compliance)
- **Receipt Images**: Automatically purged after 3 years (configurable)

---

## 11. Emergency Financial Lockdown

In case of suspected fraud or unauthorized access:
```bash
pos vault lockdown --financial
```

Effects:
- All pending financial authorizations immediately DENIED
- Vault access to payment credentials suspended
- All agents with financial capabilities disabled
- User notified via all channels (email, SMS, dashboard alert)

Unlock:
```bash
pos vault unlock --financial --two-factor
```

---

## Compliance Checklist

### Before Any Financial Operation
- [ ] User has explicitly authorized this transaction
- [ ] Transaction does not exceed budget envelope
- [ ] Vendor is recognized or user approved new vendor
- [ ] Payment method is active and valid
- [ ] Audit trail entry prepared for commit

### After Transaction Completion
- [ ] Audit entry appended to Merkle ledger
- [ ] User notification sent (if policy requires)
- [ ] Budget envelope updated
- [ ] Receipt (if available) stored and indexed

---

**End of Document**
