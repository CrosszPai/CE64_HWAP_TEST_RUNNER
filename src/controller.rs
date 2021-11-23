use serde::{Deserialize, Serialize};
use std::process::Command;

use crate::utils;

#[derive(Serialize, Deserialize, Debug)]
pub struct AppMessage {
    pub id: String,
    pub event: String,
    pub payload: String,
}

pub fn command_processing(
    message: AppMessage,
    pin: std::sync::Arc<std::sync::Mutex<rppal::gpio::OutputPin>>,
) {
    if message.event == "connected" && message.payload == "success" {
        pin.lock().unwrap().set_high();
    }
    if message.event == "income_work" {
        println!("{}", message.payload);
        let clonning_process = Command::new("git")
            .arg("clone")
            .arg(message.payload)
            .arg("temp")
            .output()
            .unwrap();
        if clonning_process.status.success() {
            println!("cloning {}", clonning_process.status.success());
        } else {
            println!(
                "cloning {}",
                String::from_utf8_lossy(&clonning_process.stderr)
            );
        }
        let make_process = Command::new("make").arg("-C").arg("temp").output().unwrap();
        if make_process.status.success() {
            println!("compiling {}", make_process.status.success());
        } else {
            println!(
                "compling error {}",
                String::from_utf8_lossy(&make_process.stderr)
            );
        }

        let mut binary_file_name = String::default();
        if let Ok(lines) = utils::read_project_config("./temp") {
            // Consumes the iterator, returns an (Optional) String
            for line in lines {
                if let Ok(data) = line {
                    if data.contains("ProjectManager.ProjectName") {
                        let project_name = data.split("=").map(|s| s.to_string());
                        binary_file_name = project_name.clone().last().unwrap();
                        break;
                    }
                }
            }
        }
        println!("{}", binary_file_name.clone());
        let upload_process = Command::new("openocd")
            .arg("-f")
            .arg("./openocd.cfg")
            .arg("-c")
            .arg(format!(
                "program ./temp/build/{project}.elf verify reset exit",
                project = binary_file_name
            ))
            .output()
            .unwrap();

        if upload_process.status.success() {
            println!("flash {}", upload_process.status.success());
            Command::new("rm").arg("-rf").arg("temp").output().unwrap();
        } else {
            println!(
                "flash error {}",
                String::from_utf8_lossy(&upload_process.stderr)
            );
        }
    }
}
