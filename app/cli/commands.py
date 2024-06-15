"""
Tool Name: Azure Activity Log Axe
Script Name: commands.py
Author: Nathan Eades
Date: 2024-06-01
Description: Controls Click Interface.
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

import click
import json
import pandas as pd
from pathlib import Path
import re
import sys
from .interactive import repl
from app.core.azure_activity_processor import AzureActivityProcessor
from app.utils.config import valid_output_types
from app.utils.file_io import write_activity_log_data
from app.utils.log_getters import get_azure_activity_restapi
from app.utils.logger import get_logger
from rich import print_json
from rich.console import Console

command_logger = get_logger('commands')

@click.group()
@click.option('--subscription-id', required=True, help='Azure Subscription ID')
@click.option('--start-time', default=None, help='Filter Start Time (If start & end time are not both provided, defaults to last 24 hours. UTC)')
@click.option('--end-time', default=None, help='Filter End Time (If start & end time are not both provided, defaults to last 24 hours. UTC)')
@click.option('--correlation-id', default=None, help='Azure Correlation ID (Must be within start & end time (Microsoft Endpoint Requirement))')
@click.option('--select', default=None, help='SUB: Field Selection. Comma Delimited E.g. axeKey,caller,operationName (Used by the Show & Save commands.)')
@click.option('--field-value-select', multiple=True, help='SUB: Select rows based on the value of a field. E.g. operationName:microsoft.storage/storageaccounts/listKeys/action (Used by the Show & Save commands. Does NOT support nested field. See README for more examples.)')
@click.option('--field-value-deselect', multiple=True, help='SUB: De-select rows based on the value of a field. E.g. operationName:microsoft.storage/storageaccounts/listKeys/action (Used by the Show & Save commands. Does NOT support nested field. See README for more examples.)')
@click.option('--output-type', type=click.Choice(['json', 'csv']), default='json', help='SUB: Output Type. (Used by the Show & Save commands.)')
@click.option('--filepath', default=None, help='SUB: Absolute File Path. (Used by the Save commands.)')
@click.pass_context
def azure_activity_log_axe(ctx, subscription_id: str, start_time: str | None, end_time: str | None, correlation_id: str | None, select: str | None, field_value_select, field_value_deselect, output_type: str | None, filepath: str | None):
    """
    Azure Activity Log Axe: Simplify and understand your logs.
    """
    console = Console()
    logDict = get_azure_activity_restapi(subscription_id, start_time, end_time, correlation_id)
    if logDict:
        console.print("[+] Azure activity logs obtained.", style="bold green")
        azure_activity: AzureActivityProcessor = AzureActivityProcessor()
        console.print("[+] Processing...", style="bold green")
        azure_activity.get_axe_key_azure_activity(logDict)
        azure_activity.get_simplified_azure_activity_list(azure_activity.get_simplified_azure_activity(azure_activity.keyed_log_data))
        console.print("[+] Axe keyed and simplified Azure activity logs are ready.", style="bold green")
    else:
        console.print("[-] Failed to obtain logs.", style="bold red")
        sys.exit(1)

    # Store the AzureActivityProcessor instance and passes arguments in the context object
    ctx.obj['select_param'] = select
    ctx.obj['field_value_select_param'] = tuple(field_value_select)
    ctx.obj['field_value_deselect_param'] = tuple(field_value_deselect)
    ctx.obj['output_type_param'] = output_type
    ctx.obj['filepath_param'] = Path(filepath) if filepath else None
    ctx.obj['azure_activity'] = azure_activity


@azure_activity_log_axe.command()
@click.pass_context
def summary(ctx):
    """
    Prints a summary of axe keyed log details.
    """
    azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']
    azure_activity.get_keyed_log_summary()

    Console().print("[+] Axe Keyed Log Summary:", style="bold green")
    print_json(json.dumps(azure_activity.summary_keyed_log_data))


@azure_activity_log_axe.command()
@click.pass_context
def save_axe_keyed_data(ctx, select: str | None = None, field_value_select: tuple | None = None, field_value_deselect: tuple | None = None, filepath: str | None = None, output_type: str | None = None):
    """
    Saves the original azure activity log data plus axeKey to a json or csv file.
    """
    default_filename = "axe_keyed_activity_data"
    azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']

    # Assign aruments from options.
    # 1st assignment check is from interactive, 2nd is running the python app command directly
    select = select or ctx.obj['select_param']
    field_value_select = field_value_select or ctx.obj['field_value_select_param']
    field_value_deselect = field_value_deselect or ctx.obj['field_value_deselect_param']
    output_type = output_type or ctx.obj['output_type_param'] or 'json'
    filepath: Path | None = Path(filepath) if filepath else None or ctx.obj['filepath_param']

    # Apply any filters that exist
    if select or field_value_select or field_value_deselect:
        keyed_log_data = df_filter(select, field_value_select, field_value_deselect, azure_activity.keyed_log_data)
        if not keyed_log_data.empty:
            Console().print("[+] Original azure activity log data plus Axe Key written to file.", style="bold green")
            write_activity_log_data(keyed_log_data.to_dict(orient='records'), default_filename, filepath, output_type)
        else:
            command_logger.warning(f'It appears your filters resulted in an empty list:\n select: {select}\n field_value_select: {field_value_select}\n field_value_deselect: {field_value_deselect}')
    else:
        Console().print("[+] Original azure activity log data plus Axe Key written to file.", style="bold green")
        write_activity_log_data(azure_activity.keyed_log_data, default_filename, filepath, output_type)


@azure_activity_log_axe.command()
@click.pass_context
def save_simplified_data(ctx, select: str | None = None, field_value_select: tuple | None = None, field_value_deselect: tuple | None = None, filepath: str | None = None, output_type: str | None = None):
    """
    Saves the simplified azure activity log data to a json or csv file.
    """
    default_filename = "simplified_activity_data"
    azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']

    # Assign aruments from options.
    # 1st assignment check is from interactive, 2nd is running the python app command directly
    select = select or ctx.obj['select_param']
    field_value_select = field_value_select or ctx.obj['field_value_select_param']
    field_value_deselect = field_value_deselect or ctx.obj['field_value_deselect_param']
    output_type = output_type or ctx.obj['output_type_param'] or 'json'
    filepath: Path | None = Path(filepath) if filepath else None or ctx.obj['filepath_param']

    # Apply any filters that exist
    if select or field_value_deselect:
        simplified_log_data_list = df_filter(select, field_value_select, field_value_deselect, azure_activity.simplified_log_data_list)
        if not simplified_log_data_list.empty:
            Console().print("[+] Simplified Azure activity log data written to file:", style="bold green")
            write_activity_log_data(simplified_log_data_list.to_dict(orient='records'), default_filename, filepath, output_type)
        else:
            command_logger.warning(f'It appears your filters resulted in an empty list:\n select: {select}\n field_value_select: {field_value_select}\n field_value_deselect: {field_value_deselect}')
    else:
        Console().print("[+] Simplified Azure activity log data written to file:", style="bold green")
        write_activity_log_data(azure_activity.simplified_log_data_list, default_filename, filepath, output_type)


@azure_activity_log_axe.command()
@click.pass_context
def show_axe_keyed_data(ctx, select: str | None = None, field_value_select: tuple | None = None, field_value_deselect: tuple | None = None, output_type: str | None = None):
    """
    Prints the original azure activity log data plus axeKey (json or csv), to the cli.
    """
    azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']

    # Assign aruments from options.
    # 1st assignment check is from interactive, 2nd is running the python app command directly
    select = select or ctx.obj['select_param']
    field_value_select = field_value_select or ctx.obj['field_value_select_param']
    field_value_deselect = field_value_deselect or ctx.obj['field_value_deselect_param']
    output_type = output_type or ctx.obj['output_type_param'] or 'json'

    # Apply any filters that exist
    if select or field_value_select or field_value_deselect:
        keyed_log_data = df_filter(select, field_value_select, field_value_deselect, azure_activity.keyed_log_data)
        if not keyed_log_data.empty:
            Console().print("[+] Original azure activity log data plus Axe Key:", style="bold green")
            print_output_type(output_type, keyed_log_data.to_dict(orient='records'))
        else:
            command_logger.info(f'It appears your filters resulted in an empty list:\n select: {select}\n field_value_select: {field_value_select}\n field_value_deselect: {field_value_deselect}')
    else:
        Console().print("[+] Original azure activity log data Axe Key:", style="bold green")
        print_output_type(output_type, azure_activity.keyed_log_data)


@azure_activity_log_axe.command()
@click.pass_context
def show_simplified_data(ctx, select: str | None = None, field_value_select: tuple | None = None, field_value_deselect: tuple | None = None, output_type: str | None = None):
    """
    Prints the simplified azure activity log data (json or csv) to the cli.
    """
    azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']

    # Assign aruments from options.
    # 1st assignment check is from interactive, 2nd is running the python app command directly
    select = select or ctx.obj['select_param']
    field_value_select = field_value_select or ctx.obj['field_value_select_param']
    field_value_deselect = field_value_deselect or ctx.obj['field_value_deselect_param']
    output_type = output_type or ctx.obj['output_type_param'] or 'json'

    # Apply any filters that exist
    if select or field_value_select or field_value_deselect:
        simplified_log_data_list = df_filter(select, field_value_select, field_value_deselect, azure_activity.simplified_log_data_list)
        if not simplified_log_data_list.empty:
            Console().print("[+] Simplified Azure activity log data:", style="bold green")
            print_output_type(output_type, simplified_log_data_list.to_dict(orient='records'))
        else:
            command_logger.info(f'It appears your filters resulted in an empty list:\n select: {select}\n field_value_select: {field_value_select}\n field_value_deselect: {field_value_deselect}')
    else:
        Console().print("[+] Simplified Azure activity log data:", style="bold green")
        print_output_type(output_type, azure_activity.simplified_log_data_list)


@azure_activity_log_axe.command()
@click.pass_context
def interactive(ctx):
    """
    Interactive REPL Interface to run Azure Activity Log Axe.
    """
    repl(ctx)


def print_output_type(output_type: str | None, azure_activity_data: list[dict]):
    # Secondary override to force json if None
    output_type = output_type or 'json'
    # Force a correct file type
    if output_type not in valid_output_types:
        command_logger.info(f'json or csv are the only valid output types. Defaulting to json.')
        output_type = 'json'

    if output_type == 'json':
        print(json.dumps(azure_activity_data, indent=2))
    elif output_type == 'csv':
        df = pd.DataFrame(azure_activity_data)
        pd.set_option('display.max_colwidth', 40)
        pd.set_option('display.width', None)
        pd.set_option('display.max_columns', len(df.columns))
        pd.set_option('display.max_rows', None)
        print(df)


def df_filter(select: str | None, field_value_select: tuple | None, field_value_deselect: tuple | None, azure_activity_data: list[dict]) -> pd.DataFrame | None:
    # Take all filter options and filter down DataFrame
    try:
        df = pd.DataFrame(azure_activity_data)

        if field_value_select:
            for condition in field_value_select:
                field, values = condition.split(':') # field:"value,value"
                field_value_select_list = values.split(",") # [value,value]
                df = df[df[field].isin(field_value_select_list)]
        if field_value_deselect:
            for condition in field_value_deselect:
                field, values = condition.split(':') # field:"value,value"
                field_value_deselect_list = values.split(",") # [value,value]
                df = df[~df[field].isin(field_value_deselect_list)]
        if select:
            select_list = select.split(",") # [value,value]
            df = df[select_list]

        return df
    except KeyError as e:
        failed_fields = re.search(r"^None of \[Index\((.*?\])|^(\[.*?\])\snot in index", e.args[0])
        if failed_fields and failed_fields.group(1) is not None:
            command_logger.warning(f'The following fields do not exist: {failed_fields.group(1)}.')
        elif failed_fields and failed_fields.group(2) is not None and failed_fields.group(2) != "['']":
            command_logger.warning(f'The following fields do not exist: {failed_fields.group(2)}.')
        elif e.args[0] is not None:
            command_logger.warning(f'The following fields do not exist: {e.args[0]}.')
        else:
            command_logger.warning(f'Usage: --select value1,value2')
            command_logger.warning(f'Ensure your select does not have spaces or quotes.')
        return pd.DataFrame()  # return empty dataframe
    except ValueError as e:
        command_logger.warning(f'Ensure field_value filters use a ":" to separate field:comma,delimited,list.')
        return pd.DataFrame()  # return empty dataframe

azure_activity_log_axe.context_settings = dict(
    help_option_names=['-h', '--help'],
    max_content_width=110  # Adjust this width based on your needs
)
