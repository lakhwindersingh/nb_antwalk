use std::path::Path;
use std::sync::Arc;
use parking_lot::Mutex;
use rusqlite::{params, Connection};
use uuid::Uuid;

#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("SQLite database error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("Item not found: {0}")]
    NotFound(String),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, StorageError>;

#[derive(Clone)]
pub struct Database {
    conn: Arc<Mutex<Connection>>,
}

impl Database {
    /// Opens or creates an in-memory SQLite database for testing
    pub fn open_in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        let db = Self { conn: Arc::new(Mutex::new(conn)) };
        db.init_schema()?;
        Ok(db)
    }

    /// Opens or creates a persistent SQLite database at the specified path
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self { conn: Arc::new(Mutex::new(conn)) };
        db.configure_pragmas()?;
        db.init_schema()?;
        Ok(db)
    }

    fn configure_pragmas(&self) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute_batch(
            r#"
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA busy_timeout = 5000;
            PRAGMA foreign_keys = ON;
            "#
        )?;
        Ok(())
    }

    pub fn init_schema(&self) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute_batch(
            r#"
            -- 1. Projects & Tasks
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                root_path TEXT UNIQUE,
                repo_url TEXT,
                status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'completed', 'archived')),
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS project_tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER NOT NULL DEFAULT 2,
                status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'review', 'done', 'canceled')),
                due_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            -- 2. Files & Blob Store
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                blake3_hash TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                extracted_text TEXT,
                last_indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cas_references (
                blake3_hash TEXT PRIMARY KEY,
                ref_count INTEGER NOT NULL DEFAULT 1,
                size_bytes INTEGER NOT NULL,
                last_referenced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            -- 3. Thoughts & Knowledge Graph
            CREATE TABLE IF NOT EXISTS thoughts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content_raw TEXT NOT NULL,
                thought_type TEXT NOT NULL CHECK (thought_type IN ('fleeting', 'journal', 'atomic', 'concept')),
                tags TEXT NOT NULL DEFAULT '[]',
                actionability_score REAL DEFAULT 0.0,
                ambiguity_score REAL DEFAULT 1.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS thought_links (
                source_thought_id TEXT NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
                target_thought_id TEXT NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
                link_type TEXT NOT NULL DEFAULT 'wikilink',
                PRIMARY KEY (source_thought_id, target_thought_id)
            );

            -- Native FTS5 full-text index for lexical search
            CREATE VIRTUAL TABLE IF NOT EXISTS thoughts_fts USING fts5(
                id UNINDEXED,
                title,
                content_raw
            );

            -- 4. Activities & Habits
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL CHECK (category IN ('meeting', 'focus_work', 'exercise', 'personal', 'rest')),
                start_time TEXT NOT NULL,
                end_time TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'custom')),
                target_count INTEGER NOT NULL DEFAULT 1,
                current_streak INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS habit_logs (
                id TEXT PRIMARY KEY,
                habit_id TEXT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                value INTEGER NOT NULL DEFAULT 1
            );

            -- 5. Vault & Ephemeral Leases
            CREATE TABLE IF NOT EXISTS vault_items (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                item_type TEXT NOT NULL CHECK (item_type IN ('api_key', 'password', 'token', 'certificate')),
                encrypted_payload BLOB NOT NULL,
                nonce BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vault_leases (
                lease_id TEXT PRIMARY KEY,
                vault_item_id TEXT NOT NULL REFERENCES vault_items(id),
                agent_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0
            );

            -- 6. Financial Ledger
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                category TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending_hitl', 'approved', 'rejected', 'settled')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            "#
        )?;
        Ok(())
    }

    // Projects CRUD
    pub fn insert_project(&self, id: &str, name: &str, root_path: Option<&str>, repo_url: Option<&str>) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            "INSERT INTO projects (id, name, root_path, repo_url, status) VALUES (?1, ?2, ?3, ?4, 'active')",
            params![id, name, root_path, repo_url],
        )?;
        Ok(())
    }

    pub fn list_projects(&self) -> Result<Vec<(String, String, String)>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare("SELECT id, name, status FROM projects ORDER BY created_at DESC")?;
        let rows = stmt.query_map([], |row| {
            Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        })?;
        let mut list = Vec::new();
        for r in rows {
            list.push(r?);
        }
        Ok(list)
    }

    // Thoughts & FTS5 Search
    pub fn insert_thought(&self, id: &str, title: &str, content: &str, thought_type: &str, tags: &[String]) -> Result<()> {
        let conn = self.conn.lock();
        let tags_json = serde_json::to_string(tags)?;
        conn.execute(
            "INSERT INTO thoughts (id, title, content_raw, thought_type, tags) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![id, title, content, thought_type, tags_json],
        )?;
        conn.execute(
            "INSERT INTO thoughts_fts (id, title, content_raw) VALUES (?1, ?2, ?3)",
            params![id, title, content],
        )?;
        Ok(())
    }

    pub fn search_thoughts_fts(&self, query: &str) -> Result<Vec<(String, String, String)>> {
        let conn = self.conn.lock();
        let sanitized = format!("\"{}\"", query.replace('"', "\"\""));
        let mut stmt = conn.prepare(
            "SELECT t.id, t.title, t.content_raw 
             FROM thoughts t
             JOIN thoughts_fts f ON t.id = f.id
             WHERE thoughts_fts MATCH ?1
             ORDER BY bm25(thoughts_fts)
             LIMIT 20"
        )?;
        let rows = stmt.query_map(params![sanitized], |row| {
            Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        })?;
        let mut results = Vec::new();
        for r in rows {
            results.push(r?);
        }
        Ok(results)
    }

    // Habits CRUD
    pub fn insert_habit(&self, id: &str, name: &str, frequency: &str, target_count: i32) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            "INSERT INTO habits (id, name, frequency, target_count, current_streak) VALUES (?1, ?2, ?3, ?4, 0)",
            params![id, name, frequency, target_count],
        )?;
        Ok(())
    }

    pub fn log_habit_completion(&self, habit_id: &str) -> Result<i32> {
        let conn = self.conn.lock();
        let log_id = Uuid::new_v4().to_string();
        conn.execute(
            "INSERT INTO habit_logs (id, habit_id, value) VALUES (?1, ?2, 1)",
            params![log_id, habit_id],
        )?;
        conn.execute(
            "UPDATE habits SET current_streak = current_streak + 1 WHERE id = ?1",
            params![habit_id],
        )?;
        let mut stmt = conn.prepare("SELECT current_streak FROM habits WHERE id = ?1")?;
        let streak: i32 = stmt.query_row(params![habit_id], |row| row.get(0))?;
        Ok(streak)
    }

    // Transactions & HITL
    pub fn insert_transaction(&self, id: &str, description: &str, amount: f64, category: &str) -> Result<String> {
        let conn = self.conn.lock();
        // Invariant 2: Transactions > $0.00 require human authorization
        let initial_status = if amount > 0.0 { "pending_hitl" } else { "approved" };
        conn.execute(
            "INSERT INTO transactions (id, description, amount, category, status) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![id, description, amount, category, initial_status],
        )?;
        Ok(initial_status.to_string())
    }

    pub fn approve_transaction(&self, id: &str) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            "UPDATE transactions SET status = 'approved' WHERE id = ?1",
            params![id],
        )?;
        Ok(())
    }
}
