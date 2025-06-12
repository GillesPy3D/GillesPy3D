# GillesPy3D Model Builder


## Deploying your own Single-User Instance
### Requirements

- [Nodejs](https://nodejs.org/)

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows and Mac) or [Docker Engine](https://docs.docker.com/install/) (Linux, Mac, and Windows)


### Quickstart

- Build and run the notebook server. This starts a local docker container running the model builder.    
  `make`

- Once your terminal calms down you'll see a link to your server that looks something like this: `127.0.0.1:8888/?token=X8dSfd...` Navigate to that link and get started.

- Your files are persisted on your local machine to the `local\_data/` directory by default.

### Setup

- Build the docker container.   
  `make build`

- Run the container.   
  `make run`

- Rebuild frontend static assets on changes to files in `/client` .  
  `make watch`

- Upon changing backend code in stochss/handlers you can update a running the notebook server.  
  `make update`

- [Optional] By default your files are saved to your local machine at `./local\_data/` . You can change this location by the changing value of `DOCKER\_WORKING\_DIR` in the file `.env` .

#### Add a python dependency

Use `requirements.txt` to add Python dependencies that will be installed into the docker container.

## Deploying Multi-User Model Builder

This uses [JupyterHub](https://jupyterhub.readthedocs.io/en/stable/#) as the basis for the multi-user deployment.  See their documentation for more details on configuring the JupyterHub environment.
  
### Setup

- In addition to the single-user requirements, you will need [Docker Compose](https://docs.docker.com/compose/install/).  

- [Optional] To set admins for JupyterHub, make a file called `userlist` in the `userlist/` directory. On each line of this file place a username followed by the word 'admin'. For example: `myuser admin`. If using Google OAuth, the username will be a Gmail address. Navigate to `/hub/admin` to use the JupyterHub admin interface.

- [Optional] By default multi-user Model Builder is set up to allocate 2 logical cpus per user, reserving 2 logical cpus for the hub container and underlying OS. You can define "power users" that are excluded from resource limitations using the same method as above for adding an admin, but instead of following the username with 'admin', use the keyword 'power' instead.

- [Optional] To disseminate messages to all users, make a JSON decodable file called `messages.json` in the `userlist/` directory. The contents of the `messages` file should be formatted as a list of dictionaries defining each message. Accepted keys are `message`, string containing the message to be display with tags for dates and time i.e. `The Server will be down for scheduled maintenance on __DATE__ from __START__ to __END__` an additional `__DATE__` tag can be added if the start and end dates differ, `start`, string representing the starting date and time i.e. `Sep 26, 2022  14:00 EST`, `end`, string representing the ending date and time i.e. `Sep 26, 2022  18:00 EST`, and `style`, a string containing a background color keyword i.e. `warning` or css i.e. `background-color: rgba(160, 32, 240, 0.5) !important;`.

```python
[
    {
        "message": The Server will be down for scheduled maintenance on __DATE__ from __START__ to __END__",
        "start": "Sep 26, 2022  14:00 EST",
        "end": "Sep 26, 2022  18:00 EST",
        "style": "info"
    },
    {
        "message": "The Server will be down for scheduled maintenance from"
    },
    {
        "message": "__DATE__ __START__ to __DATE__ __END__",
        "start": "Sep 26, 2022  14:00 EST",
        "end": "Sep 27, 2022  14:00 EST",
        "style": "warning"
    },
    {
        "message": "The Server is down for scheduled maintenance",
        "style": "background-color: rgba(160, 32, 240, 0.5) !important;"
    }
]
```

### Run Locally

To run JupyterHub locally run `make hub` and go to `http://127.0.0.1:8000/` .

### Set Up A Staging Server

To set up the staging environment you'll need to [set up Google OAuth](https://developers.google.com/identity/protocols/oauth2) for your instance.  Once you're set up, you'll need to put your OAuth credentials in `jupyterhub/secrets/.oauth.staging.env`. Do not wrap these environment variables in quotes!

Example oauth file:

```bash
OAUTH_CALLBACK=https://Your.URL/hub/oauth_callback
CLIENT_ID=8432438242-32432ada3ff23f248sf7ds.apps.googleusercontent.com
CLIENT_SECRET=XXXXXXXXXXXXXXXXXX
```

After your oauth credentials are setup, run these commands:

```bash
make build
make build_hub
make run_hub_staging
```

### Set Up A Production Server

Similar to staging, except you'll need the correct Google OAuth credentials set in `jupyterhub/secrets/.oauth.prod.env`.

Then:

```bash
make build
make build_hub
make run_hub_prod
```

