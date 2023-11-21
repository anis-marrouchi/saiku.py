#!/usr/bin/env python
import click
import os
import importlib.util
import sys
from pathlib import Path

def get_directories(source):
    return [d.name for d in os.scandir(source) if d.is_dir()]

@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def cli(ctx):
    """Saiku AI agent to help automate your tasks"""
    if ctx.invoked_subcommand is None:
        # Call your default command here
        ctx.forward(default_command)

def load_commands():
    commands_path = Path(__file__).parent / 'commands'
    command_dirs = get_directories(commands_path)

    for dir in command_dirs:
        # Skip the default command directory
        if dir == 'default':
            continue
        module_path = commands_path / dir / 'main.py'
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(dir, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cli.add_command(module.command)

spec = importlib.util.spec_from_file_location("default", Path(__file__).parent / 'commands/default/main.py')
default_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(default_module)
default_command = default_module.command

load_commands()

if __name__ == '__main__':
    cli()
