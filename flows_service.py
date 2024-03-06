##
# @file:  flows_service.py
# @brief: Utility functions for interacting with the Globus Flows service.
# See: https://github.com/globus/globus-flows-trigger-examples
#

import os
import sys

import globus_sdk
from globus_sdk.scopes import GCSCollectionScopeBuilder, MutableScope
from globus_sdk.tokenstorage import SimpleJSONFileAdapter

# Tokens and refresh tokens will be stored in this file; secure it!!
TOKEN_FILE_ADAPTER = SimpleJSONFileAdapter(
    os.path.expanduser("~/.globus-flows-tokens.json")
)

SERVICE_SCOPES = [
    globus_sdk.FlowsClient.scopes.manage_flows,
    globus_sdk.FlowsClient.scopes.run,
    globus_sdk.FlowsClient.scopes.run_status,
    globus_sdk.FlowsClient.scopes.run_manage,
    globus_sdk.FlowsClient.scopes.view_flows
]
RESOURCE_SERVER = globus_sdk.FlowsClient.resource_server

# Replace this with your own client ID; register a native application
# client at https://app.globus.org/settings/developers
# Default is 'FRIB Auth' in the 'FRIB Globus Flows' project
CLIENT_ID = "59f19e1e-f1ce-4cb1-973c-8d893e89c0a9"

CLIENT = globus_sdk.NativeAppAuthClient(CLIENT_ID)
TRANSFER_ACTION_PROVIDER_SCOPE_STRING = (
    "https://auth.globus.org/scopes/actions.globus.org/transfer/transfer"
)


def get_tokens(scopes=None):
    """Get new tokens for the flow and return them.

    Parameters
    ----------
    scopes : str | MutableScope | Iterable[str | MutableScope]
        The desired OAuth2 scopes.

    Returns
    ------
    globus_sdk.OAuthTokenResponse
        Responses for OAuth2 code for token exchange.

    """
    # Initiate login flow
    CLIENT.oauth2_start_flow(
        requested_scopes=scopes, refresh_tokens=True
    )
    authorize_url = CLIENT.oauth2_get_authorize_url()
    print(
        f"Log in at this URL and get authorization code:\n\n{authorize_url}\n"
    )
    auth_code = input("Enter authorization code here: ").strip()
    tokens = CLIENT.oauth2_exchange_code_for_tokens(auth_code)
      
    return tokens
    

def get_authorizer(flow_id=None, collection_ids=None):
    """Pre-authorize access to our mapped collections, set scope(s), get or 
    load tokens and return a RefreshTokenAuthorizer.

    Parameters
    ----------
    flow_id : str
        Flow UUID.
    collection_ids : str | Iterable[str]
        List of collection UUIDs to pre-authorize.

    Returns
    -------
    globus_sdk.RefreshTokenAuthorizer
        The authorizer using a Refresh Token to fetch Access Tokens.

    """
    if flow_id:
        scopes = globus_sdk.SpecificFlowClient(flow_id).scopes
        resource_server = flow_id
        scopes = scopes.make_mutable("user")
    else:
        scopes = SERVICE_SCOPES
        resource_server = RESOURCE_SERVER
            
    # Pre-authorize for our collections:
    if collection_ids:
        # Build a scope that will give the flow
        # access to specific mapped collections on your behalf
        transfer_scope = globus_sdk.TransferClient.scopes.make_mutable("all")
        transfer_action_provider_scope = MutableScope(
            TRANSFER_ACTION_PROVIDER_SCOPE_STRING
        )

        # If you declared and mapped collections above, add them to
        # the transfer scope
        for collection_id in collection_ids:
            gcs_data_access_scope = GCSCollectionScopeBuilder(collection_id).make_mutable("data_access", optional=True)
            transfer_scope.add_dependency(gcs_data_access_scope)

        transfer_action_provider_scope.add_dependency(transfer_scope)
        scopes.add_dependency(transfer_action_provider_scope)
        
    # Try to load saved tokens
    if TOKEN_FILE_ADAPTER.file_exists():
        tokens = TOKEN_FILE_ADAPTER.get_token_data(resource_server)
    else:
        tokens = None
        
    if tokens is None:
        # Log into Globus Auth and get tokens
        response = get_tokens(scopes=scopes)
        # Store tokens and extract token for Globus Flows service
        TOKEN_FILE_ADAPTER.store(response)
        tokens = response.by_resource_server[resource_server]
        
    return globus_sdk.RefreshTokenAuthorizer(
        tokens["refresh_token"],
        CLIENT,
        access_token=tokens["access_token"],
        expires_at=tokens["expires_at_seconds"],
        on_refresh=TOKEN_FILE_ADAPTER.on_refresh,
    )


def create_flows_client(flow_id=None, collection_ids=None):
    """Create the flow client. If a flow ID is provided, returns a 
    SpecificFlowClient associated with that UUID.

    Parameters
    ----------
    flow_id : str
        Flow UUID.
    collection_ids : str | Iterable[str]
        Collection UUID(s).

    Returns
    -------
    FlowsClient
        The Flows client.

    """
    authorizer = get_authorizer(flow_id, collection_ids=collection_ids)    
    if flow_id:
        return globus_sdk.SpecificFlowClient(flow_id, authorizer=authorizer)
    else:
        return globus_sdk.FlowsClient(authorizer=authorizer)
