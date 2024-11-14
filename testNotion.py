import streamlit as st
import re
from pathlib import Path
import tempfile
import zipfile
import base64

# Helper function to convert MDX to GitBook-compatible Markdown
def convert_mdx_to_gitbook(markdown_content):
    """
    Convert MDX content to GitBook-compatible Markdown.
    This involves removing unsupported JSX elements and formatting adjustments.
    """
    # Remove JSX components and HTML-like tags (simple regex, can be expanded)
    cleaned_content = re.sub(r'<[^>]+>', '', markdown_content)  # Removes HTML/JSX tags
    cleaned_content = re.sub(r'{[^}]+}', '', cleaned_content)  # Removes JSX expressions

    # Additional replacements for GitBook compatibility
    # Example: remove import/export statements, if present
    cleaned_content = re.sub(r'^(import|export).*\n', '', cleaned_content, flags=re.MULTILINE)

    return cleaned_content

# Streamlit interface
st.title("MDX to GitBook Markdown Converter")

# Upload .mdx files
uploaded_files = st.file_uploader("Upload your MDX files", type="mdx", accept_multiple_files=True)
if uploaded_files:
    # Create a temporary directory to store the converted files
    with tempfile.TemporaryDirectory() as tmpdirname:
        converted_files = []
        
        for uploaded_file in uploaded_files:
            # Read the content of the uploaded .mdx file
            mdx_content = uploaded_file.read().decode("utf-8")
            
            # Convert the MDX content to GitBook-compatible Markdown
            gitbook_markdown = convert_mdx_to_gitbook(mdx_content)
            
            # Create the output filename by replacing the .mdx extension with .md
            output_filename = uploaded_file.name.replace(".mdx", ".md")
            converted_file_path = Path(tmpdirname) / output_filename
            
            # Write the converted content to the new .md file
            with open(converted_file_path, "w", encoding="utf-8") as f:
                f.write(gitbook_markdown)
            
            converted_files.append(converted_file_path)
        
        # Zip all converted files
        output_zip_path = Path(tmpdirname) / "converted_markdown.zip"
        with zipfile.ZipFile(output_zip_path, "w") as zipf:
            for file_path in converted_files:
                zipf.write(file_path, file_path.name)
        
        # Provide download link for the ZIP file
        with open(output_zip_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            href = f'<a href="data:application/zip;base64,{b64}" download="converted_markdown.zip">Download Converted Markdown Files</a>'
            st.markdown(href, unsafe_allow_html=True)

        st.success(f"Converted {len(converted_files)} files to GitBook-compatible Markdown!")
