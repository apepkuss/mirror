import subprocess
import tempfile

import streamlit as st

# Streamlit UI
st.title("Docker Hub Image Uploader")

username = st.text_input("Docker Hub Username")
password = st.text_input("Docker Hub Password", type="password")
image_name = st.text_input("Docker Image Name (e.g., username/repository:tag)")
image_file = st.file_uploader("Choose a Docker Image File", type=["tar"])

if st.button("Upload Image"):
    if image_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(image_file.getvalue())
            tmp_file_path = tmp_file.name

            # Docker Login
            login_command = (
                f"echo {password} | docker login --username {username} --password-stdin"
            )
            login_result = subprocess.run(
                login_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if login_result.returncode != 0:
                st.error(f"Login Failed: {login_result.stderr.decode('utf-8')}")
            else:
                # Load Docker Image
                load_command = f"docker load < {tmp_file_path}"
                load_result = subprocess.run(
                    load_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                if load_result.returncode != 0:
                    st.error(
                        f"Loading Image Failed: {load_result.stderr.decode('utf-8')}"
                    )
                else:
                    # Tag and Push Docker Image
                    tag_command = f"docker tag {image_name.split(':')[0]} {image_name}"
                    tag_result = subprocess.run(
                        tag_command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    if tag_result.returncode != 0:
                        st.error(
                            f"Tagging Image Failed: {tag_result.stderr.decode('utf-8')}"
                        )
                    else:
                        push_command = f"docker push {image_name}"
                        push_result = subprocess.run(
                            push_command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )

                        if push_result.returncode != 0:
                            st.error(
                                f"Pushing Image Failed: {push_result.stderr.decode('utf-8')}"
                            )
                        else:
                            st.success("Image Uploaded Successfully")
