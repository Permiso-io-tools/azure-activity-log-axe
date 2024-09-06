"""
Tool Name: Azure Activity Log Axe
Script Name: interactive.py
Author: Nathan Eades
Date: 2024-06-01
Description: Controls Interactive Mode.
License: Apache License
"""

#   This file is part of Azure Activity Log Axe.
#
#   Copyright 2024 Permiso Security <https://permiso.io>
#         Nathan Eades:
#             - LinkedIn: <@eadesclouddef>
#             - GitHub: <eadesclouddef> or <neades2305>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import app.cli.commands as commands # avoid circular import
import shlex
from app.utils.logger import get_logger

interactive_logger = get_logger('interactive')

def repl(ctx):
    while True:
        # Takes input on loop to run each command while data is in memory
        command = input('azure-activity-log-axe>> ').strip()
        if command == 'exit':
            break
        elif command == 'summary':
            ctx.invoke(commands.summary)
        elif command.startswith('aggrid'):
            process_repl_aggrid(ctx, command, commands.aggrid)
        elif command.startswith('save-axe-keyed-data'):
            process_repl_save_command(ctx, command, commands.save_axe_keyed_data)
        elif command.startswith('save-simplified-data'):
            process_repl_save_command(ctx, command, commands.save_simplified_data)
        elif command.startswith('show-axe-keyed-data'):
            process_repl_show_command(ctx, command, commands.show_axe_keyed_data)
        elif command.startswith('show-simplified-data'):
            process_repl_show_command(ctx, command, commands.show_simplified_data)
        elif command == 'help' or command == 'h':
            repl_print_help()
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")


def repl_print_help():
    print("""
    Usage: COMMAND [OPTIONS]

    Azure Activity Log Axe: Interactive Mode.

    Options:
    --select TEXT             Field Selection. Comma Delimited E.g. axeKey,caller,operationName (Used by the Show & Save commands.)
    --field-value-select TEXT   Select rows based on the value of a field. E.g. operationName:microsoft.storage/storageaccounts/listKeys/action (Used by the Show & Save commands. Does NOT support nested field. See README for more examples.)
    --field-value-deselect TEXT   De-select rows based on the value of a field. E.g. operationName:microsoft.storage/storageaccounts/listKeys/action (Used by the Show & Save commands. Does NOT support nested field. See README for more examples.)
    --output-type [json|csv]  Output Type. (Used by the Show & Save commands.)
    --filepath TEXT           Absolute File Path. (Used by the Save commands.)

    Commands:
    aggrid                Browser GUI - Navigate the data using AG-Grid.
    save-axe-keyed-data   Saves the original azure activity log data plus axeKey to a json or csv file.
    save-simplified-data  Saves the simplified azure activity log data to a json or csv file.
    show-axe-keyed-data   Prints the original azure activity log data plus axeKey (json or csv), to the cli.
    show-simplified-data  Prints the simplified azure activity log data (json or csv) to the cli.
    summary               Prints a summary of axe keyed log details.
    h, help               Show this message and exit.
    """)


def process_repl_save_command(ctx, command, func):
    # This processor gets called to collect all arguments before sending to command
    try:
        args = shlex.split(command)
    except ValueError as e:
        interactive_logger.warning("Argument parsing error: you did not properly close a parenthesized string.")
    try:
        command_args = {
            'field_value_select': [], # Initialize list for multi entry option/arg
            'field_value_deselect': []
        }
        iterator_obj = iter(args[1:])
        for arg in iterator_obj:
            if arg == '--select':
                command_args['select'] = next(iterator_obj)
            elif arg == '--field-value-select':
                command_args['field_value_select'].append(next(iterator_obj))
            elif arg == '--field-value-deselect':
                command_args['field_value_deselect'].append(next(iterator_obj))
            elif arg == '--output-type':
                command_args['output_type'] = next(iterator_obj)
            elif arg == '--filepath':
                command_args['filepath'] = next(iterator_obj)
            elif arg.startswith('--'):
                interactive_logger.warning(f'Invalid arg {arg}, skipped.')

        command_args['field_value_select'] = tuple(command_args['field_value_select']) # Set multi entry option/arg to expected tuple
        command_args['field_value_deselect'] = tuple(command_args['field_value_deselect']) # Set multi entry option/arg to expected tuple
        ctx.invoke(func, **command_args)
    except (ValueError, IndexError):
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv> --filepath <file_path>')
    except StopIteration:
        interactive_logger.warning(f'You have provided an argument with no input. \n Usage: --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv> --filepath <file_path>')
    except Exception as e:
        interactive_logger.error(f'Unexpected error: {str(e)}')
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv> --filepath <file_path>')


def process_repl_show_command(ctx, command, func):
    # This processor gets called to collect all arguments before sending to command
    try:
        args = shlex.split(command)
    except ValueError as e:
        interactive_logger.warning("Argument parsing error: you did not properly close a parenthesized string.")
    try:
        command_args = {
            'field_value_select': [], # Initialize list for multi entry option/arg
            'field_value_deselect': []
        }
        iterator_obj = iter(args[1:])
        for arg in iterator_obj:
            if arg == '--select':
                command_args['select'] = next(iterator_obj)
            elif arg == '--field-value-select':
                command_args['field_value_select'].append(next(iterator_obj))
            elif arg == '--field-value-deselect':
                command_args['field_value_deselect'].append(next(iterator_obj))
            elif arg == '--output-type':
                command_args['output_type'] = next(iterator_obj)
            elif arg.startswith('--'):
                 interactive_logger.warning(f'Invalid arg {arg}, skipped.')

        command_args['field_value_select'] = tuple(command_args['field_value_select']) # Set multi entry option/arg to expected tuple
        command_args['field_value_deselect'] = tuple(command_args['field_value_deselect']) # Set multi entry option/arg to expected tuple
        ctx.invoke(func, **command_args)
    except (ValueError, IndexError):
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv>')
    except StopIteration:
        interactive_logger.warning(f'You have provided an argument with no input. \n Usage: --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv>')
    except Exception as e:
        interactive_logger.error(f'Unexpected error: {str(e)}')
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,> --output-type <json|csv>')


def process_repl_aggrid(ctx, command, func):
    # This processor gets called to collect all arguments before sending to command
    try:
        args = shlex.split(command)
    except ValueError as e:
        interactive_logger.warning("Argument parsing error: you did not properly close a parenthesized string.")
    try:
        command_args = {
            'field_value_select': [], # Initialize list for multi entry option/arg
            'field_value_deselect': []
        }
        iterator_obj = iter(args[1:])
        for arg in iterator_obj:
            if arg == '--select':
                command_args['select'] = next(iterator_obj)
            elif arg == '--field-value-select':
                command_args['field_value_select'].append(next(iterator_obj))
            elif arg == '--field-value-deselect':
                command_args['field_value_deselect'].append(next(iterator_obj))
            elif arg.startswith('--'):
                 interactive_logger.warning(f'Invalid arg {arg}, skipped.')

        command_args['field_value_select'] = tuple(command_args['field_value_select']) # Set multi entry option/arg to expected tuple
        command_args['field_value_deselect'] = tuple(command_args['field_value_deselect']) # Set multi entry option/arg to expected tuple
        ctx.invoke(func, **command_args)
    except (ValueError, IndexError):
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,>')
    except StopIteration:
        interactive_logger.warning(f'You have provided an argument with no input. \n Usage: --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,>')
    except Exception as e:
        interactive_logger.error(f'Unexpected error: {str(e)}')
        interactive_logger.warning(f'Usage: {command.split()[0]} --select <fields,> --field-value-select <field:value,> --field-value-deselect <field:value,>')