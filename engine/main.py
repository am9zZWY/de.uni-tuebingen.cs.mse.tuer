"""
Pipeline for Crawling, Tokenizing, and Indexing
"""
from concurrent.futures import ThreadPoolExecutor

from crawl import Crawler
from custom_db import index_pages, access_index, save_pages
from custom_tokenizer import Tokenizer
import asyncio

MAX_THREADS = 10

if __name__ == "__main__":
    try:
        # Initialize the pipeline
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            crawler = Crawler()
            crawler.max_size = 1000
            crawler.add_executor(executor)

            tokenizer = Tokenizer()
            tokenizer.add_executor(executor)

            # Add the pipeline elements
            crawler.add_next(tokenizer)

            # Start the pipeline
            asyncio.run(crawler.process())
    except (KeyboardInterrupt, SystemExit):
        print("Exiting...")
        crawler.save_state()
        print("State saved")

    index_pages()
    index_df = access_index()
    index_df.to_csv("inverted_index.csv")
    save_pages()