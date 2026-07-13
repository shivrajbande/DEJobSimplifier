"""
IMDB Dataset — Excel → MySQL Loader
====================================
Reads IMDB_Dataset.xlsx and loads all 12 sheets into your local MySQL database.
Run:  python imdb_excel_to_mysql.py
Deps: pip install mysql-connector-python openpyxl
"""

import openpyxl
import mysql.connector
from datetime import datetime, date

# ─────────────────────────────────────────────
# CONFIG — update these to match your setup
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Shiva@2001",
}
DB_NAME    = "imdb_demo"
EXCEL_FILE = "IMDB_Dataset.xlsx"   # path to your Excel file


# ─────────────────────────────────────────────
# DDL — one CREATE TABLE per sheet
# ─────────────────────────────────────────────
DDL = {

"movies": """
CREATE TABLE IF NOT EXISTS movies (
    Movie_ID             INT PRIMARY KEY,
    Title                VARCHAR(200),
    Primary_Genre        VARCHAR(50),
    Secondary_Genre      VARCHAR(50),
    Release_Year         INT,
    Runtime_Min          INT,
    IMDb_Rating          FLOAT,
    Vote_Count           INT,
    Budget_USD           BIGINT,
    Box_Office_USD       BIGINT,
    Language             VARCHAR(50),
    Content_Rating       VARCHAR(10),
    Production_Studio    VARCHAR(100),
    Country              VARCHAR(50),
    Status               VARCHAR(50)
)""",

"persons": """
CREATE TABLE IF NOT EXISTS persons (
    Person_ID       INT PRIMARY KEY,
    First_Name      VARCHAR(100),
    Last_Name       VARCHAR(100),
    Primary_Role    VARCHAR(50),
    Date_of_Birth   DATE,
    Nationality     VARCHAR(50),
    Gender          VARCHAR(20),
    Avg_Rating      FLOAT,
    Total_Credits   INT,
    Awards_Won      INT,
    Career_Status   VARCHAR(20),
    Net_Worth_USD_M FLOAT
)""",

"cast_details": """
CREATE TABLE IF NOT EXISTS cast_details (
    Cast_ID          INT PRIMARY KEY,
    Movie_ID         INT,
    Person_ID        INT,
    Character_Name   VARCHAR(100),
    Character_Type   VARCHAR(50),
    Billing_Position INT,
    Screen_Time_Min  INT,
    Lines_Count      INT,
    Salary_USD_M     FLOAT,
    Stunt_Double     VARCHAR(5),
    Fan_Rating       FLOAT,
    Award_Nomination VARCHAR(50),
    FOREIGN KEY (Movie_ID)  REFERENCES movies(Movie_ID),
    FOREIGN KEY (Person_ID) REFERENCES persons(Person_ID)
)""",

"directors": """
CREATE TABLE IF NOT EXISTS directors (
    Director_ID          INT PRIMARY KEY,
    Movie_ID             INT,
    Person_ID            INT,
    Directing_Style      VARCHAR(50),
    Fee_USD_M            FLOAT,
    Shooting_Weeks       INT,
    Avg_Movie_Rating     FLOAT,
    Oscar_Wins           INT,
    DGA_Member           VARCHAR(5),
    First_Feature_Year   INT,
    Total_Films_Directed INT,
    FOREIGN KEY (Movie_ID)  REFERENCES movies(Movie_ID),
    FOREIGN KEY (Person_ID) REFERENCES persons(Person_ID)
)""",

"reviews": """
CREATE TABLE IF NOT EXISTS reviews (
    Review_ID           INT PRIMARY KEY,
    Movie_ID            INT,
    User_ID             INT,
    Rating              FLOAT,
    Sentiment           VARCHAR(20),
    Platform            VARCHAR(50),
    Helpful_Votes       INT,
    Comment_Count       INT,
    Reviewer_Type       VARCHAR(30),
    Review_Date         DATE,
    Contains_Spoiler    VARCHAR(5),
    Review_Length_Words INT,
    FOREIGN KEY (Movie_ID) REFERENCES movies(Movie_ID)
)""",

"awards": """
CREATE TABLE IF NOT EXISTS awards (
    Award_ID         INT PRIMARY KEY,
    Movie_ID         INT,
    Person_ID        INT,
    Award_Name       VARCHAR(100),
    Category         VARCHAR(100),
    Year             INT,
    Result           VARCHAR(20),
    Award_Type       VARCHAR(30),
    Ceremony_Number  INT,
    Prestige_Score   FLOAT,
    FOREIGN KEY (Movie_ID)  REFERENCES movies(Movie_ID),
    FOREIGN KEY (Person_ID) REFERENCES persons(Person_ID)
)""",

"box_office": """
CREATE TABLE IF NOT EXISTS box_office (
    BoxOffice_ID             INT PRIMARY KEY,
    Movie_ID                 INT,
    Production_Budget_USD    BIGINT,
    Domestic_Gross_USD       BIGINT,
    International_Gross_USD  BIGINT,
    Worldwide_Gross_USD      BIGINT,
    Theater_Count            INT,
    Weeks_in_Theater         INT,
    ROI_Ratio                FLOAT,
    Top_Revenue_Region       VARCHAR(50),
    Opening_Weekend_Rank     INT,
    Marketing_Spend_USD_M    FLOAT,
    FOREIGN KEY (Movie_ID) REFERENCES movies(Movie_ID)
)""",

"genre_stats": """
CREATE TABLE IF NOT EXISTS genre_stats (
    Genre_ID                INT PRIMARY KEY,
    Genre_Name              VARCHAR(50),
    Total_Movies            INT,
    Avg_IMDb_Rating         FLOAT,
    Avg_Budget_USD_M        FLOAT,
    Avg_Runtime_Min         FLOAT,
    Year_Established        INT,
    Total_Global_Revenue_USD BIGINT,
    Audience_Score          FLOAT,
    Market_Trend            VARCHAR(20)
)""",

"streaming": """
CREATE TABLE IF NOT EXISTS streaming (
    Stream_ID           INT PRIMARY KEY,
    Movie_ID            INT,
    Platform            VARCHAR(50),
    Available_Since     DATE,
    Total_Views         BIGINT,
    Licensing_Fee_USD_M FLOAT,
    Days_Trending       INT,
    License_Status      VARCHAR(20),
    Is_Exclusive        VARCHAR(5),
    Watchlist_Adds      INT,
    Platform_Rating     FLOAT,
    Distribution_Scope  VARCHAR(30),
    FOREIGN KEY (Movie_ID) REFERENCES movies(Movie_ID)
)""",

"production": """
CREATE TABLE IF NOT EXISTS production (
    Prod_ID               INT PRIMARY KEY,
    Movie_ID              INT,
    Shooting_Start        DATE,
    Shooting_End          DATE,
    Total_Shoot_Days      INT,
    Filming_Type          VARCHAR(30),
    Primary_Location      VARCHAR(50),
    Crew_Size             INT,
    Post_Prod_Budget_USD_M FLOAT,
    VFX_Budget_USD_M      FLOAT,
    VFX_Level             VARCHAR(20),
    CGI_Heavy             VARCHAR(5),
    Release_Format        VARCHAR(20),
    FOREIGN KEY (Movie_ID) REFERENCES movies(Movie_ID)
)""",

"users": """
CREATE TABLE IF NOT EXISTS users (
    User_ID         INT PRIMARY KEY,
    Username        VARCHAR(50),
    Email           VARCHAR(100),
    Nationality     VARCHAR(50),
    Age             INT,
    Gender          VARCHAR(20),
    Subscription    VARCHAR(20),
    Join_Date       DATE,
    Movies_Watched  INT,
    Movies_Reviewed INT,
    Fav_Genre       VARCHAR(50),
    Avg_Rating_Given FLOAT
)""",

"soundtracks": """
CREATE TABLE IF NOT EXISTS soundtracks (
    Soundtrack_ID    INT PRIMARY KEY,
    Movie_ID         INT,
    Composer         VARCHAR(100),
    Music_Genre      VARCHAR(50),
    Track_Count      INT,
    Total_Duration_Min FLOAT,
    Budget_USD_M     FLOAT,
    Award_Nominations INT,
    Oscar_Nominated  VARCHAR(5),
    Spotify_Streams  BIGINT,
    Critic_Score     FLOAT,
    Release_Format   VARCHAR(30),
    FOREIGN KEY (Movie_ID) REFERENCES movies(Movie_ID)
)""",

}

