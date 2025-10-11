import json
import os
from notion2pandas import Notion2PandasClient
from notion_copy_page import copy_page_content_full, clear_page_content
import ast

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
    oneToOneRelations = ['Content pages DB']

    def relation_read(self, notion_property: dict, column_name: str):
        relations = notion_property.get('relation', [])
        relation_ids = [relation.get('id') for relation in relations]
        if column_name in self.oneToOneRelations:
            if len(relation_ids) > 0:
                return relation_ids[0]
            return ''
        return relation_ids

    def relation_write(self, row_value: str, column_name: str):
        if row_value == '':
            return {"relation": []}
        if column_name in self.oneToOneRelations:
            return {"relation": [{"id": row_value}]}
        notion_relations = ast.literal_eval(row_value)
        relation_ids = [{"id": notion_relation} for
                        notion_relation in notion_relations]
        return {"relation": relation_ids}

    def __init__(self):
        # Load credentials and database info
        print('init Notion')
        with open('notion_data.json', 'r') as notion_file:
            notion_data = json.load(notion_file)

        token = os.getenv("NOTION_TOKEN")
        database_id = notion_data.get('rgj25').get('id_database_pages_db')

        if not token or not database_id:
            raise ValueError("Missing Notion token or database_id in JSON file")

        # Initialize Notion2Pandas client
        self.n2p = Notion2PandasClient(auth=token)
        self.n2p.set_lambdas('relation', self.relation_read, self.relation_write)
        self.database_id = database_id
        self.df = self.load_dataframe()  # will hold the DataFrame
        print('Phases count are:{0}'.format(len(self.df)))
        for indice, riga in self.df.iterrows():
            clear_page_content(self.n2p, riga['PageID'])

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

    def active_phase(self, phase_name: str) -> (bool, str):
        filtered_df = self.df[self.df['Name'] == phase_name]
        if filtered_df.empty:
            return False, 'No phase found'
        print(len(filtered_df))
        for indice, riga in filtered_df.iterrows():
            copy_page_content_full(self.n2p, riga['Content pages DB'], riga['PageID'])
        return True, None


def main():
    notionPages = NotionPagesDB()
    ok, err = notionPages.active_phase('TEST-PHASE')
    if err is not None:
        print(err)


if __name__ == "__main__":
    main()