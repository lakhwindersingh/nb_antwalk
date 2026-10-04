use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TransactionStatus {
    PendingHitl,
    Approved,
    Rejected,
    Settled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: String,
    pub description: String,
    pub amount: f64,
    pub currency: String,
    pub category: String,
    pub status: TransactionStatus,
}

/// Invariant 2: Human-in-the-Loop Financial Gate
/// Autonomous agents are STRICTLY FORBIDDEN from committing monetary transactions > $0.00
/// without explicit interactive human authorization.
pub struct HitlFinancialGate;

impl HitlFinancialGate {
    pub fn requires_human_authorization(amount: f64) -> bool {
        amount > 0.0
    }

    pub fn evaluate_transaction_state(amount: f64) -> TransactionStatus {
        if Self::requires_human_authorization(amount) {
            TransactionStatus::PendingHitl
        } else {
            TransactionStatus::Approved
        }
    }
}
