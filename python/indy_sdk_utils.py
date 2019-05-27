""" Wrappers around Indy-SDK functions to overcome shortcomings in the SDK.
"""
import json
from indy import did, non_secrets, error


async def create_and_store_my_did(wallet_handle):
    """ Create and store my DID, adding a map from verkey to DID using the
        non_secrets API.
    """
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    await non_secrets.add_wallet_record(
        wallet_handle,
        'key-to-did',
        my_vk,
        my_did,
        '{}'
    )

    return my_did, my_vk


async def store_their_did(wallet_handle, their_did, their_vk):
    """ Store their did, adding a map from verkey to DID using the non_secrets
        API.
    """
    await did.store_their_did(
        wallet_handle,
        json.dumps({
            'did': their_did,
            'verkey': their_vk,
        })
    )

    await non_secrets.add_wallet_record(
        wallet_handle,
        'key-to-did',
        their_vk,
        their_did,
        '{}'
    )


async def did_for_key(wallet_handle, key):
    """ Retrieve DID for a given key from the non_secrets verkey to DID map.
    """
    _did = None
    try:
        _did = json.loads(
            await non_secrets.get_wallet_record(
                wallet_handle,
                'key-to-did',
                key,
                '{}'
            )
        )['value']
    except error.IndyError as e:
        if e.error_code is error.ErrorCode.WalletItemNotFound:
            pass
        else:
            raise e

    return _did


async def get_wallet_records(wallet_handle: int, search_type: str,
                             query_json: str = json.dumps({})) -> list:
    """ Search for records of a given type in a wallet.

    :param wallet_handle: Handle of the wallet to search.
    :param search_type: Type of records to search.
    :param query_json: MongoDB style query to wallet record tags.
           See non_secrets.open_wallet_search.
    :return: List of all records found.
    """
    list_of_records = []
    search_handle = await non_secrets.open_wallet_search(wallet_handle,
                                                         search_type,
                                                         query_json,
                                                         json.dumps({'retrieveTotalCount': True}))
    while True:
        results_json = await non_secrets.fetch_wallet_search_next_records(wallet_handle,
                                                                          search_handle, 10)
        results = json.loads(results_json)

        if results['totalCount'] == 0 or results['records'] is None:
            break
        for record in results['records']:
            record_value = json.loads(record['value'])
            record_value['_id'] = record['id']
            list_of_records.append(record_value)

    await non_secrets.close_wallet_search(search_handle)

    return list_of_records
