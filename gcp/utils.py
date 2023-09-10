from typing import Dict, List
from google.cloud import secretmanager

import os
import json



# dont ask me why i'm doing this, bcs i'm noob ¯\_(ツ)_/¯ 
class GSMController:

    project_id = os.getenv('PROJECT_ID')
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"

    def __init__(self, service):
        self.service     = service
        self.secret_path = f"{self.parent}/secrets/{service}"
        self.full        = f"{self.secret_path}/versions/latest"

    @classmethod
    def list_current_secrets(cls):
        """List all secrets and labels in the given project."""


        secret_lists = cls.client.list_secrets(request={"parent": cls.parent})
        return secret_lists


    @classmethod
    def list_current_secrets_name(cls) -> List[str]:
        data = [ secret.name.split("/")[-1] for secret in cls.client.list_secrets(request={"parent": cls.parent}) ]
        return data


    @classmethod
    def list_current_secrets_name_and_labels(cls) -> Dict[str, str]:
        """List all secrets and labels in the given project."""
        
        data_and_labels = dict()
        for secret in cls.client.list_secrets(request={"parent": cls.parent}):
            name = secret.name.split("/")[-1]
            try:
                data_and_labels[name] = list(secret.labels.popitem())
            except KeyError:
                data_and_labels[name] = "No Labels"

        return data_and_labels


    def access_secret_payload(self):
        """Access secret payload (latest secret data)"""
        # disini class
        response = self.client.access_secret_version(request={"name": self.full}) 

        # need to add checksum for next version

        # ini hasilnya byte, bisa pakai .decode('UTF-8')
        # data_json = json.loads(payload)
        payload = response.payload.data
        return payload


    def update_current_secret(self, payload) -> Dict[str, str]:
        
        """Add a new secret version to the given secret with the provided payload."""
        
        data = json.dumps(payload) # convert to json string from python dict 

        # Convert the string payload into a bytes. This step can be omitted if you
        # pass in bytes instead of a str for the payload argument.
        data = data.encode("UTF-8") # b'{json_payload} -> <class 'bytes'>

        # Calculate payload checksum. Passing a checksum in add-version request
        # is optional.
        # crc32c = google_crc32c.Checksum()
        # crc32c.update(payload)

        # Add the secret version.
        response = self.client.add_secret_version(
            request={
                "parent": self.secret_path,
                "payload": {"data": data},
            }
        )
        # Print the new secret version name.
        response = {
            "success": f"Data for {response.name.split('/')[-3]} has been added!",
            "version": f"{response.name.split('/')[-1]} | latest"
        }
        return response


    def create_new_secret(self, labels):

        # Create the parent secret.
        secret = self.client.create_secret(
            request={
                "parent": self.parent,
                "secret_id": self.service,
                "secret": {"labels": labels, "replication": {"automatic": {}}},
            }
        )
        return secret # -> <class 'google.cloud.secretmanager_v1.types.resources.Secret'> {name, replication, create_time, labels}


    def get_single_secret(self):
        """
        Get information about the given secret. This only returns metadata about
        the secret container, not any secret material.
        """
        # secret_path = self.client.secret_path(self.project_id, self.service)
        response = self.client.get_secret(request={"name": self.secret_path})
        return response

    
    def delete_secret(self):
        """
        Delete the secret with the given name and all of its versions.
        """
        # Delete the secret.
        result = self.client.delete_secret(request={"name": self.secret_path})
        return result


    def update_secret_metadata(self, labels):
        """
        Update the metadata about an existing secret.
        """

        # Update the secret.
        secret = {"name": self.secret_path, "labels": labels}
        update_mask = {
            "paths": ["labels"]
            }
        response = self.client.update_secret(
            request={"secret": secret, "update_mask": update_mask}
        )

        # Print the new secret name.
        return {"success": f"Updated secret: {response.name}"}