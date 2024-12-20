import asyncio
import re

import duckdb
import pandas as pd
import spacy
from unidecode import unidecode

from pipeline import PipelineElement

"""
IMPORTANT:
Make sure you install the spaCy model with:
python -m spacy download en_core_web_sm
"""

# Load the spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "parser", "senter"])


# Define regular expressions for preprocessing
def remove_html(text: str) -> str:
    html_tag = re.compile(r"<.*?>")
    text = html_tag.sub(r"", text)
    return text


def remove_emails(text: str) -> str:
    email_clean = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    text = email_clean.sub(r"", text)
    return text


def remove_prices(text: str) -> str:
    price_pattern = re.compile(
        r"""
        (?:(?:\$|€|£|¥)(?:\s?))                     # Currency symbols at the start
        \d{1,3}(?:,\d{3})*(?:\.\d{1,2})?            # Numbers with optional thousands separators and decimal points
        |
        \d{1,3}(?:,\d{3})*(?:\.\d{1,2})?            # Numbers with optional thousands separators and decimal points
        (?:\s?(?:\$|€|£|¥|USD|EUR|GBP|JPY))         # Currency symbols or codes at the end
    """,
        re.VERBOSE | re.IGNORECASE,
    )

    text = price_pattern.sub("", text)
    return text


def remove_degrees(text: str) -> str:
    degree_clean = re.compile(r"\d+\s?°C|\d+\s?°F|\d+\s?°K")
    text = degree_clean.sub(r"", text)
    return text


def remove_percentages(text: str) -> str:
    percentage_clean = re.compile(r"\d+%")
    text = percentage_clean.sub(r"", text)
    return text


def remove_phone_number(text: str) -> str:
    # This pattern matches various phone number formats
    # Thanks to https://stackoverflow.com/a/56450924
    phone_pattern = re.compile(
        r"""
        ((\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}
    """,
        re.VERBOSE,
    )

    # Replace matched phone numbers with an empty string
    text = phone_pattern.sub("", text)
    return text


def remove_dates(text: str) -> str:
    # This pattern matches various date formats
    # Thanks to https://stackoverflow.com/a/8768241
    date_pattern = re.compile(
        r"""
        ^(?:(?:(?:0?[13578]|1[02])(\/|-|\.)31)\1|(?:(?:0?[1,3-9]|1[0-2])(\/|-|\.)(?:29|30)\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:0?2(\/|-|\.)29\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:(?:0?[1-9])|(?:1[0-2]))(\/|-|\.)(?:0?[1-9]|1\d|2[0-8])\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$
    """,
        re.VERBOSE,
    )

    # Replace matched phone numbers with an empty string
    text = date_pattern.sub("", text)
    return text


def remove_times(text: str) -> str:
    # This pattern matches various time formats
    time_pattern = re.compile(
        r"""
        \b                                  # Word boundary
        (?:
            (?:1[0-2]|0?[1-9])              # Hours: 1-12 with optional leading zero
            :                               # Colon separator
            (?:[0-5][0-9])                  # Minutes: 00-59
            (?:
                :(?:[0-5][0-9])             # Optional seconds: 00-59
                (?:\.[0-9]{1,3})?           # Optional milliseconds
            )?
            \s*(?:AM|PM|am|pm|A\.M\.|P\.M\.)? # Optional AM/PM indicator
        )
        |
            (?:(?:2[0-3]|[01]?[0-9])        # Hours: 00-23
            :                               # Colon separator
            (?:[0-5][0-9])                  # Minutes: 00-59
            (?::(?:[0-5][0-9])              # Optional seconds: 00-59
                (?:\.[0-9]{1,3})?           # Optional milliseconds
            )?
        )
        \b                                  # Word boundary
    """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Replace matched times with an empty string
    text = time_pattern.sub("", text)
    return text


def remove_url(text: str) -> str:
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r"", text)
    return text


# Removes Emojis
def remove_emoji(text: str) -> str:
    emoji_clean = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_clean.sub(r"", text)
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r"", text)
    return text


def remove_unicode(text: str) -> str:
    return unidecode(text, replace_str="")


def remove_special_characters(text: str) -> str:
    special_characters = re.compile(r"[^\w\s]")
    text = special_characters.sub(r" ", text)
    return text


def remove_single_character_tokens(text: str) -> str:
    single_characters = re.compile(r"\b\w\b")
    text = single_characters.sub(r"", text)
    return text


def lower(tokens: list[str]) -> list[str]:
    return [word.lower() for word in tokens]


def preprocess_text(text: str) -> str:
    """Apply all preprocessing steps using regular expressions."""
    text = remove_unicode(text)
    text = remove_url(text)
    text = remove_html(text)
    text = remove_emails(text)
    text = remove_degrees(text)
    text = remove_times(text)
    text = remove_phone_number(text)
    text = remove_dates(text)
    text = remove_emoji(text)
    text = remove_prices(text)
    text = remove_percentages(text)
    text = remove_special_characters(text)
    text = remove_single_character_tokens(text)
    return text


def process_text(text: str) -> list[str] | list[tuple]:
    """Process text using spaCy and custom logic."""

    # Preprocess the text
    text = preprocess_text(text)

    # Process with spaCy
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        # Use the lemma for nouns and proper nouns

        token = token.lemma_ if token.pos_ in ["NOUN", "PROPN"] else token.text
        tokens.append(token)

    # Lowercase the tokens
    tokens = lower(tokens)

    return tokens


