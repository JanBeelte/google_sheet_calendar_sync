#!/usr/local/bin/python3
import warnings
from datetime import datetime

import pandas as pd
import pygsheets
from apscheduler import Scheduler
from apscheduler.triggers.cron import CronTrigger
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account

warnings.filterwarnings("ignore", category=UserWarning)

SERVICE_ACCOUNT_FILE = "credentials/fs-calendar-408013-bbc8c645727f.json"
SHEET_ID = "1bfVVtUM8FFe3bB4JDwnd0TsJ56G2RutqNk9rshx3Rf4"
SHEETS_TO_SYNC = ["2025", "2026"]
CALENDAR_ID = "7aff4042ee7d9e05524e8ea9b5b7be55d1b6fee3090a7acc161160456da0d819@group.calendar.google.com"
CLEAR_CALENDAR = True


def check_str_content(content):
    return len(content) > 0 and not content.isspace()


def prepare_sheet_data(sheet):
    sheet_df = sheet.get_as_df(start="D3", end="G", include_tailing_empty=True)
    sheet_df.columns = sheet_df.iloc[1]
    sheet_df.columns.name = None
    sheet_df.rename(columns={"": "Datum"}, inplace=True)
    sheet_df.drop([0, 1], inplace=True)
    sheet_df.reset_index(drop=True, inplace=True)
    sheet_df.Datum = pd.to_datetime(sheet_df.Datum, format="%d.%m.%Y").dt.date
    sheet_df[["Wo", "Was", "Stand"]] = sheet_df[["Wo", "Was", "Stand"]].map(str.strip)
    sheet_df["Interesting"] = sheet_df.Stand.map(check_str_content)
    return sheet_df


def pandas_to_google_event(event_pd):
    event_name = event_pd.Was
    if not check_str_content(event_name):
        event_name = event_pd.Wo

    color_id = None
    suffix = ""
    if "fix" in event_pd.Stand.lower():
        color_id = "11"
    else:
        if "option" in event_pd.Stand.lower():
            color_id = "5"
        if check_str_content(event_pd.Stand):
            suffix = " ({})".format(event_pd.Stand)

    return Event(
        "FS: {}{}".format(event_name, suffix),
        start=event_pd.Datum,
        location=event_pd.Wo,
        description="Stand: {}".format(event_pd.Stand),
        color_id=color_id,
    )


def read_master_sheet():
    client = pygsheets.authorize(
        service_account_file=SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        local=True,
    )
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
    return all_entries


def write_to_calendar(gc, all_entries):
    # Create all events from sheets
    for idx, event_pd in all_entries.iterrows():
        # Clear old event in case it still exists
        if not CLEAR_CALENDAR:
            events = gc[event_pd.Datum : event_pd.Datum]
            for event in events:
                # print('Clearing {} ...'.format(event))
                gc.delete_event(event)

        # Add new event
        event = pandas_to_google_event(event_pd=event_pd)
        gc.add_event(event)
        # For testing only sync the first entry:
        # break
    return gc


def clear_calendar(gc: GoogleCalendar):
    events = gc.get_events(
        time_min=datetime(year=int(SHEETS_TO_SYNC[0]), month=1, day=1),
        time_max=datetime(year=int(SHEETS_TO_SYNC[-1]), month=12, day=31),
    )
    for event in events:
        gc.delete_event(event)


def sync():
    print("Reading events from sheet...")
    all_entries = read_master_sheet()
    print("Events in Master-Sheet:")
    with pd.option_context("display.max_rows", None):
        print(all_entries)

    calendar_credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    gc = GoogleCalendar(CALENDAR_ID, credentials=calendar_credentials)
    if CLEAR_CALENDAR:
        # This only works on primary calendars
        # gc.clear_calendar()
        print("Clearing calendar...")
        clear_calendar(gc)

    print("Syncing events to calendar...")
    write_to_calendar(gc, all_entries)

    print("Events in the next year:")
    for event in gc:
        print(event)

    print("Calendar Sync finished!")


def main():
    sync()
    print("Starting scheduler...")

    with Scheduler() as scheduler:
        scheduler.add_schedule(
            sync,
            CronTrigger(hour=23, minute=50),
        )
        try:
            scheduler.run_until_stopped()
        except KeyboardInterrupt:
            scheduler.stop()


if __name__ == "__main__":
    main()
