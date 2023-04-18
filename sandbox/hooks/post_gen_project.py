import os

if __name__ == "__main__":
    if "{{cookiecutter.create_file}}" == "no":
        os.unlink("{{cookiecutter.file_name}}.txt")
