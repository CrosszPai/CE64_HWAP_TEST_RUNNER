use serde::{Deserialize, Serialize};
use rppal::gpio::{Gpio, Level, Trigger};

use chrono::prelude::*;
use std::rc::Rc;

use std::fs::File;
use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Error, Write};
use tokio::time;


#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct TestFile {
    pub title: String,
    pub cases: Vec<TestCase>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct TestCase {
    pub describe: String,
    pub input: TestInput,
    pub output: TestOutput,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct TestInput {
    pub pin: u8,
    pub input_type: String,
    pub timming: u64,
    pub loops: usize,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct TestOutput {
    pub pin: u8,
    pub check: String,
    pub value: String,
    pub error: f32,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct TestedRusult {
    pub input_val: u8,
    pub output_val: u8,
    pub input_time: i64,
    pub output_time: i64,
}


pub async fn process_test(){
    let f = std::fs::File::open("test.yaml").unwrap();
    let d: TestFile = serde_yaml::from_reader(f).unwrap();

    println!("{}", d.title);
    for i in d.cases {
        println!("{}", i.describe);
        let gpio = Gpio::new().unwrap();
        let mut check_pin = gpio.get(i.output.pin).unwrap().into_input_pullup();
        let mut sim_pin = gpio.get(i.input.pin).unwrap().into_output();
        let mut out_time = 0;
        if i.input.input_type == "repeat" {
            check_pin
                .set_async_interrupt(Trigger::RisingEdge, move |level: Level| {
                    let mut output: File = OpenOptions::new()
                    .write(true)
                    .create(true)
                    .append(true)
                    .open("result.txt")
                    .unwrap();
                    let val = if level.to_string() == "High" { 1 } else { 0 };
                    output
                        .write(
                            format!("output {} {} \n", val, Utc::now().timestamp_millis()).as_bytes(),
                        )
                        .unwrap();
                    println!("{}", level.to_string());
                })
                .unwrap();
            for _ in 0..i.input.loops {
                sim_pin.set_high();
                let mut output: File = OpenOptions::new()
                    .write(true)
                    .create(true)
                    .append(true)
                    .open("result.txt")
                    .unwrap();
                output
                    .write(format!("input {} {} \n", 1, Utc::now().timestamp_millis()).as_bytes())
                    .unwrap();
                time::sleep(time::Duration::from_millis(i.input.timming)).await;
                sim_pin.set_low();
                time::sleep(time::Duration::from_millis(i.input.timming)).await;
            }
            check_pin.clear_async_interrupt().unwrap();
        }
    }
}