# Map Excel sheet names → MySQL table names
SHEET_TO_TABLE = {
    "Movies":       "movies",
    "Persons":      "persons",
    "Cast":         "cast_details",
    "Directors":    "directors",
    "Reviews":      "reviews",
    "Awards":       "awards",
    "Box_Office":   "box_office",
    "Genre_Stats":  "genre_stats",
    "Streaming":    "streaming",
    "Production":   "production",
    "Users":        "users",
    "Soundtracks":  "soundtracks",
}

# Load order matters because of FK constraints
LOAD_ORDER = [
    "Movies", "Persons", "Cast", "Directors",
    "Reviews", "Awards", "Box_Office", "Genre_Stats",
    "Streaming", "Production", "Users", "Soundtracks",
]

# Columns that should be stored as DATE
DATE_COLUMNS = {
    "Date_of_Birth", "Review_Date", "Available_Since",
    "Shooting_Start", "Shooting_End", "Join_Date",
}


def parse_value(col_name, val):
    """Clean up a cell value before inserting."""
    if val is None or val == "":
        return None

    # datetime objects from openpyxl → date
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val

    # String date columns
    if col_name in DATE_COLUMNS and isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
        return None  # unparseable date → NULL

    return val


def build_insert(table: str, columns: list) -> str:
    placeholders = ", ".join(["%s"] * len(columns))
    cols = ", ".join(columns)
    return f"INSERT IGNORE INTO {table} ({cols}) VALUES ({placeholders})"