class Tokenizer(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Tokenizer")
        self.cursor = dbcon.cursor()

    def __del__(self):
        self.cursor.close()

    async def process(self, data, doc_id, link):
        """
        Tokenizes the input data.
        """
        print(f"Tokenizing {link}...")
        if data is None:
            print(f"Failed to tokenize {link} because the data was empty.")
            return

        soup = data

        # Get the text from the main content
        main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("section")
                or soup.find("body")
        )

        if main_content is None:
            print(f"Warning: No main content found for {link}. Using entire body.")
            main_content = soup

        # List of tags you want to extract text from
        tags_to_extract = [
            "title",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "span",
            "div",
            "li",
            "td",
            "th",
            "a",
            "b",
            "strong",
            "i",
            "em",
            "mark",
            "small",
            "del",
            "ins",
            "sub",
            "sup",
            "q",
            "blockquote",
            "code",
            "pre",
        ]

        extracted_text = []

        try:
            for tag in main_content.find_all(tags_to_extract):
                cleaned_text = clean_text(tag.get_text(strip=True))
                if cleaned_text:
                    extracted_text.append(cleaned_text)
        except AttributeError:
            print(f"Error: Unable to parse content for {link}")
            return

        # Process meta-description and title
        description = soup.find("meta", attrs={"name": "description"})
        description_content = clean_text(
            description.get("content") if description else ""
        )
        title = soup.find("title")
        title_content = clean_text(title.string if title else "")

        # Process image alt texts
        img_tags = soup.find_all("img")
        alt_texts = [
            clean_text(img.get("alt", "")) for img in img_tags if img.get("alt")
        ]

        # Combine all text
        all_text: list[str] = (
                extracted_text + [description_content, title_content] + alt_texts
        )
        text = " ".join(all_text).strip()
        if len(text) > 200_000:
            print(f"Text for {link} is too long ({len(text)} characters). Skipping.")
            return

        # Tokenize the text
        tokenized_text: list[str] = process_text(text=text)
        if len(tokenized_text) > 6_000:
            print(f"Too many tokens ({len(tokenized_text)}) for {link}. Skipping.")
            return

        print(f"Tokenized {link}, {len(tokenized_text)} tokens found ({self.task_queue.qsize()} tasks left)")

        try:
            tokens = pd.DataFrame({"token": tokenized_text, "doc_id": doc_id})

            # Start a transaction
            self.cursor.execute("BEGIN TRANSACTION")

            print(f"Inserting {len(tokenized_text)} tokens into the database")

            # Insert new words
            self.cursor.execute("""
                INSERT INTO words(word)
                SELECT DISTINCT token
                FROM tokens
                WHERE token NOT IN (SELECT word FROM words)
            """)

            print(f"Computing TFs for {link} ...")

            # Insert term frequencies
            self.cursor.execute("""
                INSERT INTO TFs(word, doc, tf)
                SELECT w.id, t.doc_id, COUNT(*)
                FROM   tokens AS t, words AS w
                WHERE  t.token = w.word
                GROUP BY w.id, t.doc_id, t.token
            """)

            # Commit the transaction
            self.cursor.execute("COMMIT")

            print(f"Finished processing {link}")
        except Exception as e:
            # Rollback in case of error
            self.cursor.execute("ROLLBACK")
            print(f"Error processing {link}: {str(e)}")


def clean_text(text):
    """
    Clean the input text by removing excess whitespace.
    """
    # Remove excess whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Test tokenization

test_sentences = [
    "Mr. Smith's car is blue-green.",
    # URLs, emails, prices, and code snippets
    "The URL is https://www.example.com/path?param=value#fragment",
    "She said, 'I can't believe it!'",
    "Send an e-mail to john.doe@example.com",
    "The price is $19.99 (20% off)",
    "I love the movie 'Star Wars: Episode IV - A New Hope'",
    "Python 3.9.5 was released on 05/03/2021",
    "Call me at +1 (555) 123-4567",
    "The equation is E=mc^2",
    "Use the #hashtag and @mention",
    "I'm running... but I'm tired",
    "It's 72°F outside",
    "He said: Don't do that!",
    "The file name is 'document_v1.2.txt'",
    "1,000,000 people can't be wrong",
    "The code is: <html><body>Hello</body></html>",
    "Let's meet at 9:30 AM",
    "The password is: P@ssw0rd!",
    "I'll have a ham & cheese sandwich",
    "The result was 42% (not 50%)",
    # Dates and times
    "The time is 12:34 PM",
    "The time is 12:34:56 PM",
    "The date is 2021-05-03",
    "The time is 12:34:56.789",
    "The time is 12:34:56.789 PM",
    "The time is 23:59",
    "The time is 23:59:59",
    "The time is 23:59:59.999",
    "The time is 23:59:59.999 PM",
    # Named entities
    "I live in New York City",
    "I work at Google",
    "I visited the Statue of Liberty",
    "I went to the United States of America",
    "I flew with Lufthansa",
    "I bought an iPhone",
    "I use Microsoft Windows",
    "Apple Inc. is a great company",
    "I ate at McDonald's",
    "I study at the Max Planck Institute",
    "Tübingen is a nice city",
    "Everyday I eat at Salam Burger in Tübingen and I love it",
    # Misc
    "I ❤️ Python",
    "I'm 6'2\" tall",
    "I'm 6'2\" tall and I weigh 180 lbs.",
    "I'm 6'2\" tall and I weigh 180 lbs. I'm 25 years old.",
    "Das ist „wert ist der Stein“",
    "I'm running... but I'm tired",
    "​​​​​​​+49",
    "()(){}{)Hi{}}",
]

if __name__ == "__main__":
    for sentence in test_sentences:
        print(f"Original: {sentence}")
        print(f"Tokenized: {process_text(sentence)}")
        print()

    # dummy_query = "and the finally the what the I am the only tiger in the house"
    # print(process_and_expand_query(dummy_query))
