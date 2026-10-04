//! Personal OS Pillar Integration Dispatcher
//!
//! Links extracted email entities to Projects, Activities, Interactions, and Purchases
//! per Section 1 & Section 2.2 of `.nb/plan/extensions/email_triage/concise.md`.

use crate::error::Result;
use crate::extractor::{ExtractedContact, ExtractedEvent, ExtractedReceipt, ExtractedTask};
use pos_email::EmailStore;
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use uuid::Uuid;

/// Record of a dispatched entity link to Personal OS pillars
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DispatchedEntity {
    pub entity_type: String,
    pub entity_id: String,
    pub pillar: String,
    pub email_id: Uuid,
}

pub struct PillarDispatcher {
    store: EmailStore,
    dispatch_count: Arc<AtomicUsize>,
}

impl PillarDispatcher {
    pub fn new(store: EmailStore) -> Self {
        Self {
            store,
            dispatch_count: Arc::new(AtomicUsize::new(0)),
        }
    }

    /// Dispatch task to Projects pillar
    pub fn dispatch_task(&self, email_id: Uuid, _task: &ExtractedTask) -> Result<DispatchedEntity> {
        let task_id = format!("task_{}", Uuid::new_v4());
        self.store
            .link_extracted_entity(email_id, "task", &task_id, "projects")?;
        self.dispatch_count.fetch_add(1, Ordering::SeqCst);

        Ok(DispatchedEntity {
            entity_type: "task".to_string(),
            entity_id: task_id,
            pillar: "projects".to_string(),
            email_id,
        })
    }

    /// Dispatch calendar event to Activities pillar
    pub fn dispatch_event(&self, email_id: Uuid, _event: &ExtractedEvent) -> Result<DispatchedEntity> {
        let event_id = format!("event_{}", Uuid::new_v4());
        self.store
            .link_extracted_entity(email_id, "event", &event_id, "activities")?;
        self.dispatch_count.fetch_add(1, Ordering::SeqCst);

        Ok(DispatchedEntity {
            entity_type: "event".to_string(),
            entity_id: event_id,
            pillar: "activities".to_string(),
            email_id,
        })
    }

    /// Dispatch contact to Interactions / CRM pillar
    pub fn dispatch_contact(
        &self,
        email_id: Uuid,
        _contact: &ExtractedContact,
    ) -> Result<DispatchedEntity> {
        let contact_id = format!("contact_{}", Uuid::new_v4());
        self.store
            .link_extracted_entity(email_id, "contact", &contact_id, "interactions")?;
        self.dispatch_count.fetch_add(1, Ordering::SeqCst);

        Ok(DispatchedEntity {
            entity_type: "contact".to_string(),
            entity_id: contact_id,
            pillar: "interactions".to_string(),
            email_id,
        })
    }

    /// Dispatch receipt to Purchases pillar
    pub fn dispatch_receipt(
        &self,
        email_id: Uuid,
        _receipt: &ExtractedReceipt,
    ) -> Result<DispatchedEntity> {
        let purchase_id = format!("purchase_{}", Uuid::new_v4());
        self.store
            .link_extracted_entity(email_id, "receipt", &purchase_id, "purchases")?;
        self.dispatch_count.fetch_add(1, Ordering::SeqCst);

        Ok(DispatchedEntity {
            entity_type: "receipt".to_string(),
            entity_id: purchase_id,
            pillar: "purchases".to_string(),
            email_id,
        })
    }

    pub fn total_dispatched(&self) -> usize {
        self.dispatch_count.load(Ordering::SeqCst)
    }
}
