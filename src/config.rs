use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Config {
    pub endpoint: String,
    pub device_id: String,
}
