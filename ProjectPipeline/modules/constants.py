URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
    # Latency is the time it takes for a request to travel from client → server → client.
    # High latency makes the user wait longer
URL_MONITOR_SIZE = "ResponseSize"
    # Response size is the amount of data the server sends back to the client.
    # if the response size is too large it can slow down the website when loading for the client.
URL_MONITOR_MEMORY = "Memory"
    # Memory helps monitor website health by showing how much RAM your website and servers are using. 
    # The less RAM the memory is low, meaning it can handle more requests the website at once. 
    # The more RAM the memory is too high, meaning the website may become slow or unresponsive.
URL_NAMESPACE = "EUGENEPROJECT_WSU2025"

MONITORED_URLS = [
    "https://www.youtube.com",
    "https://www.google.com",
    "https://www.instagram.com",
]