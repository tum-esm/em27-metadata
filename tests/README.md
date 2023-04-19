# Integrity tests of the JSON files

These tests are set up to run on every push to the repository.

## Conducted tests

**`locations.json`:**

-   JSON format is valid
-   Values for `lat`/`lng`/`alt` are in a reasonable range

**`sensors.py`:**

-   JSON format is valid
-   All dates exist
-   Time periods are ordered ascendingly
-   no overlapping time periods
-   no gaps between time periods
-   last time periods ends with null
-   no two adjacent time periods with the same location
-   all locations exist in `location-coordinates`

**`campaigns.json`:**

-   JSON format is valid
-   All dates exist
-   start date before end date
-   no duplicate sensors/locations/directions
-   directions make sense (lat of north > lat of south)
-   locations in `location-coordinates`
-   sensors in `sensor-locations`
