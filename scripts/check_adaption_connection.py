"""Verify that the local project can authenticate with the Adaption API."""

from __future__ import annotations

import os
import sys

import adaption
from adaption import Adaption
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    api_key = os.getenv("ADAPTION_API_KEY")

    if not api_key:
        print(
            "ADAPTION_API_KEY was not found.\n"
            "Create a .env file containing:\n"
            "ADAPTION_API_KEY=pt_live_..."
        )
        return 1

    try:
        client = Adaption(api_key=api_key)

        # This makes an authenticated request without uploading data
        # or starting a credit-consuming adaptation run.
        datasets = list(client.datasets.list(limit=1))

        print("Successfully authenticated with Adaption.")
        print(f"Adaption SDK version: {adaption.__version__}")

        if datasets:
            dataset = datasets[0]
            dataset_id = getattr(dataset, "dataset_id", "unknown")
            status = getattr(dataset, "status", "unknown")
            print(f"Most recent dataset: {dataset_id} ({status})")
        else:
            print("No existing datasets were found, which is fine.")

        client.close()
        return 0

    except adaption.AuthenticationError:
        print("Authentication failed. Check the API key in your .env file.")
        return 1

    except adaption.APIConnectionError as error:
        print("Could not connect to the Adaption API.")
        print(f"Underlying error: {error.__cause__}")
        return 1

    except adaption.APIStatusError as error:
        print(f"Adaption returned HTTP status {error.status_code}.")
        print(error.response)
        return 1

    except adaption.APIError as error:
        print(f"Unexpected Adaption API error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())