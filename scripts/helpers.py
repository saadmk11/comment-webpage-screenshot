import subprocess


def print_message(message, message_type=None):
    """Helper function to print colorful outputs in GitHub Actions shell"""
    # https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions
    if not message_type:
        return subprocess.run(['echo', f'{message}'])

    if message_type == 'endgroup':
        return subprocess.run(['echo', '::endgroup::'])

    return subprocess.run(['echo', f'::{message_type}::{message}'])


def convert_string_to_list(string):
    """Helper function to convert a string to a list"""
    return [s.lstrip().rstrip() for s in string.split(',') if s]
