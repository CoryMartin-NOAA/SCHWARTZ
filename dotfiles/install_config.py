#!/usr/bin/env python3
import argparse
import configparser
import re
from typing import Any
from pathlib import Path
import os

def check_bash_profile_sourced():
    """
    Check if .bash_profile is sourced in .bashrc file
    """
    home_dir = Path.home()
    bashrc_file = home_dir / ".bashrc"
    bash_profile_file = home_dir / ".bash_profile"

    if not bashrc_file.exists():
        print(".bashrc file not found")
        return False

    with open(bashrc_file, "r", encoding='utf-8') as f:
        bashrc_contents = f.read()

    if f"source {bash_profile_file}" in bashrc_contents or f". {bash_profile_file}" in bashrc_contents:
        print(".bash_profile is sourced in .bashrc")
        return True
    else:
        print(".bash_profile is not sourced in .bashrc")
        return False


def render_template(template_path: str, context: dict[str, Any]) -> str:
    """Renders a template file using the given context.

    Args:
        template_path (str): The path to the template file.
        context (dict): A dictionary containing variable names and their corresponding values.

    Returns:
        str: The rendered template.
    """
    if not context:
        raise ValueError("Context dictionary cannot be empty")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    def replace_variables(template_content, context):
        for key, value in context.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if not isinstance(nested_key, str):
                        raise ValueError("Nested key in context dictionary must be a string")
                    if not isinstance(nested_value, (int, float, str, bool)):
                        raise ValueError("Nested value in context dictionary must be a string, integer, float, or boolean")
                    template_content = template_content.replace('{{{{ {0}.{1} }}}}'.format(key, nested_key), str(nested_value))
            else:
                if not isinstance(key, str):
                    raise ValueError("Key in context dictionary must be a string")
                if not isinstance(value, (int, float, str, bool)):
                    raise ValueError("Value in context dictionary must be a string, integer, float, or boolean")
                template_content = template_content.replace('{{{{ {0} }}}}'.format(key), str(value))
        return template_content

    template_content = replace_variables(template_content, context)

    # Handle if statements
    while True:
        match = re.search(r'{% if (.*?) %}(.*?){% endif %}', template_content, re.DOTALL)
        if not match:
            break
        condition, block = match.groups()
        if not isinstance(condition, str):
            raise ValueError("Condition in if statement must be a string")
        if not isinstance(block, str):
            raise ValueError("Block in if statement must be a string")

    return template_content

def read_toml_file(filename: str) -> dict:
    """Reads a TOML file and returns its contents as a dictionary."""
    config = configparser.ConfigParser()
    config.read(filename)
    return {section: dict(config.items(section)) for section in config.sections()}


def main() -> None:
    """
    Reads a TOML file and prints its contents.

    Args:
        filename (str): The path to the TOML file.
        machine (str): The machine in which use the template from.
    """
    parser = argparse.ArgumentParser(description="Reads a TOML file and prints its contents.")
    parser.add_argument("-f", "--filename", help="The path to the TOML file", default="config.toml")
    parser.add_argument("-m", "--machine", help="The machine in which use the template from", required=True)
    parser.add_argument("-s", "--shell", help="shell on which to install | bash or powershell", required=False, default="bash")
    parser.add_argument("--install", help="Install the environment", action=argparse.BooleanOptionalAction, required=False, default=True)
    args = parser.parse_args()
    install = args.install
    config = read_toml_file(filename=args.filename)


    # get home directory
    # =================
    if not install:
        home = Path.cwd()
    else:
        home = Path.home()

    # Change bash aliases
    # ====================
    alias = render_template(template_path="bash/bash_aliases", context=config)

    # write bash aliases to $home/.bash_aliases
    with open(file=f"{home}/.bash_aliases", mode="w", encoding='utf-8') as f:
        f.write(alias)

    # Change bash functions
    # ======================
    functions = render_template(template_path="bash/bash_functions", context=config)

    # write bash functions to $home/.bash_functions
    # print(functions)
    with open(file=f"{home}/.bash_functions", mode="w", encoding='utf-8') as f:
        f.write(functions)

    # Change bash profile
    # ====================
    if args.shell.lower() == 'bash':
        profile = render_template(template_path="bash/bash_profile", context=config)

        machine_templates = {
            "hera": "hera",
            "orion": "orion",
            "hercules": "hercules",
            "mac": "mac",
            "wcoss": "wcoss",
            "niagara": "niagara",
            "gaea": "gaea"
        }
        machine_profile = render_template(template_path=f"bash/machines/{machine_templates[args.machine]}", context=config)

        profile = profile + machine_profile

        # write bash profile to $home/.bash_profile
        with open(file=f"{home}/.bash_profile", mode="w", encoding='utf-8') as f:
            f.write(profile)

        # check if .bash_profile is sourced in your ~/.bashrc file
        if not check_bash_profile_sourced():
            # add source .bash_priofile to ~/.bashrc
            with open(file=f"{home}/.bashrc", mode="a", encoding='utf-8') as f:
                print("Adding a line to source the .bash_profile within your .bashrc file to make sure it's sourced")
                f.write("\n" + f"source {home}/.bash_profile" + "\n")

    # Change Powershell profile
    if args.shell.lower() == 'powershell':
        profile = render_template(template_path="powershell/Microsoft.PowerShell_Profile.ps1")

        try:
            with open(file=f"{home}/Microsoft.PowerShell_Profile.ps1", mode="w", encoding='utf-8') as f:
                # Perform file operations
                pass
        except IOError as e:
            print(f"An error occurred: {e}")

    # Change .gitconfig
    # ==================
    gitconfig = render_template(template_path="git/gitconfig", context=config)

    # write .gitconfig to $home/.gitconfig
    # print(gitconfig)
    with open(file=f"{home}/.gitconfig", mode="w", encoding='utf-8') as f:
        f.write(gitconfig)

    # Change github_profile
    #======================
    github_profile = render_template(template_path="git/github_profile", context=config)
    with open(file=f"{home}/.github_profile", mode="w", encoding='utf-8') as f:
        f.write(github_profile)

    # Add Machine specific git-credentials
    #=====================================
    git_creds = render_template(template_path=f"git/machines/{machine_templates.get(args.machine, '')}", context=config)

    with open(file=f"{home}/.git-credentials", mode="w", encoding='utf-8') as f:
        f.write(git_creds)



if __name__ == "__main__":
    main()
