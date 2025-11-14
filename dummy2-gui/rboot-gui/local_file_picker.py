import asyncio
from pathlib import Path
from nicegui import ui


async def local_file_picker(directory: str, multiple: bool = False) -> list[str]:
    """Open a local file picker dialog.

    Args:
        directory: The directory to start in
        multiple: Whether to allow multiple file selection

    Returns:
        A list of selected file paths
    """
    files = []

    def handle_upload(e):
        nonlocal files
        files = e.value
        dialog.close()

    with ui.dialog() as dialog, ui.card():
        with ui.column():
            ui.upload(
                multiple=multiple,
                on_upload=handle_upload,
                auto_upload=True
            ).props(f'accept=*')
            ui.button('Cancel', on_click=dialog.close)

    await dialog
    return [f.name for f in files] if files else []