import pygsheets
import pandas as pd

SHEET_ID = '1bfVVtUM8FFe3bB4JDwnd0TsJ56G2RutqNk9rshx3Rf4'
SHEETS_TO_SYNC = [
    '2023',
    '2024'
]

def prepare_sheet_data(sheet_name):
    sheet = doc_handle.worksheet_by_title(sheet_name)
    sheet_df = sheet.get_as_df(start='D3',end='G')
    sheet_df.columns = sheet_df.iloc[1]
    sheet_df.columns.name = None
    sheet_df.rename(columns={'':'Datum'}, inplace=True)
    sheet_df.drop([0,1], inplace=True)
    sheet_df.reset_index(drop=True, inplace=True)
    sheet_df.Datum = pd.to_datetime(sheet_df.Datum, format='%d.%m.%Y')
    sheet_df.Stand = sheet_df.Stand.map(str).map(lambda content: content.strip())
    sheet_df['Interesting'] = sheet_df.Stand.map(lambda content: len(content)>0 and not content.isspace())
    return sheet_df

if __name__ == '__main__':
    client = pygsheets.authorize("client_secret_616621345489-h4bc2astbq7lbmdbda7eqa5cpmm64fv8.apps.googleusercontent.com.json")
    doc_handle = client.open_by_key(SHEET_ID)
    all_sheets = doc_handle.worksheets()
    print('Available Sheets: {}'.format(all_sheets))
    
    all_entries = pd.DataFrame()
    for sheet_name in SHEETS_TO_SYNC:
        sheet_df = prepare_sheet_data(sheet_name=sheet_name)
        # print(sheet_df.columns)
        # print(sheet_df)
        entries_for_calendar = sheet_df[sheet_df.Interesting]
        all_entries = pd.concat([all_entries, entries_for_calendar]) 

    all_entries.reset_index(drop=True, inplace=True)
    print(all_entries)