import os
import re


def update_first_title(file_path, old_title, new_title):
    with open(file_path, "r") as file:
        content = file.read()

    # Use regular expression to replace the first occurrence of the title
    pattern = re.compile(re.escape(old_title) + r"\n=+", re.DOTALL)
    updated_content = pattern.sub(
        new_title + "\n" + "=" * len(new_title), content, count=1
    )

    with open(file_path, "w") as file:
        file.write(updated_content)


if __name__ == "__main__":
    # Replace 'zpywallet' with your actual module name
    modules_rst_path = os.path.abspath("docs/source/modules.rst")
    update_first_title(modules_rst_path, "zpywallet", "API Reference")
