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
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import json
import logging
import pandas as pd
import psutil
import re
import socket
import sys
from dash import Dash, dcc, html, Input, Patch, State, callback_context, no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pathlib import Path
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
def aggrid(ctx, select: str | None = None, field_value_select: tuple | None = None, field_value_deselect: tuple | None = None):
    """
    Browser GUI - Navigate the data using AG-Grid.
    """

    # Set up logger for Dash app
    dash_logger = get_logger('dash_app')

    # Redirect Werkzeug logger to custom logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    werkzeug_logger.handlers = []  # Clear existing handlers
    werkzeug_logger.addHandler(dash_logger.handlers[0])

    try:
        # Get Data from CTX Object
        azure_activity: AzureActivityProcessor = ctx.obj['azure_activity']
        # Assign aruments from options.
        # 1st assignment check is from interactive, 2nd is running the python app command directly
        select = select or ctx.obj['select_param']
        field_value_select = field_value_select or ctx.obj['field_value_select_param']
        field_value_deselect = field_value_deselect or ctx.obj['field_value_deselect_param']
        dfKeyedLogData: pd.DataFrame | None = None
        dfSimplifiedData: pd.DataFrame | None = None

        # Apply any filters that exist
        if select or field_value_select or field_value_deselect:
            dfKeyedLogData = df_filter(select, field_value_select, field_value_deselect, azure_activity.keyed_log_data)
            dfSimplifiedData = df_filter(select, field_value_select, field_value_deselect, azure_activity.simplified_log_data_list)
        else:
            dfKeyedLogData = azure_activity.keyed_log_data
            dfSimplifiedData = azure_activity.simplified_log_data_list

        # Check that field is JSON
        def is_json_serializable(value) -> bool:
            try:
                json.dumps(value)
                return True
            except (TypeError, OverflowError):
                return False

        # Convert fields to JSON strings if they are JSON serializable
        def jsonSerialize(og_df: pd.DataFrame) -> pd.DataFrame:
            df: pd.DataFrame = og_df.copy()
            for col in df.columns:
                df[col] = df[col].apply(lambda x: json.dumps(x) if is_json_serializable(x) else x)
            return df
        # Clean Data and Create Default Columns
        convertedDfKeyedLogData: pd.DataFrame = jsonSerialize(dfKeyedLogData)
        convertedDfSimplifiedData: pd.DataFrame = jsonSerialize(dfSimplifiedData)
        keyed_default_columns: list[str] = ['axeKey', 'operationName', 'correlationId', 'operationId', 'caller', 'category', 'eventTimestamp', 'status']
        simplified_default_columns: list[str] = ['axeKey', 'operationName', 'correlationId', 'operationIds', 'caller', 'category', 'startTime', 'endTime', 'statusCounts']
        keyedLogDataColumnDefDefaults: list[dict[str,str]] = [{"field": str(col)} for col in keyed_default_columns]
        simplifiedDataColumnDefDefaults: list[dict[str,str]] = [{"field": str(col)} for col in simplified_default_columns]

        # Create App & Get Stylesheets
        app: Dash = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            assets_folder="../../assets"
        )

        app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>Azure Activity Log Axe</title>
                {%favicon%}
                {%css%}
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''

        app.layout = html.Div([
            html.Div([
                html.Div([
                    dcc.Input(id='quick-filter-input', placeholder='global filter...'),
                ], className='button-group'),
                html.Div([
                    html.Div([
                        html.Div(id='column-select-div-button', className='custom-button-selector'),
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle('Column Select'), close_button=False),
                            dbc.ModalBody(id='column-select-body'),
                            dbc.ModalFooter([
                                dbc.Button('Save', id='save-column-select-button', className='modal-footer-button'),
                                dbc.Button('Close', id='close-column-select-button', className='modal-footer-button'),
                            ]),
                        ], id='column-select-modal', is_open=False, scrollable=True),
                    ], className='button-group-selector'),
                    html.Div([
                        html.Button(
                            children=[
                                html.Div('Keyed Data', className='button-text-dev'),
                                html.Div(len(dfKeyedLogData), id='keyed-event-count', className='event-counter event-counter-keyed'),
                            ], id='keyed-data-button', className='custom-button',
                        ),
                    ], className='button-group-keyed'),
                    html.Div([
                        html.Button(
                            children=[
                                html.Div('Simplified Data', className='button-text-dev'),
                                html.Div(len(dfSimplifiedData), id='simplified-event-count', className='event-counter event-counter-simplified'),
                            ], id='simplified-data-button', className='custom-button'),
                    ], className='button-with-counter'),
                ], className='button-group'),
            ], id='button-container'),
            html.Div([
                dag.AgGrid(
                    id='ag-grid',
                    rowData=[],
                    columnDefs=[],
                    defaultColDef={
                        'resizable': True,
                        'sortable': True,
                        'filter': True,
                        'minWidth': 125,
                    },
                    dashGridOptions={
                        'enableCellTextSelection': True,
                        'ensureDomOrder': True,
                        'pagination': True,
                        'paginationAutoPageSize': True,
                        'headerHeight': 30,
                        'footerHeight': 30,
                        'rowHeight': 30,
                    },
                )
            ], id='ag-grid-container'),
            html.Div([
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Data Viewer'), close_button=False),
                        dbc.ModalBody(id='viewer-modal-content'),
                        dbc.ModalFooter(
                            dbc.Button('Close', id='close-modal-button', className='modal-footer-button')
                        ),
                    ],
                    id='viewer-modal',
                    size='lg',
                    is_open=False,
                    centered=True,
                ),
            ]),
            dcc.Store(id='all-columns', data=[]),
        ], id='app-container')

        # Global Filter Controller
        @app.callback(
            Output('ag-grid', 'dashGridOptions'),
            Input('quick-filter-input', 'value')
        )
        def update_filter(filter_value) -> Patch:
            newFilter = Patch()
            newFilter['quickFilterText'] = filter_value
            return newFilter

        # AG-GRID Cell Data Viewer Modal Controller
        @app.callback(
            Output('viewer-modal', 'is_open'), # Display Control
            Output('viewer-modal-content', 'children'),
            Input('ag-grid', 'cellDoubleClicked'),
            Input('close-modal-button', 'n_clicks'),
            State('viewer-modal', 'is_open'),
        )
        def show_json_modal(cell_double_clicked: dict | None, close_click, is_open) -> tuple:
            # No Update
            if callback_context.triggered_id == 'close-modal-button':
                return False, no_update
            if cell_double_clicked is None:
                return False, no_update

            # Double Click Modal Control
            cell_value: str = cell_double_clicked.get('value')
            try:
                return_value: str = ''
                if cell_value.startswith('{') or cell_value.startswith('['): # JSON
                    parsed_json = json.loads(cell_value)
                    return_value = json.dumps(parsed_json, indent=2)
                elif cell_value.startswith('"'): # STR
                    return_value = cell_value.strip('"')
                else: # OTHER
                    return_value = cell_value
                return True, html.Pre(return_value)
            except (json.JSONDecodeError, TypeError, ValueError):
                return False, cell_value

        # AG-GRID Data & UI Button Color Controller
        @app.callback(
            Output('ag-grid', 'rowData'), # Data Output
            Output('ag-grid', 'columnDefs'), # Column Definitions
            Output('all-columns', 'data'), # Controls Viewable Columns
            Output('keyed-data-button', 'className'), # Data Selection Button Class
            Output('simplified-data-button', 'className'), # Data Selection Button Class
            Input('keyed-data-button', 'n_clicks'),
            Input('simplified-data-button', 'n_clicks'),
            Input('save-column-select-button', 'n_clicks'),
            State('column-select-body', 'children'), # Get Checked Fields
        )
        def button_controller(
            keyed_clicks: int,
            simp_clicks: int,
            save_clicks: int,
            checkbox_modal_body: dict[str, any],
            ) -> tuple:
            if not callback_context.triggered:
                # No Change.
                raise PreventUpdate
            else:
                triggered_id = callback_context.triggered_id

                # UI Color CSS Classes
                normal_button_class = 'custom-button'
                active_button_class = 'custom-button active'

                # Display Relevant Data & Correct Color
                if triggered_id == 'keyed-data-button':
                    return convertedDfKeyedLogData.to_dict('records'), keyedLogDataColumnDefDefaults, sorted(list(dfKeyedLogData.columns)), active_button_class, normal_button_class
                elif triggered_id == 'simplified-data-button':
                    return convertedDfSimplifiedData.to_dict('records'), simplifiedDataColumnDefDefaults, sorted(list(dfSimplifiedData.columns)), normal_button_class, active_button_class

                # Save New Column Selections
                elif triggered_id == 'save-column-select-button':
                    selected_columns = []
                    checkboxes = checkbox_modal_body.get('props', {}).get('children', [])
                    for checkbox in checkboxes:
                        props = checkbox.get('props', {})
                        if props.get('value', False):
                            label = props.get('label')
                            if label:
                                selected_columns.append(label)

                    if selected_columns:
                        new_columnDefs = [{'field': col} for col in selected_columns]
                        return no_update, new_columnDefs, no_update, no_update, no_update
                    else:
                        raise PreventUpdate
                # No Change.
                raise PreventUpdate

        # Data Columns Selection Modal Controller
        @app.callback(
            Output('column-select-modal', 'is_open'), # Display Control
            Output('column-select-body', 'children'), # Show Columns in Selector Modal
            Input('column-select-div-button', 'n_clicks'),
            Input('save-column-select-button', 'n_clicks'),
            Input('close-column-select-button', 'n_clicks'),
            State('column-select-modal', 'is_open'),
            State('all-columns', 'data'),
            State('ag-grid', 'columnDefs'),
        )
        def toggle_column_select_modal(
            n_open: int,
            n_save: int,
            n_close: int,
            is_open: bool,
            available_columns: list[str],
            current_columnDefs) -> tuple:
            # No Change
            if not callback_context.triggered:
                raise PreventUpdate

            triggered_id = callback_context.triggered_id

            # No Change
            if triggered_id == 'close-column-select-button':
                return False, no_update
            if triggered_id == 'save-column-select-button':
                return False, no_update

            # Display Selecting Checkboxes
            if triggered_id == 'column-select-div-button':
                current_columns = [col['field'] for col in current_columnDefs]
                modal_body = dbc.Form([
                    dbc.Checkbox(
                        id=f'column-checkbox-{col}',
                        label=col,
                        value=col in current_columns,
                        className='mb-2'
                    ) for col in available_columns
                ])
                return True, modal_body

            # No Change
            return False, no_update

        # Dash App Start
        run_dash_app(dash_logger, app)
    except Exception as e:
        dash_logger.error(f"Error in Dash application: {str(e)}")
        command_logger.info(f"An error occurred: {str(e)}")


