# TueR – Tübingen Retrieval (Engine)

This is the engine for the **TüR** (**Tü**bingen **R**etrieval) project, built with Python, Flask, DuckDB, and lots of
motivation.

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Server](#server)
5. [Known Issues](#known-issues)

## Requirements

- Python 3
- pip
- virtualenv

## Installation

1. **Install Python 3:**

- Download and install the latest version of Python 3 from the official website.

2. **Install virtualenv:**
   ```shell
   pip install virtualenv
   ```

3. **Create and activate a virtual environment:**
   ```shell
   virtualenv --python=3.11 .venv
   source .venv/bin/activate
   ```

4. **Install requirements:**
   ```shell
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Usage

### Crawl pages:

```shell
python main.py --online
```

---

**Important:**

- The online pipeline will run until you stop it manually, or it reaches the maximum number of sites.
- You can adapt the configuration in the `main.py`. The crawler has alot of options to configure.
- The online pipeline will start a lot of threads, so it can be quite resource-intensive. You can limit the number of
- You need a lot of RAM (~20 GB of RAM) for the offline pipeline.
  threads in the `main.py` file.
- Have fun crawling the web!

---

### Start the server:

```shell
python server.py
```

### Access the application:

Open your browser and navigate to [http://localhost:8000/](http://localhost:8000/)

## Server

The server is built with Flask and runs on port 8000 by default. To start the server, use the following command:

```shell
python server.py
```

You can see a list of all available routes by navigating to <http://localhost:8000/site-map>.

---

**Important:**

- The server will only work if you have crawled some pages before.
- For the summarization you will need a strong CPU and a lot of RAM, as the summarization is done on the fly and can be
  quite resource-intensive.

---

## Known Issues

The pipeline will not stop by itself, even if reached the maximum sites.
You will have to stop it manually by pressing `Ctrl + C` in the terminal.
But it will be able to resume from where it left off when you restart it.

When the offline pipeline runs, it will try to finish completely before stopping.
If you force stop it, the pipeline will not save the state because it's saved in `crawlies.db.wal`.
