import json
import os
from notion2pandas import Notion2PandasClient
from notion_copy_page import copy_page_content_full

def get_text(notion_blocks):
    """Extracts plain text from the first Notion block containing rich_text."""
    if not notion_blocks or 'results' not in notion_blocks:
        return ''
    for block in notion_blocks['results']:
        block_type = block.get('type')
        block_data = block.get(block_type, {})
        rich_texts = block_data.get('rich_text', [])
        if rich_texts:
            return ''.join(rt.get('plain_text', '') for rt in rich_texts)
    return ''
class NotionPagesDB:
    """Wrapper class for accessing and sorting a Notion database as a DataFrame."""

    def __init__(self):
        # Load credentials and database info
        with open('notion_data.json', 'r') as notion_file:
            notion_data = json.load(notion_file)

        token = os.getenv("NOTION_TOKEN")
        database_id = notion_data.get('rgj25').get('id_database_pages_db')

        if not token or not database_id:
            raise ValueError("Missing Notion token or database_id in JSON file")

        # Initialize Notion2Pandas client
        self.n2p = Notion2PandasClient(auth=token)
        self.database_id = database_id
        self.df = self.load_dataframe()  # will hold the DataFrame

    def load_dataframe(self, ascending: bool = True):
        """Fetches data from Notion DB, sorted by Name."""
        sort_by_name = {
            "sorts": [
                {
                    "property": "Name",
                    "direction": "ascending" if ascending else "descending"
                }
            ]
        }

        #custom_block_prop = {'inside_text': get_text}

        # Load DataFrame
        self.df = self.n2p.from_notion_DB_to_dataframe_kwargs(
            database_id=self.database_id,
            filter_params=sort_by_name,
            #columns_from_blocks=custom_block_prop
        )


        return self.df

def main():
    notionPages = NotionPagesDB()
    copy_page_content_full(notionPages.n2p, '28944e81-37da-8076-a5d8-fee4ce1b2ad6',
                           '28944e81-37da-8044-824d-d9b3d55dab07')

if __name__ == "__main__":
    main()