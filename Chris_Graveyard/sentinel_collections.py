from sentinelhub import SentinelHubCatalog, SHConfig

# Configure Sentinel Hub with your instance ID, client ID, and client secret
config = SHConfig()
config.instance_id = "44b8b66c-925c-4ab5-a776-b1f48364172d"  # Replace with your instance ID
config.sh_client_id = 'b15c8cd5-e24c-4eb4-894f-4ad544e6a59f'
config.sh_client_secret = 'WRewj3YLfo0jb81YSA9duxrupDvxn2EX'

def print_available_collections():
    catalog = SentinelHubCatalog(config=config)  # Pass the configuration object
    collections = catalog.get_collections()
    if collections:
        print("Available data collections from Sentinel Hub:")
        for collection in collections:
            print(collection)
    else:
        print("No data collections available. Please check your configuration or contact support.")

print_available_collections()
