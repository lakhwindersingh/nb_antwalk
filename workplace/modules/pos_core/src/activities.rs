use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Activity {
    pub id: String,
    pub title: String,
    pub category: String,
    pub start_time: String,
    pub end_time: Option<String>,
    pub source: String,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Habit {
    pub id: String,
    pub name: String,
    pub frequency: String,
    pub target_count: i32,
    pub current_streak: i32,
}

pub struct StreakCalculator;

impl StreakCalculator {
    pub fn calculate_next_streak(current_streak: i32, is_consecutive: bool) -> i32 {
        if is_consecutive {
            current_streak + 1
        } else {
            1
        }
    }
}