def main():
    # ── Step 1: Connect and create database ──────────────────────────
    print("🔌 Connecting to MySQL...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    cur.execute(f"USE `{DB_NAME}`")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")  # disable during setup
    print(f"✅ Database `{DB_NAME}` ready\n")

    # ── Step 2: Create all tables ─────────────────────────────────────
    print("📐 Creating tables...")
    for table_name, ddl in DDL.items():
        cur.execute(ddl)
        print(f"   ✔ {table_name}")
    conn.commit()
    print()

    # ── Step 3: Load Excel ────────────────────────────────────────────
    print(f"📂 Opening {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE, read_only=True, data_only=True)

    for sheet_name in LOAD_ORDER:
        if sheet_name not in wb.sheetnames:
            print(f"⚠️  Sheet '{sheet_name}' not found, skipping.")
            continue

        table = SHEET_TO_TABLE[sheet_name]
        ws = wb[sheet_name]

        rows = list(ws.iter_rows(values_only=True))

        # Row 0 = title banner (merged cell), Row 1 = actual headers
        headers = [str(h) for h in rows[1] if h is not None]
        data_rows = rows[2:]  # actual data starts at row index 2

        insert_sql = build_insert(table, headers)
        inserted = 0
        errors = 0

        for row in data_rows:
            if all(v is None for v in row):
                continue  # skip blank rows
            values = [parse_value(headers[i], row[i]) for i in range(len(headers))]
            try:
                cur.execute(insert_sql, values)
                inserted += 1
            except mysql.connector.Error as e:
                errors += 1
                if errors <= 3:  # only print first 3 errors per table
                    print(f"     ⚠️  Row error in {sheet_name}: {e}")

        conn.commit()
        status = f"✅ {sheet_name:15s} → {table:20s} | {inserted} rows inserted"
        if errors:
            status += f"  ({errors} skipped)"
        print(status)

    # ── Step 4: Re-enable FK checks ───────────────────────────────────
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    # ── Step 5: Quick row count verification ─────────────────────────
    print("\n📊 Row counts in MySQL:")
    for table in DDL.keys():
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cur.fetchone()[0]
        print(f"   {table:25s}: {count} rows")

    cur.close()
    conn.close()
    print("\n🎬 All done! IMDB data is now in MySQL and ready for embeddings.")


if __name__ == "__main__":
    main()