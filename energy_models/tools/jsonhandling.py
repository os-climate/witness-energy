import json
import numpy as np
import pandas as pd
def preprocess_json(data):
    """
    Replaces all occurrences of . in the keys of a dictionary with #.
    Recursively processes nested dictionaries and lists.

    Args:
        data (dict or list): The JSON data to be processed.

    Returns:
        dict or list: The processed JSON data.
    """
    if isinstance(data, dict):
        processed_data = {}
        for key, value in data.items():
            processed_key = key.replace('.', '#')
            if isinstance(value, dict):
                processed_value = preprocess_json(value)
            elif isinstance(value, list):
                processed_value = [preprocess_json(item) for item in value]
            else:
                processed_value = value
            processed_data[processed_key] = processed_value
        return processed_data
    elif isinstance(data, list):
        return [preprocess_json(item) for item in data]
    else:
        return data

def preprocess_data_and_save_json(data, output_file_path):
    processed_data = preprocess_json(data)
    with open(output_file_path, 'w') as output_file:
        json.dump(processed_data, output_file, indent=4)

def preprocess_and_save_json(input_file_path, output_file_path):
    """
    Reads a JSON file, preprocesses it by replacing all occurrences of . in the keys with #,
    and writes the result to another file.

    Args:
        input_file_path (str): The path to the input JSON file.
        output_file_path (str): The path to the output JSON file.
    """
    with open(input_file_path, 'r') as input_file:
        data = json.load(input_file)
        processed_data = preprocess_json(data)
    with open(output_file_path, 'w') as output_file:
        json.dump(processed_data, output_file, indent=4)

def postprocess_json(data):
    """
    Replaces all occurrences of # in the keys of a dictionary with .

    Args:
        data (dict): The dictionary to be processed.

    Returns:
        dict: The processed dictionary.
    """
    processed_data = {}
    for key, value in data.items():
        processed_key = key.replace('#', '.')
        if isinstance(value, dict):
            processed_value = postprocess_json(value)
        elif isinstance(value, list):
            processed_value = [postprocess_json(item) for item in value]
        else:
            processed_value = value
        processed_data[processed_key] = processed_value
    return processed_data


def convert_to_editable_json(data):
    def convert(obj):

        if isinstance(obj, pd.DataFrame):
            df = obj.apply(lambda x: x.astype(int) if x.dtype == np.int32 else x)
            df = df.where(pd.notnull(df), None)
            return [{col: df[col].values.tolist()} for col in df.columns]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(elem) for elem in obj]
        elif isinstance(obj, float):
            return obj  # Round to 2 decimal places
        elif isinstance(obj, np.int32):
            return int(obj)
        else:
            return obj
    
    data = convert(data)
    return json.dumps(data, ensure_ascii=False)


def get_document_from_cosmosdb_pymongo(connection_string: str, database_name: str, collection_name: str, query: dict):
    """
    Connects to a MongoDB database using a connection string, and retrieves a single document from a collection
    using a query.

    :param connection_string: a MongoDB connection string
    :param database_name: the name of the database
    :param collection_name: the name of the collection
    :param query: a dictionary representing the query to use to find the document
    :return: a dictionary representing the retrieved document, or None if no document is found
    """

    # Create a MongoClient object using the connection string
    client = MongoClient(connection_string)

    # Access the specified database and collection
    db = client[database_name]
    collection = db[collection_name]

    # Use the find_one method to retrieve a single document matching the query
    document = collection.find_one(query)

    # Close the client connection
    client.close()

    # Return the retrieved document, or None if no document is found
    return document


import json
from pymongo import MongoClient

def insert_json_to_mongodb_bis(json_path, collection_name, database_name, connection_string):
    # Read the JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Connect to the database
    client = MongoClient(connection_string)
    db = client[database_name]
    # Insert the data into the specified collection
    collection = db[collection_name]
    result = collection.insert_one(data)

    # Print the ID of the inserted document
    print('Document inserted with ID:', result.inserted_id)

    # Close the MongoDB connection
    client.close()



if __name__ == '__main__': 
    from os.path import join, dirname

    # delete . in json file, replace by # (not handled by mongodb)
    """    
    in_json = join(dirname(dirname(__file__)), 'sos_processes', 'regionalization_data', 'data_nuclear_test.json')
    out_json = join(dirname(__file__), 'data_nuclear_test_updated.json')
    preprocess_and_save_json(in_json , out_json)
    """
    connection_string = ""
    database_name = 'regionalization'
    container_name = 'regionalizationv0'
    json_file_path = join(dirname(__file__), 'data_nuclear_test_updated.json')

    insert_json_to_mongodb_bis(json_file_path, container_name, database_name, connection_string)