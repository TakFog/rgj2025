import json
from notion2pandas import Notion2PandasClient
import time
import requests
from notion2pandas import Notion2PandasClient
import os

def copy_page_content_full(notion: Notion2PandasClient, source_page_id: str, target_page_id: str):
    """
    Copies all blocks from one Notion page to another.
    Notion-hosted files/images are downloaded and re-uploaded.
    External files/images are copied as links.
    """

    def _wait_for_upload_completion(file_upload_id: str, poll_interval=5, max_wait_time=300):
        """Wait for a single_part file upload to complete."""
        start_time = time.monotonic()
        while time.monotonic() - start_time < max_wait_time:
            status_resp = notion.file_uploads.retrieve(file_upload_id=file_upload_id)
            status = status_resp.get("status")
            if status == "uploaded":
                return
            elif status == "failed":
                raise Exception(f"Upload failed: {status_resp}")
            time.sleep(poll_interval)
        raise TimeoutError("File upload timed out")

    def clean_media_block(block_type: str, block_content: dict):
        """Prepare a media block (image, file, pdf, video, audio) for appending."""
        file_info = block_content.get("file")
        external_info = block_content.get("external")
        filename = ""
        if block_type == "image":
            filename = "image.jpg"
        if block_type == "audio":
            filename = "audio.mp3"
        if block_type == "video":
            filename = "video.mp4"

        if file_info and "url" in file_info:
            # Notion-hosted → scarica e ricarica
            response = requests.get(file_info["url"])
            response.raise_for_status()
            content = response.content
            upload_resp = notion.file_uploads.create(
                mode="single_part",
                filename=filename,
            )
            file_upload_id = upload_resp["id"]

            with open(filename, "wb") as f:
                f.write(response.content)

            with open(filename, "rb") as f:
                notion.file_uploads.send(file_upload_id=file_upload_id, file=f)

            _wait_for_upload_completion(file_upload_id)
            os.remove(filename)
            return {
                "object": "block",
                "type": block_type,
                block_type: {"type": "file_upload", "file_upload": {"id": file_upload_id}}
            }

        elif external_info and "url" in external_info:
            # External → copia direttamente
            return {
                "object": "block",
                "type": block_type,
                "image": {"type": "external", "external": {"url": external_info["url"]}}
            }

        return None

    def copy_block_recursive(src_block_id: str, dst_parent_id: str):
        """Recursively copy all child blocks."""
        children = notion.blocks.children.list(block_id=src_block_id)["results"]
        supported_block_types = ["image", "video", "audio"]
        for child in children:
            block_type = child["type"]
            block_content = child.get(block_type, {})

            if block_type in supported_block_types:
                media_block = clean_media_block(block_type, block_content)
                if not media_block:
                    continue
                new_block = media_block
            else:
                # Copy normal block content
                new_block = {"object": "block", "type": block_type}
                new_block[block_type] = {}
                for k, v in block_content.items():
                    if k not in (
                        "id",
                        "created_time",
                        "last_edited_time",
                        "created_by",
                        "last_edited_by",
                        "has_children",
                    ):
                        new_block[block_type][k] = v

            # Append the block
            created = notion.blocks.children.append(
                block_id=dst_parent_id,
                children=[new_block]
            )
            new_block_id = created["results"][0]["id"]

            # Recursively copy children if present
            if child.get("has_children"):
                copy_block_recursive(child["id"], new_block_id)

    # Start recursive copy
    copy_block_recursive(source_page_id, target_page_id)