@azure_activity_log_axe.command()
@click.pass_context
def interactive(ctx):
    """
    Interactive REPL Interface to run Azure Activity Log Axe.
    """
    repl(ctx)


def print_output_type(output_type: str | None, azure_activity_data: list[dict]) -> None:
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
                field_value_select_list = values.split(',') # [value,value]
                if isinstance(df[field].iloc[0], dict):
                    df = df[df[field].apply(lambda x: x.get('value') in field_value_select_list)]
                else:
                    df = df[df[field].isin(field_value_select_list)]
        if field_value_deselect:
            for condition in field_value_deselect:
                field, values = condition.split(':') # field:"value,value"
                field_value_deselect_list = values.split(',') # [value,value]
                if isinstance(df[field].iloc[0], dict):
                    df = df[~df[field].apply(lambda x: x.get('value') in field_value_deselect_list)]
                else:
                    df = df[~df[field].isin(field_value_deselect_list)]
        if select:
            select_list = select.split(',') # [value,value]
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


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True


def kill_process_on_port(logger: logging.Logger, port: int) -> bool | str:
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                try:
                    process = psutil.Process(conn.pid)
                    if process.name().lower().startswith('python'):
                            logger.info(f'Killing Python process (PID: {conn.pid}) using port {port}')
                            process.terminate()
                            logger.info(f'Waiting briefly before starting Dash app...')
                            process.wait(timeout=5)
                            return True
                    else:
                        logger.warning(f'Process on port {port} (PID: {conn.pid}) is not a Python process. Not killing.')
                except psutil.NoSuchProcess:
                    logger.info(f'Process on port {port} no longer exists')
        return False
    except psutil.AccessDenied:
        logger.error(f'Access denied when trying to identify process on port: {port}.')
        logger.error('Try running the script with elevated privileges.')
        return 'error'
    except (PermissionError, OSError) as e:
        logger.error(f'Permission error when trying to kill process on port: {port}.')
        logger.error('Try running the script with elevated privileges.')
        return 'error'


def run_dash_app(logger: logging.Logger, app: Dash, port: int = 8000):
    try:
        if is_port_in_use(port):
            if kill_process_on_port(logger, port) != 'error':
                Console().print('[+] Starting Dash App ⚙', style='bold green')
                command_logger.info('[+] Starting Dash App ⚙')
                app.run(debug=False,port=port)
        else:
            Console().print('[+] Starting Dash App ⚙', style='bold green')
            command_logger.info('[+] Starting Dash App ⚙')
            app.run(debug=False,port=port)
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        print(f'An unexpected error occurred: {str(e)}')


azure_activity_log_axe.context_settings = dict(
    help_option_names=['-h', '--help'],
    max_content_width=110  # Adjust this width based on your needs
)
