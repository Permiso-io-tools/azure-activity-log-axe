import azure_logger
import hashlib

simplify_key_logger = azure_logger.get_logger("simplify_key")

def get_simplify_key(cor_id: str | None, operation_id: str | None, resource_id: str | None) -> str | None:
    if cor_id and operation_id and resource_id:
        try:
            cor_id = cor_id.lower()
            operation_id = operation_id.lower()
            resource_id = resource_id.lower()

            return hashlib.md5((f'{cor_id}:{operation_id}:{resource_id}').encode()).hexdigest()
        except Exception as e:
            simplify_key_logger.error(f"General exception: {e}")

    # Missing data
    simplify_key_logger.critical(f"Missing data, key cannot be created.")