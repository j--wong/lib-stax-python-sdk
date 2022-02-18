import os

from staxapp.config import Config
from staxapp.openapi import StaxClient

Config.access_key = os.getenv("STAX_ACCESS_KEY")
Config.secret_key = os.getenv("STAX_SECRET_KEY")

# Create PermissionSet client
permission_sets_client = StaxClient("permission-sets")

# Create PermissionSet
permission_set_payload = {
    "Name": "MyPermissionSet",
    "Description": "permission set created via SDK",
    "MaxSessionDuration": 3600,
    "InlinePolicies": [
        {
            "Name": "S3Access",
            "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":{\"Effect\":\"Allow\",\"Action\":\"s3:*\",\"Resource\":\"*\"}}"
        }
    ],
    "Tags": {
        "Department": "IT"
    }
}
permission_set = permission_sets_client.CreatePermissionSet(**permission_set_payload)
print("permission set created:", permission_set)
print("-----------------------------------------")

# Get PermissionSet by ID
permission_set = permission_sets_client.GetPermissionSet(permission_set_id=permission_set.get("Id"))
print("retrieved permission set:", permission_set)
print("-----------------------------------------")

# Update PermissionSet
permission_set_update = {
    "Description": f"{permission_set.get('Description')} - updated",
    "MaxSessionDuration": 7200
}
updated_permission_set = permission_sets_client.UpdatePermissionSet(permission_set_id=permission_set.get("Id"), **permission_set_update)
print("permission set updated:", updated_permission_set)
print("-----------------------------------------")

# Delete PermissionSet
deleted_permission_set = permission_sets_client.DeletePermissionSet(permission_set_id=permission_set.get("Id"))
print("permission set deleted:", deleted_permission_set)
print("-----------------------------------------")

# Retrieve all ACTIVE PermissionSets
active_permission_sets = permission_sets_client.ListPermissionSets(status="ACTIVE")
print(active_permission_sets)
print("-----------------------------------------")
