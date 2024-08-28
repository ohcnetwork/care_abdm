from abdm.utils.fidelius import (
    CryptoController,
    DecryptionRequest,
    EncryptionRequest,
    KeyMaterial,
)


class Cipher:
    def __init__(
        self,
        external_public_key,
        external_nonce,
        internal_private_key=None,
        internal_public_key=None,
        internal_nonce=None,
    ):
        self.external_public_key = external_public_key
        self.external_nonce = external_nonce

        self.internal_private_key = internal_private_key
        self.internal_public_key = internal_public_key
        self.internal_nonce = internal_nonce

        self.key_to_share = None

    def generate_key_pair(self):
        key_material = KeyMaterial.generate()

        self.internal_private_key = key_material.private_key
        self.internal_public_key = key_material.public_key
        self.internal_nonce = key_material.nonce
        self.key_to_share = key_material.x509_public_key

        return {
            "privateKey": self.internal_private_key,
            "publicKey": self.internal_public_key,
            "nonce": self.internal_nonce,
        }

    def encrypt(self, payload):
        if not self.internal_private_key:
            key_material = self.generate_key_pair()

            if not key_material:
                return None

        encryption_request = EncryptionRequest(
            requester_public_key=self.external_public_key,
            requester_nonce=self.external_nonce,
            sender_private_key=self.internal_private_key,
            sender_nonce=self.internal_nonce,
            string_to_encrypt=payload,
        )
        controller = CryptoController()
        encrypted_string = controller.encrypt(encryption_request)

        return {
            "publicKey": self.key_to_share,
            "data": encrypted_string,
            "nonce": self.internal_nonce,
        }

    def decrypt(self, payload):
        decryption_request = DecryptionRequest(
            sender_public_key=self.external_public_key,
            sender_nonce=self.external_nonce,
            requester_private_key=self.internal_private_key,
            requester_nonce=self.internal_nonce,
            encrypted_data=payload,
        )
        controller = CryptoController()
        decrypted_string = controller.decrypt(decryption_request)

        return decrypted_string
