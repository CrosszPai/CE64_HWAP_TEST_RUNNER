use std::fs::{self, File};
use std::io::{self, BufRead};
use std::path::Path;

pub fn read_project_config<P>(dir: P) -> io::Result<io::Lines<io::BufReader<File>>>
where
    P: AsRef<Path>,
{
    println!("read config");
    let paths = fs::read_dir(dir).unwrap();
    let mut project_cfg = String::default();
    for path in paths {
        project_cfg = String::from(path.unwrap().file_name().to_str().unwrap());
        if project_cfg.contains(".ioc") {
            break;
        }
    }
    println!("{}", project_cfg);
    if !project_cfg.contains(".ioc") {
        project_cfg = String::default();
    }
    println!("{}", project_cfg);
    let file = File::open(String::from("./temp/") + project_cfg.as_str())?;
    Ok(io::BufReader::new(file).lines())
}
