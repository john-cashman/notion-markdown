import streamlit as st
import zipfile
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote
import tempfile
import base64

# Helper function to sanitize filenames
def sanitize_filename(name):
    path_parts = Path(name).parts
    cleaned_parts = []
    for part in path_parts:
        cleaned = re.sub(r'\s*[a-f0-9]{32}\b', '', part)
        cleaned = re.sub(r'\s*[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\b', '', cleaned)
        cleaned = re.sub(r'\s*[0-9a-f]{16}\b', '', cleaned)
        cleaned = re.sub(r'\s+\([0-9a-f]{3,}\)', '', cleaned)
        cleaned = cleaned.replace('…', '...').replace(' ', '-')
        cleaned = re.sub(r'[<>:"/\\|?*]', '-', cleaned)
        cleaned = re.sub(r'-+', '-', cleaned).strip('-')
        cleaned = ''.join(c for c in cleaned if ord(c) < 128)
        if not cleaned or cleaned == '.':
            cleaned = 'untitled'
        cleaned_parts.append(cleaned)
    return str(Path(*cleaned_parts))

# Check if file type is supported
def is_supported_file(filename):
    supported_extensions = {'.md', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp4', '.mov', '.csv'}
    return Path(filename).suffix.lower() in supported_extensions

# Build a file map of cleaned paths
def build_link_database(source_dir):
    source_dir = Path(source_dir).resolve()
    file_map = {}
    skipped_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if is_supported_file(file):
                try:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(source_dir)
                    clean_path = sanitize_filename(str(rel_path))
                    file_map[str(rel_path.as_posix())] = clean_path
                except Exception as e:
                    skipped_files.append((file, str(e)))
    return file_map, skipped_files

# Copy and rename files based on the file map
def copy_and_rename_files(source_dir, target_dir, file_map):
    source_dir = Path(source_dir).resolve()
    target_dir = Path(target_dir).resolve()
    
    for old_rel_path_str, new_rel_path_str in file_map.items():
        old_rel_path = Path(old_rel_path_str)
        new_rel_path = Path(new_rel_path_str)
        source_path = source_dir / old_rel_path
        target_path = target_dir / new_rel_path
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if old_rel_path.suffix.lower() == '.md':
            # Process markdown content if necessary
            with source_path.open('r', encoding='utf-8') as f:
                content = f.read()
            with target_path.open('w', encoding='utf-8') as f:
                f.write(content)  # Here you'd call `update_markdown_links` if needed
        else:
            # Copy other files directly
            shutil.copy2(source_path, target_path)

# Streamlit interface
st.title("Notion to GitBook Markdown Converter")

# Upload ZIP file
uploaded_file = st.file_uploader("Upload your Notion export ZIP file", type="zip")
if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Extract ZIP
        zip_path = Path(tmpdirname) / "notion_export"
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(zip_path)
        
        # Prepare target directory
        target_dir = Path(tmpdirname) / "markdown_export"
        
        # Build file map and process files
        file_map, skipped_files = build_link_database(zip_path)
        copy_and_rename_files(zip_path, target_dir, file_map)
        
        # Zip the processed files for download
        output_zip_path = Path(tmpdirname) / "processed_markdown.zip"
        with zipfile.ZipFile(output_zip_path, 'w') as zipf:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(target_dir))
        
        # Provide download link
        with open(output_zip_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            href = f'<a href="data:application/zip;base64,{b64}" download="processed_markdown.zip">Download Processed Markdown ZIP</a>'
            st.markdown(href, unsafe_allow_html=True)

        # Display skipped files if any
        if skipped_files:
            st.write("Skipped Files:")
            for file, error in skipped_files:
                st.write(f"{file}: {error}")
