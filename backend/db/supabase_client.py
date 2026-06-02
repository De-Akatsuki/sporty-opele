import os
import json
import socket
import urllib.parse
from dotenv import load_dotenv

# Try importing supabase
try:
    from supabase import create_client, Client
except ImportError:
    Client = None

load_dotenv()

# We look for environment variables in the parent directory as well
if not os.getenv("SUPABASE_URL"):
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if we should use mock database
is_mock = False
if not SUPABASE_URL or not SUPABASE_KEY or "your_supabase" in SUPABASE_URL or "your_supabase" in SUPABASE_KEY:
    is_mock = True

class MockTable:
    def __init__(self, table_name):
        self.table_name = table_name
        self.db_dir = os.path.join(os.path.dirname(__file__), "local_db")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_file = os.path.join(self.db_dir, f"{table_name}.json")
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w") as f:
                json.dump([], f)
        self.temp_data = []

    def _read(self):
        try:
            with open(self.db_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, data):
        try:
            with open(self.db_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing mock DB file: {e}")

    def select(self, fields="*"):
        self.temp_data = self._read()
        return self

    def eq(self, field, value):
        self.temp_data = [row for row in self.temp_data if row.get(field) == value or str(row.get(field)) == str(value)]
        return self

    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data
        return Result(self.temp_data)

    def upsert(self, row_data, on_conflict=None):
        data = self._read()
        rows_to_process = row_data if isinstance(row_data, list) else [row_data]
        
        for new_row in rows_to_process:
            updated = False
            if on_conflict:
                for idx, existing in enumerate(data):
                    if existing.get(on_conflict) == new_row.get(on_conflict):
                        data[idx].update(new_row)
                        updated = True
                        break
            if not updated:
                if "id" not in new_row:
                    new_row["id"] = len(data) + 1
                data.append(new_row)
        
        self._write(data)
        self.temp_data = rows_to_process
        return self

    def insert(self, row_data):
        data = self._read()
        rows_to_process = row_data if isinstance(row_data, list) else [row_data]
        for r in rows_to_process:
            if "id" not in r:
                r["id"] = len(data) + 1
            data.append(r)
        self._write(data)
        self.temp_data = rows_to_process
        return self

    def delete(self):
        # Clears all rows in the temp filter
        # For simplicity, if we filtered by fixture_id, delete those.
        # If no filters, delete everything.
        all_data = self._read()
        if not self.temp_data:
            # Delete everything
            self._write([])
        else:
            # Delete matching
            temp_ids = [item.get("id") for item in self.temp_data if "id" in item]
            remaining = [item for item in all_data if item.get("id") not in temp_ids]
            self._write(remaining)
        self.temp_data = []
        return self

    def update(self, update_data):
        data = self._read()
        filtered_ids = [item.get("id") for item in self.temp_data if "id" in item]
        filtered_names = [item.get("team_name") for item in self.temp_data if "team_name" in item]
        
        updated_rows = []
        for idx, item in enumerate(data):
            match = False
            if "id" in item and item["id"] in filtered_ids:
                match = True
            elif "team_name" in item and item["team_name"] in filtered_names:
                match = True
            
            if match:
                data[idx].update(update_data)
                updated_rows.append(data[idx])
        
        self._write(data)
        self.temp_data = updated_rows
        return self

class MockClient:
    def table(self, name):
        return MockTable(name)

# Initialize client
if is_mock:
    print("⚠️ Supabase credentials not configured. Using local JSON mock database at backend/db/local_db/")
    supabase = MockClient()
else:
    try:
        # Test if we can resolve the hostname
        parsed_url = urllib.parse.urlparse(SUPABASE_URL)
        host = parsed_url.netloc
        if ":" in host:
            host = host.split(":")[0]
        # Resolve hostname
        socket.gethostbyname(host)
        
        if Client:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✓ Connected to Supabase Production database.")
        else:
            print("⚠️ Supabase python package not available. Falling back to local JSON mock database.")
            supabase = MockClient()
            is_mock = True
    except Exception as e:
        print(f"⚠️ Supabase connection test failed ({e}). Falling back to local JSON mock database at backend/db/local_db/")
        supabase = MockClient()
        is_mock = True

# Helper functions
def upsert_team(team_data: dict):
    """Insert or update a team record."""
    return supabase.table("wc_teams").upsert(team_data, on_conflict="team_name").execute()

def insert_prediction(prediction_data: dict):
    """Insert a new prediction."""
    return supabase.table("predictions").insert(prediction_data).execute()

def get_fixtures_for_date(date: str):
    """Get all fixtures for a given date (YYYY-MM-DD)."""
    return supabase.table("wc_fixtures").select("*").eq("match_date", date).execute()

def log_outcome(outcome_data: dict):
    """Log actual match outcome vs prediction."""
    return supabase.table("prediction_outcomes").insert(outcome_data).execute()


def upsert_processed_features(row: dict):
    """Insert or update processed feature row for a fixture."""
    return supabase.table("processed_features").upsert(row, on_conflict="fixture_id").execute()
