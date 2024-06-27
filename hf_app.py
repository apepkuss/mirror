import requests
import streamlit as st
from huggingface_hub import HfApi

# Initialize session state variables if they don't exist
if "list_pressed" not in st.session_state:
    st.session_state["list_pressed"] = False
if "options" not in st.session_state:
    st.session_state["options"] = None


# Streamlit UI
st.title("Hugging Face Repository .gguf Files Lister")

repo_id = st.text_input(
    "Huggingface Repo ID (chat model)",
    value="second-state/Qwen2-0.5B-Instruct-GGUF",
    placeholder="Example: meta-llama/Meta-Llama-3-8B-Instruct",
)

if st.button("List model files (*.gguf)"):
    st.session_state["list_pressed"] = True
    try:
        # Initialize HfApi
        api = HfApi()

        # List all files in the repo
        repo_files = api.list_repo_files(repo_id=repo_id)

        # Filter .gguf files
        gguf_files = [file for file in repo_files if file.endswith(".gguf")]

        st.session_state["options"] = gguf_files

    except Exception as e:
        st.error(f"Failed to list files: {str(e)}")

# Check if the button has been pressed or options are already fetched
if st.session_state["list_pressed"] and st.session_state["options"]:
    # Select a .gguf file to download
    selected_file = st.selectbox(
        "Select a .gguf file to download",
        options=st.session_state["options"],
    )

    # Display the "Download Selected File" button
    if selected_file:
        if st.button("Download Selected File"):
            print(f"Downloading {selected_file}...")

            # Construct the URL for the selected file
            file_url = f"https://huggingface.co/{repo_id}/resolve/main/{selected_file}"

            # Initialize a progress bar in Streamlit
            progress_bar = st.progress(0, text="Downloading...")

            # Use requests to download the file with progress updates
            response = requests.get(file_url, stream=True)
            total_length = response.headers.get("content-length")

            if total_length is None:  # No content length header
                st.write("Downloading file...")
                with open(selected_file, "wb") as f:
                    f.write(response.content)
            else:
                total_length = int(total_length)
                downloaded = 0

                with open(selected_file, "wb") as f:
                    for data in response.iter_content(chunk_size=4096):
                        downloaded += len(data)
                        f.write(data)
                        progress_percentage = int(100 * downloaded / total_length)
                        progress_bar.progress(
                            progress_percentage, text="Downloading..."
                        )

                progress_bar.empty()  # Optionally clear/hide the progress bar after download

            st.write(f"Downloaded '{selected_file}'")
