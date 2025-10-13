# WSU_DevOps_2025
This project spins up a lambda fucntion that fires every minute, collecting differenct metrics on websites. These metrics are: 
- Availability (If the site is returning 200 as a response)
- Latency (How long the request takes to receive a response)
- Response size (Showing how big of a response is being returned, in gigabytes)

These metrics have alarms associated with them that will send an alert once their requirements have been met. These alarms will cause AWS sns to send notification about which alarms have been triggered, and also trigger other lambda funciton that will send the alarm information into a nosql database in a log format.

-insert achitect diagram-

## Setup
Before being able to clone and start running this repo, some requirements must be met.
1. Python and Node must be installed 
2. The aws cli must be installed from [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. Running aws configure and inputting the required information
4. Run the following commands to clone the repo
```sh
npm install -g aws-cdk 
git clone https://github.com/Prinpa/WSU_DevOps_2025.git
cd PatDowd
source .venv/bin/activate
python -m pip install -r requirements.txt
```
## Deploying
Now that the project has been installed, its ready to run. THis can be done by using `cdk synth` then `cdk deploy`

And once you're done, use `cdk destroy` to stop every

## API documentation

The API provides endpoints to manage URLs in the database. The following endpoints are available:

### GET /urls

Fetches all stored URLs.

**Request:**
```
GET /urls
```

**Response:**
- 200 OK: Returns a JSON array of URLs.

---

### POST /urls

Adds a new URL to the database.

**Request:**
```
POST /urls
Content-Type: application/json
```
**Body Example:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
- 201 Created: Returns a message confirming the URL was added.

---

### DELETE /urls/{url}

Removes a URL from the database.

**Request:**
```
DELETE /urls/{url}
```

**Response:**
- 200 OK: Returns a message confirming the URL was deleted.

---
