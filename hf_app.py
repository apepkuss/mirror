import re

import docker
import docker.errors
import requests
import streamlit as st
from huggingface_hub import HfApi, hf_hub_download

# Initialize session state variables if they don't exist
if "list_pressed" not in st.session_state:
    st.session_state["list_pressed"] = False
if "options" not in st.session_state:
    st.session_state["options"] = None
if "chat_model_file" not in st.session_state:
    st.session_state["chat_model_file"] = None


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

            st.session_state["chat_model_file"] = selected_file

            st.write(f"Downloaded '{selected_file}'")


def get_readme_content(repo_id, revision="main"):
    """
    Download the README.md file content from a Hugging Face repository.

    Parameters:
    - repo_id (str): The repository ID in the format "namespace/repository_name".
    - revision (str): The branch name, tag, or commit hash. Default is "main".

    Returns:
    - str: The content of the README.md file.
    """
    # Download the README.md file
    readme_path = hf_hub_download(
        repo_id=repo_id, filename="README.md", revision=revision
    )

    # Read the content of the README.md file
    with open(readme_path, "r", encoding="utf-8") as readme_file:
        readme_content = readme_file.read()

    return readme_content


def extract_prompt_type(readme_content):
    match = re.search(r"Prompt type: `(.+?)`", readme_content)
    if match:
        return match.group(1)  # This captures the value within the backticks
    else:
        return None


def extract_reverse_type(readme_content):
    match = re.search(r"Reverse prompt: `(.+?)`", readme_content)
    if match:
        return match.group(1)  # This captures the value within the backticks
    else:
        return None


def build_docker_image(dockerfile, tag, build_args=None, platform=None):
    """
    Build a Docker image with build arguments.

    Parameters:
    - dockerfile (str): Path to the directory containing the Dockerfile.
    - tag (str): The tag to give to the image.
    - build_args (dict, optional): A dictionary of build arguments.
    - platform (str, optional): Platform in the format os[/arch[/variant]].

    Returns:
    - The image object if the build was successful.
    """
    try:
        client = docker.from_env()
        image, build_log = client.images.build(
            path=dockerfile,
            tag=tag,
            buildargs=build_args,
            platform=platform,
        )
        for line in build_log:
            if "stream" in line:
                print(line["stream"].strip())
        return image
    except docker.errors.BuildError as build_error:
        print(f"Error building Docker image: {build_error}")
        for line in build_error.build_log:
            if "stream" in line:
                print(line["stream"].strip())
    except Exception as e:
        print(f"An error occurred: {e}")


if st.session_state["chat_model_file"]:
    # get the README.md content
    readme_content = get_readme_content(repo_id)

    # try to parse the prompt type from the README.md file
    prompt_template = extract_prompt_type(readme_content)
    if prompt_template is None:
        prompt_template = st.text_input("Prompt template")
    if prompt_template:
        st.write(f"Prompt template: {prompt_template}")

    # try to parse the reverse prompt from the README.md file
    reverse_prompt = extract_reverse_type(readme_content)
    if prompt_template is None and reverse_prompt is None:
        reverse_prompt = st.text_input("Reverse prompt")
    if reverse_prompt:
        st.write(f"Reverse prompt: {reverse_prompt}")

    if prompt_template:
        image_tag = st.text_input("Docker image tag")
        if image_tag:

            # Example usage
            dockerfile = "."  # Assuming the Dockerfile is in the current directory
            # tag = "apepkuss/qwen-2-0.5b-instruct:latest"  # "apepkuss/Qwen2-0.5B-Instruct-GGUF:latest"
            platform = "linux/arm64"
            if reverse_prompt:
                build_args = {
                    "CHAT_MODEL_FILE": st.session_state["chat_model_file"],
                    "PROMPT_TEMPLATE": prompt_template,
                    "REVERSE_TEMPLATE": reverse_prompt,
                }
            else:
                build_args = {
                    "CHAT_MODEL_FILE": st.session_state["chat_model_file"],
                    "PROMPT_TEMPLATE": prompt_template,
                }

            if st.button("Build Docker Image"):
                st.write(f"Building Docker image {image_tag}...")
                image = build_docker_image(dockerfile, image_tag, build_args, platform)

                if image:
                    st.write(f"Docker image {image_tag} built successfully.")
                # st.write(f"Docker image {image_tag} built successfully.")
