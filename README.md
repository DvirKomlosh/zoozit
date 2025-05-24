# Zoozit

Zoozit is a project designed to give more accurate time estimations for bus rides in Israel.

it uses the [open bus stride client](https://github.com/hasadna/open-bus-stride-client) to get past data,
and the MOT's api to get live data.

### how to run the proejct:

to use the open bus stride client, install the library:

```bash
pip install --upgrade open-bus-stride-client
```

you'll need an internet connection to use the API.

## for developers:

to use open-bus-stride-client well you might need to use some resources:
read the [API docs](https://open-bus-stride-api.hasadna.org.il/docs#) to learn what API calls are available
use the [data model](https://github.com/hasadna/open-bus-stride-db/blob/main/DATA_MODEL.md) to learn what each data type includes, and how to get from one data type to another.


