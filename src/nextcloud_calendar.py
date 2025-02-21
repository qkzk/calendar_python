import caldav

BASE_URL = "http://qkzk.ddns.net:81/remote.php/dav/"
USERNAME = "qkzk"
APP_PASSWORD_PATH = "/home/quentin/gclem/dev/python/boulot_utils/calpy_branches/tokens/quentin/nextcloud"


def read_app_password():
    with open(APP_PASSWORD_PATH) as f:
        return f.read().strip()


def create_nextcloud_client(app_password) -> caldav.DAVClient:
    return caldav.DAVClient(url=BASE_URL, username=USERNAME, password=app_password)


def get_calendars(client: caldav.DAVClient) -> list[caldav.Calendar]:
    principal = client.principal()
    calendars = principal.calendars()
    return calendars


def display_event(calendar: caldav.Calendar) -> None:
    events = calendar.events()
    for event in events:
        print(event.data)
        caldav.Event


def example() -> None:
    app_password = read_app_password()
    print(app_password)
    client = create_nextcloud_client(app_password)
    calendars = get_calendars(client)
    for calendar in calendars:
        print(f"calendar {calendar.name}")
        display_event(calendar)


if __name__ == "__main__":
    example()
