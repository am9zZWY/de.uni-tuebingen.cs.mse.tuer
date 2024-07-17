import logging
import os

import pandas as pd

from collections import defaultdict

from pandas import DataFrame

# Create a DataFrame to store HTML pages
headers = ['id', 'url', 'title', 'snippet', 'tokenized_text']
pages_df = pd.DataFrame(columns=headers).astype({
    'id': 'int',
    'url': 'str',
    'title': 'str',
    'snippet': 'str',
    'tokenized_text': 'object'
})
inverted_index = defaultdict(list)
inverted_index_df = pd.DataFrame(columns=['word', 'doc_ids'])


def upsert_page_to_index(url: str):
    """
    Add a page to the index if it doesn't exist.
    Args:
        url: URL of the page

    Returns:

    """

    global pages_df
    # Get an existing row with the same URL if it exists
    existing_row = pages_df[pages_df['url'] == url]

    if not existing_row.empty:
        page_id = existing_row['id'].values[0]
    else:
        # Create a new row
        page_id = len(pages_df) + 1
        pages_df = pd.concat(
            [pages_df, pd.DataFrame(
                [
                    {'id': page_id, 'url': url, 'title': '', 'snippet': '', 'tokenized_text': []}
                ])],
            ignore_index=True)

    return page_id


def add_tokens_to_index(url: str, tokenized_text: list[str]):
    """
    Add tokenized text to the index.
    Args:
        url:
        tokenized_text: List of tokens

    Returns:

    """
    global pages_df

    page_id = upsert_page_to_index(url)
    if not pages_df[pages_df['id'] == page_id].empty:
        pages_df.at[pages_df[pages_df['id'] == page_id].index[0], 'tokenized_text'] = tokenized_text
    else:
        print(f"Page with ID {page_id} not found")


def add_title_to_index(url: str, title: str):
    """
    Add a title to the index.
    Args:
        url:
        title:

    Returns:

    """
    global pages_df

    page_id = upsert_page_to_index(url)
    if not pages_df[pages_df['id'] == page_id].empty:
        pages_df.at[pages_df[pages_df['id'] == page_id].index[0], 'title'] = title
    else:
        print(f"Page with ID {page_id} not found")


def add_snippet_to_index(url, snippet):
    """
    Add a snippet/description to the index.
    Args:
        url:
        snippet:

    Returns:

    """
    global pages_df

    upsert_page_to_index(url)
    if not pages_df[pages_df['url'] == url].empty:
        pages_df.at[pages_df[pages_df['url'] == url].index[0], 'snippet'] = snippet
    else:
        print(f"Page with URL {url} not found")


def get_tokens() -> list[list[str]]:
    """
    Get the tokenized text from the pages DataFrame.
    Tokenized text is a matrix of tokens.
    One row per document, one column per token.

    Returns: list[list[str]]

    """
    global pages_df
    tokens = pages_df['tokenized_text'].to_list()
    return tokens


def get_overview():
    return pages_df.head()


def add_document_to_index(doc_id, words: list[str]):
    global inverted_index

    if not words:
        return

    for word in set(words):
        inverted_index[word].append(doc_id)


def index_pages():
    for index, row in pages_df.iterrows():
        page_id = row['id']
        tokenized_text = row['tokenized_text']
        add_document_to_index(page_id, tokenized_text)


def access_index():
    index_df = pd.DataFrame(list(inverted_index.items()), columns=['word', 'doc_ids'])
    return index_df


def get_page_by_id(page_id: int):
    global pages_df
    page = pages_df[pages_df['id'] == page_id]
    return page


def save_pages() -> None:
    """
    Save the pages DataFrame to a CSV file.
    Returns: None
    """

    global pages_df
    pages_df.to_csv("pages.csv", index=False, header=headers)


def get_doc_by_id(page_id: int):
    global pages_df
    page = pages_df[pages_df['id'] == page_id]
    return page


def load_inverted_index() -> pd.DataFrame:
    """
    Load the inverted index DataFrame from a CSV file.
    Returns: pd.DataFrame
    """

    global inverted_index_df

    # Check if the file exists
    if not os.path.exists(f"inverted_index.csv"):
        print("No inverted index found")
        return pd.DataFrame()

    try:
        inverted_index_df = pd.read_csv("inverted_index.csv", header=0)
    except pd.errors.EmptyDataError:
        print("No inverted index found")
        return pd.DataFrame()

    print("Loaded inverted index")
    return inverted_index_df


def load_pages() -> DataFrame | None:
    """
    Load the pages DataFrame from a CSV file.
    Returns: pd.DataFrame
    """

    global pages_df

    # Check if the file exists
    if not os.path.exists(f"pages.csv"):
        print("No pages found")
        return None

    try:
        pages_df = pd.read_csv("pages.csv", header=0)
    except pd.errors.EmptyDataError:
        print("No pages found")
        return None

    # Convert the tokenized_text column to a list of lists
    pages_df['tokenized_text'] = pages_df['tokenized_text'].apply(eval)

    print("Loaded pages")
    return None


load_pages()
