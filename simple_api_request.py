import requests

def fetch_random_joke():
    """
    Fetches a random joke from the Official Joke API.

    Returns:
        dict: A dictionary containing the joke data if successful.
        None: If the request fails.
    """
    url = "https://official-joke-api.appspot.com/random_joke"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def main():
    joke = fetch_random_joke()
    if joke:
        print("Here's a random joke:")
        print(f"{joke['setup']}\n{joke['punchline']}")
    else:
        print("Failed to fetch a joke.")

if __name__ == "__main__":
    main()
