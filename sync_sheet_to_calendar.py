#!/usr/local/bin/python3
import pygsheets
import pandas as pd
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

CREDENTIALS_PATH = "client_secret_616621345489-h4bc2astbq7lbmdbda7eqa5cpmm64fv8.apps.googleusercontent.com.json"
SHEET_ID = '1bfVVtUM8FFe3bB4JDwnd0TsJ56G2RutqNk9rshx3Rf4'
SHEETS_TO_SYNC = [
    '2023',
    '2024'
]
CALENDAR_ID = '7aff4042ee7d9e05524e8ea9b5b7be55d1b6fee3090a7acc161160456da0d819@group.calendar.google.com'

def check_str_content(content):
    return len(content)>0 and not content.isspace()

def prepare_sheet_data(sheet):
    sheet_df = sheet.get_as_df(start='D3',end='G', include_tailing_empty=True)
    sheet_df.columns = sheet_df.iloc[1]
    sheet_df.columns.name = None
    sheet_df.rename(columns={'':'Datum'}, inplace=True)
    sheet_df.drop([0,1], inplace=True)
    sheet_df.reset_index(drop=True, inplace=True)
    sheet_df.Datum = pd.to_datetime(sheet_df.Datum, format='%d.%m.%Y').dt.date
    sheet_df[['Wo', 'Was', 'Stand']] = sheet_df[['Wo', 'Was', 'Stand']].applymap(str.strip)
    sheet_df['Interesting'] = sheet_df.Stand.map(check_str_content)
    return sheet_df

def pandas_to_google_event(event_pd):
    event_name = event_pd.Was
    if not check_str_content(event_name):
        event_name = event_pd.Wo

    color_id = None
    suffix = ''
    if 'fix' in event_pd.Stand.lower():
        color_id = '11'
    else:
        if 'option' in event_pd.Stand.lower():
            color_id = '5'
        if check_str_content(event_pd.Stand):
            suffix = ' ({})'.format(event_pd.Stand)

    return Event(
        'FS: {}{}'.format(event_name, suffix),
        start=event_pd.Datum,
        location=event_pd.Wo,
        description='Stand: {}'.format(event_pd.Stand),
        color_id=color_id
    )

if __name__ == '__main__':
    print('Reading events from sheets...')
    client = pygsheets.authorize(CREDENTIALS_PATH, local=True)
    doc_handle = client.open_by_key(SHEET_ID)
    # all_sheets = doc_handle.worksheets()
    # print('Available Sheets: {}'.format(all_sheets))
    
    all_entries = pd.DataFrame()
    for sheet_name in SHEETS_TO_SYNC:
        sheet = doc_handle.worksheet_by_title(sheet_name)
        sheet_df = prepare_sheet_data(sheet=sheet)
        # print(sheet_df.columns)
        # print(sheet_df)
        entries_for_calendar = sheet_df[sheet_df.Interesting]
        all_entries = pd.concat([all_entries, entries_for_calendar]) 

    all_entries.reset_index(drop=True, inplace=True)
    # print(all_entries)

    print('Syncing events to calendar...')
    gc = GoogleCalendar(CALENDAR_ID, credentials_path=CREDENTIALS_PATH)
    gc.clear_calendar()

    # Create all events from sheets
    for idx, event_pd in all_entries.iterrows():
        # Clear old event in case it still exists
        events = gc[event_pd.Datum:event_pd.Datum]
        for event in events:
            # print('Clearing {} ...'.format(event))
            gc.delete_event(event)

        # Add new event
        event = pandas_to_google_event(event_pd=event_pd)
        gc.add_event(event)
        # For testing only sync the first entry:
        # break


    print('Events in the next year:')
    for event in gc:
        print(event)

    print('Calendar Sync finished!')
