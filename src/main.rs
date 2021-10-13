mod config;

use futures_util::{future, pin_mut, SinkExt, StreamExt};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};

use rppal::gpio::Gpio;
use rppal::system::DeviceInfo;
use serde::{Deserialize, Serialize};
use std::borrow::Cow;

#[derive(Serialize, Deserialize, Debug)]
struct AppMessage {
    id: String,
    event: String,
    payload: String,
}
const GPIO_LED: u8 = 23;
#[tokio::main]
async fn main() {
    println!(
        "Blinking an LED on a {}.",
        DeviceInfo::new().unwrap().model()
    );
    let config_yaml =
        std::fs::File::open("./config.yaml").expect("this program require config file");
    println!("Reading config");
    let config_value: config::Config = serde_yaml::from_reader(config_yaml).unwrap();
    println!("{:?}, {:?}", config_value.endpoint, config_value.device_id);
    if config_value.device_id == "" || config_value.endpoint == "" {
        panic!("Plase config file")
    }
    let connect_addr = config_value.endpoint;

    let url = url::Url::parse(&connect_addr).unwrap();

    let (stdin_tx, stdin_rx) = futures_channel::mpsc::unbounded();
    tokio::spawn(read_stdin(stdin_tx));

    let (mut ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    println!("WebSocket handshake has been successfully completed");
    let connected_message = AppMessage {
        id: config_value.device_id,
        event: String::from("connected"),
        payload: "".to_string(),
    };
    let cns = serde_json::to_string(&connected_message).unwrap();
    println!("{}", cns);
    ws_stream.send(Message::Text(cns)).await.unwrap();
    let (write, read) = ws_stream.split();
    let stdin_to_ws = stdin_rx.map(Ok).forward(write);
    let ws_to_stdout = {
        read.for_each(|message| async move {
            let data = message.unwrap().into_data();
            let msg: AppMessage =
                serde_json::from_str(Cow::as_ref(&String::from_utf8_lossy(&data))).unwrap();
            println!("{:?}", msg);
            let gpio = Gpio::new().unwrap();
            let mut pin = gpio.get(GPIO_LED).unwrap().into_output();
            pin.set_low();
            tokio::io::stdout().write_all(&data).await.unwrap();
        })
    };

    pin_mut!(stdin_to_ws, ws_to_stdout);
    future::select(stdin_to_ws, ws_to_stdout).await;
}

// Our helper method which will read data from stdin and send it along the
// sender provided.
async fn read_stdin(tx: futures_channel::mpsc::UnboundedSender<Message>) {
    let mut stdin = tokio::io::stdin();
    loop {
        let mut buf = vec![0; 1024];
        let n = match stdin.read(&mut buf).await {
            Err(_) | Ok(0) => break,
            Ok(n) => n,
        };
        buf.truncate(n);
        tx.unbounded_send(Message::binary(buf)).unwrap();
    }
}
